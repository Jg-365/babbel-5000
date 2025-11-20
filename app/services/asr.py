import base64
import time
from typing import Optional

from app.utils.languages import detect_language


class ASRService:
    def __init__(self, metrics, logger):
        self.metrics = metrics
        self.logger = logger

    async def transcribe(self, audio_base64: str, trace_id: str, session_id: Optional[str]):
        start = time.time()
        audio_bytes = base64.b64decode(audio_base64)
        lang = detect_language(audio_bytes)
        text = self._fake_transcription(audio_bytes, lang)
        latency_ms = int((time.time() - start) * 1000)
        self.metrics.record_latency("asr", latency_ms)
        self.logger.info({
            "event": "asr_complete",
            "trace_id": trace_id,
            "session_id": session_id,
            "lang": lang,
            "latency_ms": latency_ms,
        })
        return {
            "text": text,
            "lang": lang,
            "timestamps": [],
            "trace_id": trace_id,
        }

    async def transcribe_stream(self, audio_bytes: bytes, lang_hint: str, trace_id: str):
        lang = lang_hint if lang_hint != "auto" else detect_language(audio_bytes)
        text = self._fake_transcription(audio_bytes, lang)
        self.logger.debug({
            "event": "asr_stream_chunk",
            "trace_id": trace_id,
            "lang": lang,
            "chunk": len(audio_bytes),
        })
        return {"text": text, "lang": lang, "trace_id": trace_id}

    def _fake_transcription(self, audio_bytes: bytes, lang: str) -> str:
        sample_len = min(8, len(audio_bytes))
        sample_hex = audio_bytes[:sample_len].hex()
        return f"transcript-{lang}-{sample_hex}"
