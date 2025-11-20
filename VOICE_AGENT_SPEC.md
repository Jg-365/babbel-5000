# Agente de Voz Interativo Multilíngue (Open-Source)

## 1. Visão Geral do Produto
- **Objetivo do assistente:** oferecer conversação por voz em tempo real, multimodalidade básica (fala ↔ texto ↔ fala) e suporte multilíngue sem custos de licenciamento.
- **Proposta de valor:** execução 100% local ou em servidor simples, mantendo privacidade; uso exclusivo de modelos e bibliotecas open-source; experiência fluida para prática de idiomas e automações por voz.
- **Diferencial:** pipeline inteiramente offline/gratuito (ASR + LLM + TTS), suporte robusto ao alemão (input/output) e a PT/EN/ES, streaming de resposta, e arquitetura modular para evolução.
- **Casos de uso:**
  - Prática de conversação em idiomas (incluindo alemão com respostas contextualizadas).
  - Assistente geral de comandos de voz em desktop ou servidor pessoal.
  - Interface de voz para aplicações internas (suporte, FAQs, automações). 
  - Modo tutor de idiomas com correção on-the-fly.

## 2. Requisitos Funcionais Detalhados
1. **Captura de áudio do usuário**
   - Descrição: microfone via WebRTC (browser) ou stream PCM/WAV via cliente nativo; amostragem 16 kHz mono.
   - Critérios de aceitação: áudio recebido como chunks < 1s; suporte a WebSocket; formato PCM 16-bit little-endian.
2. **Detecção automática de idioma (PT/EN/DE/ES)**
   - Descrição: classificador leve (fastText langid) ou heurística do próprio ASR confidences para PT/EN/DE/ES.
   - Critérios: acurácia >90% em frases curtas; expõe código do idioma no payload para o LLM/TTS.
3. **Transcrição ASR offline**
   - Descrição: Whisper.cpp ou Faster-Whisper, modelo médio/grande quantizado (int8/int4) com VAD opcional.
   - Critérios: latência < 1.5s para 5s de áudio em CPU moderna; retorna timestamps opcionais; suporta alemão, inglês, espanhol, português.
4. **Processamento NLU/LLM open-source**
   - Descrição: pipeline de prompts com modelos Llama 3.1 8B, Qwen 2.5 7B, Mistral Nemo ou Phi-4 Mini (GGUF/ONNX/Intel-ext). 
   - Critérios: resposta coerente no idioma detectado; contexto de 5–10 turnos preservado; tempo de inferência < 2s em GPU média ou <5s CPU.
5. **Suporte para conversação aberta**
   - Descrição: prompts de sistema multilíngues, modo tutor, modo assistente geral; fallback seguro (mensagem neutra) em caso de falha.
   - Critérios: nunca retornar texto vazio; se erro, responder mensagem padrão "Desculpe, não consegui processar agora".
6. **Memória curta (5–10 turnos)**
   - Descrição: janela deslizante de mensagens armazenadas em cache (Redis local ou in-memory) por sessão.
   - Critérios: pelo menos 5 turnos mantidos; exclusão FIFO quando exceder; inclui idioma atual.
7. **Transformação da resposta em áudio (TTS gratuito)**
   - Descrição: Coqui TTS ou Piper TTS com vozes específicas para DE/EN/ES/PT; suporta SSML básico ou tags simples para pausas.
   - Critérios: latência <1.5s para 200 caracteres; saída WAV/OGG 16 kHz mono; volume normalizado.
8. **Streaming da resposta**
   - Descrição: chunking de texto via server-sent tokens do LLM e/ou áudio progressivo via WebSocket binário.
   - Critérios: primeiro byte em <800 ms após início da inferência; chunks <512 ms.
9. **Fallback em caso de falha**
   - Descrição: watchdog de tempo máximo (timeout ASR/LLM/TTS), fallback para mensagem estática em texto + áudio pré-gerado.
   - Critérios: se latência total > 8s ou erro de módulo, retornar fallback; log do motivo.
10. **Logs e métricas básicos**
    - Descrição: logging estruturado (JSON) com tempos de ASR/LLM/TTS, idioma detectado, status; métricas Prometheus simples.
    - Critérios: cada requisição possui trace-id; exporta p95 latências; erros registrados com stack/causa.

