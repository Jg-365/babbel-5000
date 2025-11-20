# babbel-5000

Implementação inicial de um agente de voz multilíngue totalmente open-source seguindo o escopo definido em `VOICE_AGENT_SPEC.md`.

## Visão geral
- Stack: **FastAPI** para orquestração, serviços modulares de ASR/LLM/TTS simulados para permitir desenvolvimento offline imediato.
- Idiomas: suporte a alemão, inglês, espanhol e português (detecção e resposta com memória curta por sessão).
- Streaming: WebSocket `/stream` com reconhecimento incremental e áudio binário.

## Como executar
```bash
pip install -r requirements.txt
# Linux/macOS
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Windows (quando o executável uvicorn não estiver no PATH)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Interface Web
- Acesse http://127.0.0.1:8000/ui/ (ou http://127.0.0.1:8000/ui) para abrir o playground responsivo.
- A UI é mobile-first, solicita acesso ao microfone para voz ↔ voz e usa o mesmo host dos endpoints.
- Use o seletor de idioma para travar DE/EN/ES/PT ou deixe "Auto" para detecção automática.

## Endpoints principais
- `POST /transcribe`: recebe áudio base64 e retorna texto + idioma detectado.
- `POST /chat`: gera resposta com contexto curto armazenado em memória.
- `POST /tts`: sintetiza áudio base64 a partir de texto.
- `WebSocket /stream`: fluxo bidirecional de áudio e eventos JSON.
- `GET /health`: status de cada módulo.

## Observações
Os serviços de ASR/LLM/TTS estão implementados com saídas simuladas e métricas básicas para validar o pipeline. Eles podem ser substituídos por Whisper.cpp/Faster-Whisper, modelos LLM open-source e Coqui/Piper TTS conforme os binários/modelos forem disponibilizados localmente.
