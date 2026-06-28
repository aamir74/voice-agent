"""Mint LiveKit access tokens so the frontend can join a room."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from livekit import api
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["token"])


class TokenRequest(BaseModel):
    room: str = Field(default="voice-agent")
    identity: str | None = None


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str
    identity: str


@router.post("/token", response_model=TokenResponse)
def create_token(body: TokenRequest) -> TokenResponse:
    identity = body.identity or f"user-{uuid.uuid4().hex[:8]}"
    grant = api.VideoGrants(
        room_join=True,
        room=body.room,
        can_publish=True,
        can_subscribe=True,
    )
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(grant)
        .to_jwt()
    )
    return TokenResponse(
        token=token,
        url=settings.livekit_url,
        room=body.room,
        identity=identity,
    )