## 3. Requisitos Não Funcionais
- **Desempenho:** latência alvo (voz→texto→voz) <4s em CPU moderna, <2.5s com GPU modesta; ASR ~1.5s/5s áudio, LLM 5–15 tok/s, TTS <1.5s/200 chars.
- **Escalabilidade:** implantação em contêineres; serviços ASR/LLM/TTS podem ser desacoplados e escalados horizontalmente; uso de fila leve (Redis/NATS) opcional.
- **Privacidade:** processamento local; nenhum envio para serviços pagos ou externos; armazenamento opcional de logs/áudio configurável.
- **Compatibilidade local:** suporte a Linux x86_64; dependências via Docker ou ambientes Python/Node; GPU CUDA opcional.
- **Consumo CPU/GPU:**
  - ASR quantizado roda em CPU; uso de GPU reduz latência.
  - LLM 7–8B quantizado int4/int8 para CPU; GPU de 6–8 GB recomendado para stream rápido.
  - TTS Coqui/Piper roda em CPU; uso de GPU opcional.
- **Limitações esperadas:** qualidade de voz limitada a modelos TTS; LLM 7–8B pode falhar em tarefas complexas; latência maior em hardware fraco.

## 4. Arquitetura Técnica Completa
- **Pipeline:** Cliente (microfone) → Gateway WebSocket/HTTP → Serviço ASR → Orquestrador (FastAPI/Node) com memória curta → Serviço LLM → Serviço TTS → Stream de áudio ao cliente.
- **Microserviços:**
  - `asr-service` (Whisper.cpp/Faster-Whisper REST/WebSocket).
  - `llm-service` (text-generation API compatível OpenAI ou vLLM-like self-hosted).
  - `tts-service` (Coqui/Piper REST/WebSocket).
  - `orchestrator` (contexto, roteamento, idioma, logs).
- **Comunicação:**
  - REST para requisições simples (`/transcribe`, `/chat`, `/tts`).
  - WebSocket `/stream` para áudio bidirecional (PCM 16-bit LE frames) e eventos JSON.
- **Formatos de mensagem:** JSON com `trace_id`, `session_id`, `lang`, `timestamps`, `payload` (texto ou base64 para áudio). Áudio binário puro em frames PCM.
- **Escalabilidade:** ASR/LLM/TTS podem ser independentes com auto-escalonamento; cache de contexto no Redis; balanceamento por round-robin.

## 5. Tecnologias Gratuitas Recomendadas
- **ASR:** Whisper.cpp (offline), Faster-Whisper (GPU/CPU, quantização int8/int4).
- **LLM:** Llama 3.1 8B (GGUF), Qwen 2.5 7B, Mistral Nemo, Phi-4 Mini; backends: llama.cpp, vLLM local, TensorRT-LLM (gratuito) onde aplicável.
- **TTS:** Coqui TTS; Piper TTS (recomendado para DE/EN/ES/PT, leve e rápido).
- **Orquestração:** Python + FastAPI ou Node.js + Bun; LangChainJS gratuito para chaining; Redis para contexto curto; NATS ou WebSocket nativo para streaming.

## 6. Fluxo de Interação (texto)
1. Usuário fala (microfone cliente envia frames PCM).
2. Gateway recebe e normaliza áudio.
3. ASR local (Whisper.cpp/Faster-Whisper) transcreve e envia texto + idioma provável.
4. Módulo NLU confirma idioma (langid) e ajusta prompt.
5. LLM processa intenção no idioma detectado e gera resposta textual.
6. TTS converte resposta para áudio no mesmo idioma (voz correspondente).
7. Servidor faz streaming de áudio ao cliente enquanto gera.
8. Orquestrador salva contexto (últimos turnos) e logs de latência.

## 7. API Design
- **POST `/transcribe`**
  - Payload: `audio_base64` (WAV/PCM 16k mono), `trace_id`, `session_id`.
  - Resposta: `{ "text": "...", "lang": "de|en|es|pt", "timestamps": [...] }`.
  - Erros: `400 audio_invalid`, `500 asr_failed`.
- **POST `/chat`**
  - Payload: `{ "text": "...", "lang": "auto|de|en|es|pt", "session_id": "...", "trace_id": "..." }`.
  - Resposta: `{ "reply": "...", "lang": "...", "context": [...] }`.
  - Erros: `400 invalid_lang`, `500 llm_failed`.
