"""Application configuration loaded from environment variables.

A single Settings instance is the source of truth for API keys, service URLs, and
model names. Both the FastAPI app and the LiveKit agent worker import `settings`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (two levels up from this file: app/core/config.py -> backend/)
BACKEND_DIR = Path(__file__).resolve().parents[2]

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's questions politely and concisely "
    "using only the provided document context. If the answer is not in the context, "
    "say that you don't have that information in the uploaded documents."
)


class Settings(BaseSettings):
    """Runtime configuration. Values come from the environment / a .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LiveKit ---
    livekit_url: str = Field(default="ws://localhost:7880", alias="LIVEKIT_URL")
    livekit_api_key: str = Field(default="devkey", alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(default="secret", alias="LIVEKIT_API_SECRET")

    # --- Groq (STT, OpenAI-compatible) ---
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL"
    )
    stt_model: str = Field(default="whisper-large-v3", alias="STT_MODEL")

    # --- Gemini (LLM via OpenAI-compat, embeddings via native SDK) ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        alias="GEMINI_BASE_URL",
    )
    llm_model: str = Field(default="gemini-2.5-flash", alias="LLM_MODEL")
    embedding_model: str = Field(
        default="gemini-embedding-001", alias="EMBEDDING_MODEL"
    )

    # --- TTS (Kokoro local) ---
    kokoro_model_path: str = Field(
        default=str(BACKEND_DIR / "models" / "kokoro-v1.0.onnx"),
        alias="KOKORO_MODEL_PATH",
    )
    kokoro_voices_path: str = Field(
        default=str(BACKEND_DIR / "models" / "voices-v1.0.bin"),
        alias="KOKORO_VOICES_PATH",
    )
    kokoro_voice: str = Field(default="af_heart", alias="KOKORO_VOICE")
    # Slightly faster than 1.0 trims audio length per sentence, reducing CPU pauses.
    kokoro_speed: float = Field(default=1.1, alias="KOKORO_SPEED")

    # --- Storage ---
    data_dir: str = Field(default=str(BACKEND_DIR / "data"), alias="DATA_DIR")
    chroma_dir: str = Field(
        default=str(BACKEND_DIR / "data" / "chroma"), alias="CHROMA_DIR"
    )
    collection_name: str = Field(default="knowledge_base", alias="COLLECTION_NAME")

    # --- RAG ---
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")

    # --- Server ---
    cors_origins: str = Field(
        default="http://localhost:5173", alias="CORS_ORIGINS"
    )
    default_system_prompt: str = Field(
        default=DEFAULT_SYSTEM_PROMPT, alias="DEFAULT_SYSTEM_PROMPT"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def uploads_dir(self) -> Path:
        return Path(self.data_dir) / "uploads"

    def ensure_dirs(self) -> None:
        """Create the data/upload/chroma directories if they don't exist."""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_dir).mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
