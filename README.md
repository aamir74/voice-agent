# Real-Time Voice AI Agent (LiveKit + RAG)

Talk to an AI assistant over WebRTC. The agent transcribes your speech, retrieves relevant
context from PDFs you've uploaded, generates a grounded answer with an LLM, and speaks it back
— all in real time. Answers come from your documents, not the model's own knowledge.

## Architecture

```
React Frontend ──REST──┐                ┌── Groq Whisper (STT)
(Vite + TS + Tailwind)  │                │── Gemini 2.5 Flash (LLM)
        │  WebRTC        ▼                │── Kokoro (TTS, local)
        └──────────► LiveKit Room ◄── Agent Worker (livekit-agents)
                         ▲                │
FastAPI Backend ─────────┘                └── RAG: Gemini embeddings → ChromaDB
(token, upload, prompt, sources, health)
```

Real-time audio flows through **LiveKit Cloud** (WebRTC); the REST API and the agent run
locally. Two backend processes share the on-disk ChromaDB store and a small state file, so a
document uploaded via the API is immediately retrievable by the agent during a call:

1. **FastAPI app** — REST API (LiveKit tokens, PDF upload/ingestion, editable prompt, RAG
   sources, health).
2. **Agent worker** — registers with LiveKit Cloud, auto-joins each room, and runs the
   STT → RAG → LLM → TTS loop.

| Concern    | Choice                                   |
| ---------- | ---------------------------------------- |
| STT        | Groq `whisper-large-v3` (OpenAI-compat)  |
| LLM        | Google `gemini-2.5-flash` (OpenAI-compat)|
| TTS        | Kokoro (local ONNX)                      |
| Embeddings | Gemini `gemini-embedding-001`            |
| Vector DB  | ChromaDB (persistent, on disk)           |
| Frontend   | React + TypeScript + Vite + Tailwind     |

## Prerequisites

