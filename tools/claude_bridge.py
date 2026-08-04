#!/usr/bin/env python3
"""
claude_bridge.py — Ponte OpenAI-compatibile → Claude Code nel vault.

Espone un endpoint /v1/chat/completions (formato OpenAI) che, a ogni richiesta,
lancia `claude -p "<messaggio>"` DENTRO la cartella del vault, così la risposta
arriva con tutto il contesto del secondo cervello (CLAUDE.md, note, ecc.).

Serve a collegare la pipeline vocale HuggingFace speech-to-speech (il cui slot LLM
parla protocollo OpenAI) al cervello Claude Code — senza usare/pagare OpenAI.

Avvio:  python "99_Meta/tools/claude_bridge.py"
        → server su http://127.0.0.1:8000/v1
Config (variabili d'ambiente, tutte opzionali):
  JARVIS_VAULT_DIR   cartella del vault (default: questa)
  JARVIS_CLAUDE_CMD  eseguibile claude (default: risolto dal PATH)
  JARVIS_TIMEOUT     secondi max per una risposta (default 180)
  JARVIS_PORT        porta (default 8000)
Dipendenze: fastapi, uvicorn (leggere; niente torch/modelli).
"""
import os, time, uuid, json, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

VAULT_DIR = os.environ.get("JARVIS_VAULT_DIR") or str(Path(__file__).resolve().parents[2])
CLAUDE_CMD = os.environ.get("JARVIS_CLAUDE_CMD") or shutil.which("claude") or "claude"
TIMEOUT = int(os.environ.get("JARVIS_TIMEOUT", "180"))
MODEL_ID = os.environ.get("JARVIS_MODEL_NAME", "claude-code-vault")

app = FastAPI(title="Jarvis Claude Bridge", version="0.1")


def _content_to_text(content) -> str:
    """OpenAI content puo' essere str o lista di parti {type,text}. Estrae il testo."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                parts.append(p.get("text", ""))
            elif isinstance(p, str):
                parts.append(p)
        return " ".join(parts)
    return str(content or "")


def messages_to_prompt(messages) -> str:
    """Prende l'ultimo messaggio utente come prompt (il contesto del vault viene da CLAUDE.md)."""
    for m in reversed(messages or []):
        if m.get("role") == "user":
            return _content_to_text(m.get("content")).strip()
    return ""


def _build_cmd(prompt: str):
    base = [CLAUDE_CMD, "-p", prompt]
    # Su Windows i file .CMD/.BAT vanno lanciati tramite cmd /c.
    if os.name == "nt" and CLAUDE_CMD.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c"] + base
    return base


def run_claude(prompt: str) -> str:
    if not prompt:
        return "(nessun messaggio ricevuto)"
    try:
        proc = subprocess.run(
            _build_cmd(prompt),
            cwd=VAULT_DIR,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return "(timeout: Claude non ha risposto in tempo)"
    except FileNotFoundError:
        return f"(errore: eseguibile claude non trovato: {CLAUDE_CMD})"
    out = (proc.stdout or "").strip()
    if not out:
        err = (proc.stderr or "").strip()
        out = f"(nessuna risposta) {err[:400]}" if err else "(nessuna risposta)"
    return out


def _completion_payload(text: str) -> dict:
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex[:24],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_ID,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@app.get("/v1/models")
def list_models():
    return {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "local-claude-code"}]}


@app.get("/health")
def health():
    return {"status": "ok", "vault": VAULT_DIR, "claude": CLAUDE_CMD}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    prompt = messages_to_prompt(body.get("messages", []))
    text = run_claude(prompt)

    if body.get("stream"):
        # Streaming SSE minimale: un chunk di contenuto + [DONE].
        cid = "chatcmpl-" + uuid.uuid4().hex[:24]
        created = int(time.time())

        def gen():
            first = {"id": cid, "object": "chat.completion.chunk", "created": created,
                     "model": MODEL_ID, "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}]}
            yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"
            done = {"id": cid, "object": "chat.completion.chunk", "created": created,
                    "model": MODEL_ID, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return JSONResponse(_completion_payload(text))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("JARVIS_PORT", "8000"))
    print(f"[bridge] Vault: {VAULT_DIR}")
    print(f"[bridge] Claude: {CLAUDE_CMD}")
    print(f"[bridge] In ascolto su http://127.0.0.1:{port}/v1  (Ctrl+C per fermare)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
