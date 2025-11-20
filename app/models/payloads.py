from typing import List, Optional

from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded PCM/WAV 16k mono")
    session_id: Optional[str] = Field(None, description="Client session identifier")
    trace_id: Optional[str] = Field(None, description="Optional trace correlation id")
    lang: str = Field("auto", description="Language hint: auto|de|en|es|pt")


class TranscribeResponse(BaseModel):
    text: str
    lang: str
    timestamps: Optional[List[float]] = None
    trace_id: Optional[str] = None


class ChatRequest(BaseModel):
    text: str
    lang: str = Field("auto", description="Language hint or override")
    session_id: Optional[str] = None
    trace_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    lang: str
    context: List[dict]
    trace_id: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    # pydantic v2 removed `regex` kwarg; use `pattern` instead
    lang: str = Field(..., pattern="^(de|en|es|pt)$")
    voice: str = Field("default", description="Voice profile name")
    trace_id: Optional[str] = None


class TTSResponse(BaseModel):
    audio_base64: str
    duration_ms: int
    trace_id: Optional[str] = None


class HealthStatus(BaseModel):
    asr: str
    llm: str
    tts: str
