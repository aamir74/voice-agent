"""LiveKit agent worker: the real-time STT -> RAG -> LLM -> TTS voice loop.

Run with:  uv run python -m app.agent.voice_agent dev

The agent joins each room as a participant. On every user turn it:
  1. refreshes the editable system prompt (set from the UI),
  2. retrieves relevant chunks from the uploaded knowledge base, and
  3. appends that context to the chat so the LLM answers from the documents.

STT/LLM/TTS are the modular services from app/services; this file only orchestrates.
"""

from __future__ import annotations

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions, WorkerOptions

from app.core.config import settings
from app.core.logging import get_logger
from app.core.state import get_system_prompt
from app.agent.kokoro_tts import KokoroTTS
from app.services.llm import create_llm
from app.services.rag import build_context_block, retrieve
from app.services.stt import create_stt

logger = get_logger(__name__)

RAG_INSTRUCTION = (
    "Use ONLY the following retrieved context to answer the user's question. "
    "If the answer is not contained in the context, say you don't have that "
    "information in the uploaded documents. Do not rely on prior knowledge.\n\n"
    "Retrieved context:\n{context}"
)


class RagAgent(Agent):
    """Voice agent that grounds every answer in the uploaded knowledge base."""

    def __init__(self) -> None:
        super().__init__(instructions=get_system_prompt())

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        # Keep the system prompt in sync with whatever the user set in the UI.
        await self.update_instructions(get_system_prompt())

        query = new_message.text_content or ""
        if not query.strip():
            return

        chunks = retrieve(query)
        context = build_context_block(chunks)
        if not context:
            logger.info("rag_no_context")
            return

        # Prepend the retrieved context into the user's own message rather than
        # appending a trailing system message. Gemini rejects a request whose final
        # turn is a system message ("contents is not specified"), so folding the
        # context into the user turn keeps the request valid and grounds the answer.
        new_message.content = [
            RAG_INSTRUCTION.format(context=context),
            f"\n\nUser question: {query}",
        ]
        logger.info("rag_injected", extra={"chunks": len(chunks)})


async def entrypoint(ctx: JobContext) -> None:
    logger.info("agent_job_start", extra={"room": ctx.room.name})

    # Connect to the room FIRST, then start the session. Starting the session before
    # the room is connected means the agent never subscribes to the user's audio
    # track, so it receives no speech (no transcript, no logs).
    await ctx.connect()
    logger.info("agent_connected", extra={"room": ctx.room.name})

    # AgentSession uses its bundled Silero VAD by default (no explicit plugin needed).
    # Preemptive generation is disabled because on_user_turn_completed rewrites the
    # user message with RAG context; preemptive would start the LLM on the original
    # (un-augmented) message and warn/ignore our changes.
    session = AgentSession(
        stt=create_stt(),
        llm=create_llm(),
        tts=KokoroTTS(voice=settings.kokoro_voice),
        preemptive_generation=False,
    )

    await session.start(
        agent=RagAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )
    logger.info("agent_session_started")

    # Speak the greeting directly via TTS instead of generate_reply(). Gemini's
    # OpenAI-compatible endpoint rejects a request that has no user message
    # ("contents is not specified"), which an instructions-only greeting would
    # produce. say() bypasses the LLM entirely.
    await session.say(
        "Hi! I'm ready to answer questions about your uploaded documents. "
        "What would you like to know?"
    )


def main() -> None:
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    )


if __name__ == "__main__":
    main()
