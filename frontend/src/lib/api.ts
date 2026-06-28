// Typed REST client for the FastAPI backend.

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface TokenResponse {
  token: string;
  url: string;
  room: string;
  identity: string;
}

export interface UploadResponse {
  filename: string;
  chunk_count: number;
}

export interface RagSource {
  text: string;
  source: string;
  score: number;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchToken(room = 'voice-agent'): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/api/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room }),
  });
  return handle<TokenResponse>(res);
}

export async function getPrompt(): Promise<string> {
  const res = await fetch(`${API_URL}/api/prompt`);
  const data = await handle<{ prompt: string }>(res);
  return data.prompt;
}

export async function updatePrompt(prompt: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/prompt`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  const data = await handle<{ prompt: string }>(res);
  return data.prompt;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/api/documents`, {
    method: 'POST',
    body: form,
  });
  return handle<UploadResponse>(res);
}

export async function getSources(): Promise<RagSource[]> {
  const res = await fetch(`${API_URL}/api/sources`);
  const data = await handle<{ sources: RagSource[] }>(res);
  return data.sources;
}