- **POST `/tts`**
  - Payload: `{ "text": "...", "lang": "de|en|es|pt", "voice": "default|custom", "trace_id": "..." }`.
  - Resposta: `audio_base64` (WAV/OGG), `duration_ms`.
  - Erros: `400 text_missing`, `500 tts_failed`.
- **WebSocket `/stream`**
  - Mensagens cliente→server: `{ "type": "start", "lang": "auto" }` seguido de frames binários PCM.
  - Mensagens server→cliente: eventos JSON `{ "type": "partial_text", "text": "..." }`, `{ "type": "final_text", ... }` e frames binários de áudio TTS.
  - Erros: evento `{ "type": "error", "code": "asr_timeout|llm_failed|tts_failed" }`.
- **GET `/health`**
  - Resposta: `{ "status": "ok", "asr": "ok", "llm": "ok", "tts": "ok" }`.

## 8. Modelo de Dados (JSON)
- **Contexto conversacional:**
```json
{
  "session_id": "uuid",
  "turns": [
    {"role": "user", "text": "...", "lang": "de", "ts": 1712345678},
    {"role": "assistant", "text": "...", "lang": "de", "ts": 1712345680}
  ],
  "lang": "de",
  "last_updated": 1712345680
}
```
- **Logs de áudio:**
```json
{
  "trace_id": "uuid",
  "session_id": "uuid",
  "lang": "de",
  "latency_ms": {"asr": 1200, "llm": 1800, "tts": 900},
  "status": "ok|error",
  "error": null,
  "timestamp": 1712345680
}
```
- **Sessão do usuário:**
```json
{
  "session_id": "uuid",
  "user_agent": "browser|cli",
  "created_at": 1712345600,
  "expires_at": 1712349200,
  "preferences": {"lang": "auto", "voice": "default"}
}
```

## 9. Plano de MVP (Versão Beta)
- **Semana 1:** Implementar captura de áudio + endpoint `/transcribe` com Whisper.cpp/Faster-Whisper local; healthcheck.
- **Semana 2:** Integrar LLM (Llama 3.1 8B/Qwen 2.5 7B) via API local; manter contexto curto in-memory.
- **Semana 3:** Integrar TTS (Piper/Coqui), endpoint `/tts`, respostas por áudio via REST.
- **Semana 4:** Pipeline completo voz↔voz com `/stream`, memória curta, fallback e métricas básicas.

## 10. Critérios de Sucesso
- Latência fim-a-fim p95 ≤ 4s (voz→voz) em CPU moderna; ≤2.5s com GPU modesta.
- Disponibilidade ≥ 99% em ambiente local/servidor único durante testes.
- Acurácia ASR em alemão WER ≤ 12% em frases de teste; detecção de idioma ≥ 90%.
- Naturalidade TTS nota ≥ 4/5 em avaliação subjetiva interna; volume consistente.
- Taxa de reconhecimento por idioma: p95 confiança ≥ 0.8 para PT/EN/DE/ES.

## 11. Limitações e Riscos
- Modelos 7–8B podem gerar respostas menos ricas que serviços pagos; contexto limitado.
- Execução local de Llama 3.1 8B pode ser lenta em CPU pura; exige quantização e possível KV-cache offloading.
- Piper/Coqui têm qualidade inferior a TTS comerciais; sotaques podem variar.
- Riscos de latência alta em dispositivos fracos; necessidade de parametrizar tamanho de modelo (tiny/base para hardware limitado).
- Manutenção de sincronização áudio/texto em streaming requer testes finos (buffer/jitter).

## 12. Extensões Futuras
- Slots de frases de comando ("abrir app", "criar nota"), integrando com automações locais (MQTT/CLI).
- Modo tutor de idiomas com feedback explícito e correção de pronúncia.
- Memória longa usando banco vetorial (Chroma/FAISS) gratuito e embeddings open-source.
- Suporte offline total com download automático de modelos em primeira execução.
- Integração com agentes (LangGraph/LangChainJS) para ferramentas locais gratuitas.

## 13. Output Final
Texto estruturado e técnico, usando apenas componentes open-source/gratuitos, pronto para uso em PRD e implementação imediata.