- **Python 3.10+** and [`uv`](https://docs.astral.sh/uv/)
- **Node 20+** and [`bun`](https://bun.sh/)
- A **LiveKit Cloud** project (free) — sign up at [cloud.livekit.io](https://cloud.livekit.io).
  From your project's **Settings → Keys**, grab the **WebSocket URL** (`wss://<project>.livekit.cloud`),
  **API Key**, and **API Secret**. *(A local `livekit-server --dev` also works — see the note at
  the end of "Running" — but this guide uses Cloud.)*
- API keys: **Groq** ([console.groq.com/keys](https://console.groq.com/keys)) and
  **Google Gemini** ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))

## Environment Variables

Copy the examples and fill in your keys:

```powershell
# PowerShell (Windows)
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

```bash
# macOS / Linux
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then edit **`backend/.env`** and set the values from your **LiveKit Cloud** project and your
API keys:

```env
# From LiveKit Cloud → Settings → Keys
LIVEKIT_URL=wss://<your-project>.livekit.cloud
LIVEKIT_API_KEY=<your-livekit-api-key>
LIVEKIT_API_SECRET=<your-livekit-api-secret>

# Provider keys
GROQ_API_KEY=<your-groq-key>
GEMINI_API_KEY=<your-gemini-key>
```

Everything else (Kokoro model paths, RAG settings, CORS) is pre-filled and works as-is.
`frontend/.env` only needs `VITE_API_URL` (defaults to `http://localhost:8000`).

| Variable                              | Description                                         |
| ------------------------------------- | --------------------------------------------------- |
| `LIVEKIT_URL`                         | LiveKit Cloud WebSocket URL (`wss://…livekit.cloud`) |
| `LIVEKIT_API_KEY` / `_SECRET`         | LiveKit Cloud API credentials                       |
| `GROQ_API_KEY`                        | Groq key for Whisper STT                            |
| `GEMINI_API_KEY`                      | Gemini key for the LLM and embeddings               |
| `KOKORO_MODEL_PATH` / `_VOICES_PATH`  | Paths to the local Kokoro model files               |
| `VITE_API_URL` (frontend)             | Backend base URL (default `http://localhost:8000`)  |

> ⚠️ **Never commit `.env`.** It's gitignored. If you've shared keys anywhere, rotate them in
> the Groq / Google AI Studio / LiveKit dashboards.

## Setup

### 1. Backend

```bash
cd backend
uv sync
```

> **Windows / `uv` not found?** The official installer puts `uv` at
> `C:\Users\<you>\.local\bin`, which may not be on your PATH yet. Add it permanently (run once,
> then reopen your terminals):
> ```powershell
> [Environment]::SetEnvironmentVariable("Path", "$HOME\.local\bin;" + [Environment]::GetEnvironmentVariable("Path","User"), "User")
> ```

Download the two Kokoro TTS model files into `backend/models/`:

```powershell
# PowerShell — from the backend/ directory
New-Item -ItemType Directory -Force models | Out-Null
$base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
Invoke-WebRequest "$base/kokoro-v1.0.onnx" -OutFile "models/kokoro-v1.0.onnx"   # ~310 MB
Invoke-WebRequest "$base/voices-v1.0.bin"  -OutFile "models/voices-v1.0.bin"    # ~27 MB
```

### 2. Frontend

```bash
cd frontend
bun install
```

## Running (3 terminals)

Because we use **LiveKit Cloud**, there's **no local LiveKit server to run** — you only need
three processes. Open **three terminals**, all from the project root (`voice-agent/`). Commands
are shown for **PowerShell (Windows)**; on macOS/Linux just use `cd backend` / `cd frontend`.

### Terminal 1 — FastAPI backend (REST API)

```powershell
cd backend
uv run uvicorn app.main:app --port 8000
```

Wait for `Application startup complete`, then verify: open <http://localhost:8000/health> →
`{"status":"ok", ...}`.

### Terminal 2 — Voice agent worker

```powershell
cd backend
uv run python -m app.agent.voice_agent dev
```

Wait for `registered worker` — this means the agent connected to your LiveKit Cloud project and
is ready to join calls. (The first time it speaks, it loads the Kokoro model — a ~10 s one-time
delay.)

### Terminal 3 — Frontend

```powershell
cd frontend
bun run dev
```

Open the printed URL (default <http://localhost:5173>).

> **Stopping:** press `Ctrl+C` in each terminal.
>
> **Prefer a fully local LiveKit instead of Cloud?** Run a 4th terminal with
> `livekit-server --dev` and set these in `backend/.env`:
> `LIVEKIT_URL=ws://localhost:7880`, `LIVEKIT_API_KEY=devkey`, `LIVEKIT_API_SECRET=secret`.
> Everything else is identical.

## Using It

1. **Edit the system prompt** and click *Save Prompt*.
2. **Upload a PDF** — wait for the "N chunks indexed" confirmation.
3. **Connect** to start the voice call and allow microphone access.
4. **Ask a question** answerable from your document. You'll see the live transcript, the
   retrieved chunks in the *RAG Sources* panel, and hear the spoken answer.

## Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok","chroma_ok":true,"livekit_configured":true}
```

## Project Structure

```
backend/app/
  core/       config, structured logging, shared state (prompt + Chroma)
  services/   stt, llm, tts, embeddings, ingestion, rag
  api/        token, upload, prompt, sources, health
  agent/      voice_agent (livekit-agents worker)
frontend/src/
  hooks/      useVoiceRoom (LiveKit room lifecycle)
  components/ VoiceCall, SystemPromptEditor, DocumentUpload, LiveTranscript, RagSourcesPanel
  lib/        api (typed REST client)
```

## Limitations & Tradeoffs

- **Single shared knowledge base.** All uploads go into one Chroma collection; there's no
  per-user or per-room isolation.
- **Kokoro runs on CPU**, so the first synthesis after startup has some model-load latency
  (~10 s). On low-core machines, running STT + VAD + TTS locally can add a 1–3 s response
  delay; a quantized model or a hosted TTS would reduce this.
- **Chunking is a simple overlapping splitter** (character-based). A semantic splitter would
  improve retrieval quality.
- **STT/LLM use Groq's and Gemini's OpenAI-compatible endpoints** via the LiveKit OpenAI
  plugin; swapping providers is a config change.
- **State is shared via disk** between the two backend processes (KISS); a production system
  would use a shared service or message bus.
- **Agent dispatch is automatic** — the worker (no `agent_name` set) joins every new LiveKit
  room. For multi-tenant use you'd set an `agent_name` and dispatch explicitly per room.
