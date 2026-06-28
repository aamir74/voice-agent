"""Text-to-speech via Kokoro (local ONNX model).

Kokoro runs fully locally, so there is no per-character API cost or network latency.
This module exposes a small `synthesize()` helper returning float32 PCM samples plus
the sample rate; the LiveKit TTS adapter (app/agent/kokoro_tts.py) wraps it to stream
audio frames into the room.

Model files must be present (see README): download `kokoro-v1.0.onnx` and
`voices-v1.0.bin` into backend/models/.
"""

from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_kokoro = None  # lazy Kokoro instance


def _build_session():
    """Build a CPU-tuned ONNX session so synthesis runs faster than real time.

    Kokoro's default session underutilizes multi-core CPUs; using all cores and
    full graph optimization roughly halves synthesis latency, which is what removes
    the pauses between sentences during a call.
    """
    import os

    import onnxruntime as ort

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    # Leave at least one core free for STT/VAD/turn-detection; grabbing every core
    # starves the rest of the realtime pipeline (huge turn-detection/STT latency).
    cpu = os.cpu_count() or 4
    opts.intra_op_num_threads = max(1, cpu - 1)
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    return ort.InferenceSession(
        settings.kokoro_model_path,
        sess_options=opts,
        providers=["CPUExecutionProvider"],
    )


def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro  # imported lazily so import errors surface late

        logger.info(
            "kokoro_init",
            extra={
                "model": settings.kokoro_model_path,
                "voices": settings.kokoro_voices_path,
            },
        )
        _kokoro = Kokoro.from_session(
            _build_session(), settings.kokoro_voices_path
        )
    return _kokoro


def synthesize(text: str, voice: str | None = None) -> tuple[np.ndarray, int]:
    """Synthesize `text` to mono float32 PCM. Returns (samples, sample_rate)."""
    kokoro = _get_kokoro()
    samples, sample_rate = kokoro.create(
        text,
        voice=voice or settings.kokoro_voice,
        speed=settings.kokoro_speed,
        lang="en-us",
    )
    return np.asarray(samples, dtype=np.float32), int(sample_rate)


def synthesize_stream(text: str, voice: str | None = None):
    """Async generator yielding (samples, sample_rate) chunks as they're produced.

    Streaming lets playback start before the whole utterance is synthesized, which
    removes the long pauses between sentences when running Kokoro on CPU.
    """
    kokoro = _get_kokoro()
    return kokoro.create_stream(
        text,
        voice=voice or settings.kokoro_voice,
        speed=settings.kokoro_speed,
        lang="en-us",
    )
