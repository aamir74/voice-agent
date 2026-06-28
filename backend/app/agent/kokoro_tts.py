"""LiveKit TTS adapter wrapping the local Kokoro synthesizer.

Implements the `livekit.agents.tts.TTS` interface (v1.x) so Kokoro can be plugged
into an AgentSession like any hosted TTS provider. Audio is streamed: Kokoro yields
PCM chunks progressively and we push each one to the AudioEmitter as it arrives, so
playback starts before the whole utterance is synthesized (Kokoro is CPU-bound, so
waiting for the full clip per sentence caused long inter-sentence pauses).
"""

from __future__ import annotations

import numpy as np
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    tts,
)
from livekit.agents.utils import shortuuid

from app.core.logging import get_logger
from app.services.tts import synthesize_stream

logger = get_logger(__name__)

NUM_CHANNELS = 1
SAMPLE_RATE = 24000


class KokoroTTS(tts.TTS):
    """Local Kokoro text-to-speech for LiveKit agents."""

    def __init__(self, *, sample_rate: int = SAMPLE_RATE, voice: str | None = None) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=NUM_CHANNELS,
        )
        self._voice = voice

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "KokoroChunkedStream":
        return KokoroChunkedStream(
            tts=self, input_text=text, conn_options=conn_options, voice=self._voice
        )


class KokoroChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: KokoroTTS,
        input_text: str,
        conn_options: APIConnectOptions,
        voice: str | None,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._voice = voice

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        # Collect all chunks Kokoro yields for this (sentence-sized) input, then push
        # once. Kokoro yields a single chunk per sentence anyway, so non-streaming
        # output keeps the emitter protocol simple and correct. The latency win comes
        # from the tuned multi-thread ONNX session, not from chunk-level streaming.
        parts: list[bytes] = []
        async for samples, _sr in synthesize_stream(self._input_text, self._voice):
            if samples is not None and len(samples):
                parts.append(_float_to_pcm16(samples).tobytes())

        output_emitter.initialize(
            request_id=shortuuid(),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
            mime_type="audio/pcm",
        )
        if parts:
            output_emitter.push(b"".join(parts))
        output_emitter.flush()


def _float_to_pcm16(samples: np.ndarray) -> np.ndarray:
    """Convert float32 PCM in [-1, 1] to little-endian int16 PCM."""
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2")
