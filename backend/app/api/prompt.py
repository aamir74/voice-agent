"""Editable system prompt: GET the current value, PUT to update it."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.state import get_system_prompt, set_system_prompt

router = APIRouter(prefix="/api", tags=["prompt"])


class PromptResponse(BaseModel):
    prompt: str


class PromptUpdate(BaseModel):
    prompt: str = Field(..., min_length=1)


@router.get("/prompt", response_model=PromptResponse)
def read_prompt() -> PromptResponse:
    return PromptResponse(prompt=get_system_prompt())


@router.put("/prompt", response_model=PromptResponse)
def update_prompt(body: PromptUpdate) -> PromptResponse:
    stored = set_system_prompt(body.prompt)
    return PromptResponse(prompt=stored)
