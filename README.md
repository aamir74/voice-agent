# Real-Time Voice AI Agent (LiveKit + RAG)

Talk to an AI assistant over WebRTC. It transcribes your speech, retrieves context from PDFs
you upload, generates a grounded answer, and speaks it back — in real time. Answers come from
your documents, not the model's own knowledge.

## Architecture

```
React Frontend ──REST──┐                ┌── Groq Whisper (STT)
(Vite + TS + Tailwind)  │                │── Gemini 2.5 Flash (LLM)
        │  WebRTC        ▼                │── Kokoro (TTS, local)
        └──────────► LiveKit Cloud ◄─ Agent Worker (livekit-agents)
                         ▲                │
FastAPI Backend ─────────┘                └── RAG: Gemini embeddings → ChromaDB
(token, upload, prompt, sources, health)
```

Real-time audio flows through **LiveKit Cloud**; the REST API and agent run locally as two
processes sharing the on-disk ChromaDB store, so an uploaded document is instantly retrievable
mid-call.

- **FastAPI app** — REST: LiveKit tokens, PDF upload/ingestion, editable system prompt, RAG sources, health.
- **Agent worker** — registers with LiveKit Cloud, auto-joins each room, runs the STT → RAG → LLM → TTS loop.

| STT | LLM | TTS | Embeddings | Vector DB | Frontend |
|-----|-----|-----|------------|-----------|----------|
| Groq `whisper-large-v3` | Gemini `2.5-flash` | Kokoro (local ONNX) | Gemini `embedding-001` | ChromaDB | React + TS + Vite |

## Prerequisites

- **Python 3.10+** with [`uv`](https://docs.astral.sh/uv/), **Node 20+** with [`bun`](https://bun.sh/)
- A **[LiveKit Cloud](https://cloud.livekit.io)** project → Settings → Keys (URL, API key, secret)
- API keys: **[Groq](https://console.groq.com/keys)** and **[Google Gemini](https://aistudio.google.com/apikey)**

## Setup

```bash
# Backend deps
cd backend && uv sync

# Kokoro TTS model files into backend/models/
#   kokoro-v1.0.onnx (~310MB) and voices-v1.0.bin (~27MB)
#   from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0

# Frontend deps
cd ../frontend && bun install
```

> **Windows:** if `uv` isn't found, add it to PATH once, then reopen terminals:
> ```powershell
> [Environment]::SetEnvironmentVariable("Path", "$HOME\.local\bin;" + [Environment]::GetEnvironmentVariable("Path","User"), "User")
> ```

## Environment Variables

```bash
cp backend/.env.example backend/.env      # then fill in the keys below
cp frontend/.env.example frontend/.env    # VITE_API_URL, defaults to http://localhost:8000
```

| Variable (`backend/.env`) | Description |
|---------------------------|-------------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL (`wss://<project>.livekit.cloud`) |
| `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | LiveKit Cloud credentials |
| `GROQ_API_KEY` | Groq key (Whisper STT) |
| `GEMINI_API_KEY` | Gemini key (LLM + embeddings) |

Kokoro paths, RAG settings, and CORS are pre-filled. **Never commit `.env`** (it's gitignored).

## Run (3 terminals)

No local LiveKit server needed — LiveKit Cloud handles the media.

```bash
# 1 — Backend API
cd backend && uv run uvicorn app.main:app --port 8000      # wait: "Application startup complete"

# 2 — Agent worker
cd backend && uv run python -m app.agent.voice_agent dev   # wait: "registered worker"

# 3 — Frontend
cd frontend && bun run dev                                 # open http://localhost:5173
```

Then in the browser: **edit prompt → Save → upload a PDF → Connect (allow mic) → ask a question
from the PDF.** Health check: `curl http://localhost:8000/health`.

## Limitations & Tradeoffs

- **Latency (~1–3 s before the spoken reply).** STT, VAD, and Kokoro TTS all run locally on
  CPU and compete for cores. **Fixes:** use a quantized Kokoro model (`q8`, ~2× faster), move
  TTS to a hosted provider (ElevenLabs/Cartesia), or run on a GPU. The ONNX session is already
  multi-threaded and capped to leave a core free for STT/VAD.
- **Single shared knowledge base** — one Chroma collection, no per-user/room isolation.
- **Simple character-based chunking** with overlap; a semantic splitter would improve retrieval.
- **State shared via disk** between the two backend processes (KISS); production would use a
  shared service or message bus.
- **Automatic agent dispatch** — the worker joins every new room; multi-tenant use needs an
  `agent_name` and explicit dispatch.
