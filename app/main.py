from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.models.payloads import ChatRequest, HealthStatus, TTSRequest, TranscribeRequest
from app.services.asr import ASRService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.utils.context import ContextMemory
from app.utils.logging import build_logger, log_request
from app.utils.metrics import Metrics

app = FastAPI(title="Open Voice Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = build_logger()
metrics = Metrics()
asr_service = ASRService(metrics=metrics, logger=logger)
llm_service = LLMService(metrics=metrics, logger=logger)
tts_service = TTSService(metrics=metrics, logger=logger)
context_memory = ContextMemory()

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="ui")


@app.get("/ui")
async def ui_root():
    """Ensure /ui without trailing slash serves the SPA index."""
    return RedirectResponse(url="/ui/")

@app.post("/transcribe")
async def transcribe(request: TranscribeRequest):
    trace_id = request.trace_id or metrics.create_trace_id()
    log_request(logger, "transcribe", trace_id, request.session_id, request.lang)
    result = await asr_service.transcribe(request.audio_base64, trace_id=trace_id, session_id=request.session_id)
    return JSONResponse(result)


@app.post("/chat")
async def chat(request: ChatRequest):
    trace_id = request.trace_id or metrics.create_trace_id()
    log_request(logger, "chat", trace_id, request.session_id, request.lang)
    context = context_memory.get(request.session_id)
    reply = await llm_service.generate_reply(
        request.text,
        lang=request.lang,
        session_id=request.session_id,
        context=context,
        trace_id=trace_id,
    )
    context_memory.append(request.session_id, "user", request.text, reply.lang)
    context_memory.append(request.session_id, "assistant", reply.reply, reply.lang)
    return JSONResponse(reply.model_dump())


@app.post("/tts")
async def tts(request: TTSRequest):
    trace_id = request.trace_id or metrics.create_trace_id()
    log_request(logger, "tts", trace_id, None, request.lang)
    result = await tts_service.synthesize(request.text, lang=request.lang, voice=request.voice, trace_id=trace_id)
    return JSONResponse(result)


@app.get("/health")
async def health():
    status = HealthStatus(asr="ok", llm="ok", tts="ok")
    return status


@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    trace_id = metrics.create_trace_id()
    session_id = None
    lang = "auto"
    try:
        start_event = await ws.receive_json()
        session_id = start_event.get("session_id")
        lang = start_event.get("lang", "auto")
        log_request(logger, "stream_start", trace_id, session_id, lang)
        await ws.send_json({"type": "ack", "trace_id": trace_id})
    except WebSocketDisconnect:
        return

    transcript_chunks = []
    while True:
        try:
            message = await ws.receive()
        except WebSocketDisconnect:
            break

        if message["type"] == "websocket.receive":
            if "bytes" in message and message["bytes"] is not None:
                partial = await asr_service.transcribe_stream(message["bytes"], lang_hint=lang, trace_id=trace_id)
                transcript_chunks.append(partial["text"])
                await ws.send_json({"type": "partial_text", "text": partial["text"], "lang": partial["lang"]})
            elif "text" in message and message["text"]:
                await ws.send_json({"type": "error", "code": "unexpected_text"})
        elif message["type"] == "websocket.disconnect":
            break

        if len(transcript_chunks) >= 3:
            full_text = " ".join(transcript_chunks)
            context = context_memory.get(session_id)
            reply = await llm_service.generate_reply(full_text, lang=lang, session_id=session_id, context=context, trace_id=trace_id)
            context_memory.append(session_id, "user", full_text, reply.lang)
            context_memory.append(session_id, "assistant", reply.reply, reply.lang)
            await ws.send_json({"type": "final_text", "text": full_text, "lang": reply.lang})
            async for audio_chunk in tts_service.stream(reply.reply, lang=reply.lang, voice="default", trace_id=trace_id):
                await ws.send_bytes(audio_chunk)
            await ws.send_json({"type": "done", "trace_id": trace_id})
            transcript_chunks.clear()

    await ws.close()
