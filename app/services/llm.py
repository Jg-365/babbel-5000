import random
import time
from typing import List, Optional

from app.models.payloads import ChatResponse
from app.utils.languages import normalize_lang

SYSTEM_PROMPT = "Você é um assistente de voz multilíngue. Responda no idioma do usuário."


class LLMService:
    def __init__(self, metrics, logger):
        self.metrics = metrics
        self.logger = logger

    async def generate_reply(
        self,
        text: str,
        lang: str,
        session_id: Optional[str],
        context: Optional[List[dict]],
        trace_id: str,
    ) -> ChatResponse:
        start = time.time()
        normalized_lang = normalize_lang(lang)
        memory_prefix = self._format_memory(context)
        reply_text = self._fake_model_reply(text, normalized_lang, memory_prefix)
        latency_ms = int((time.time() - start) * 1000)
        self.metrics.record_latency("llm", latency_ms)
        self.logger.info({
            "event": "llm_complete",
            "trace_id": trace_id,
            "session_id": session_id,
            "lang": normalized_lang,
            "latency_ms": latency_ms,
        })
        return ChatResponse(reply=reply_text, lang=normalized_lang, context=context or [], trace_id=trace_id)

    def _fake_model_reply(self, text: str, lang: str, memory_prefix: str) -> str:
        canned = {
            "de": "Ich habe dich verstanden und antworte auf Deutsch.",
            "en": "I understood you and will reply in English.",
            "es": "Te entendí y responderé en español.",
            "pt": "Entendi você e vou responder em português.",
        }
        summary = text[:160]
        filler = canned.get(lang, canned["en"])
        tag = random.choice(["mistral", "llama", "qwen", "phi"])
        return f"{memory_prefix}{filler} Echo: {summary} [{tag}]"

    def _format_memory(self, context: Optional[List[dict]]) -> str:
        if not context:
            return ""
        recent = context[-5:]
        rendered = " | ".join([f"{turn['role']}: {turn['text']}" for turn in recent])
        return f"Contexto: {rendered}. "
