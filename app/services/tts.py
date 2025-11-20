import base64
import math
import time
from typing import AsyncIterator

from app.utils.languages import normalize_lang


class TTSService:
    def __init__(self, metrics, logger):
        self.metrics = metrics
        self.logger = logger

    async def synthesize(self, text: str, lang: str, voice: str, trace_id: str):
        start = time.time()
        normalized_lang = normalize_lang(lang)
        audio_bytes = self._generate_silence(len(text))
        duration_ms = int((time.time() - start) * 1000)
        self.metrics.record_latency("tts", duration_ms)
        self.logger.info({
            "event": "tts_complete",
            "trace_id": trace_id,
            "lang": normalized_lang,
            "voice": voice,
            "duration_ms": duration_ms,
        })
        return {
            "audio_base64": base64.b64encode(audio_bytes).decode(),
            "duration_ms": duration_ms,
            "trace_id": trace_id,
        }

    async def stream(self, text: str, lang: str, voice: str, trace_id: str) -> AsyncIterator[bytes]:
        normalized_lang = normalize_lang(lang)
        chunk_count = max(1, math.ceil(len(text) / 32))
        for i in range(chunk_count):
            payload = f"{normalized_lang}-{voice}-{i}".encode()
            yield payload

    def _generate_silence(self, text_length: int) -> bytes:
        frames = max(1600, text_length * 20)
        return bytes([0] * frames)
