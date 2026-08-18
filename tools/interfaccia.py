#!/usr/bin/env python3
"""
La finestra di Jarvis: una pagina locale che mostra cosa sta facendo la macchina.

Perche' esiste: parlando al terminale non si capisce se ti sta sentendo, se sta pensando
o se si e' piantato. Qui si vede. In ascolto la linea disegna il TUO volume vero, quindi
un'occhiata basta per sapere se il microfono ti prende.

Non e' un programma a parte: jarvis.py lo avvia dentro di se' in un thread.
    da jarvis.py ->  import interfaccia; interfaccia.avvia()
                     interfaccia.stato("ascolto") / .dice("tu", "...") / .misure(...)

Dipendenze: fastapi + uvicorn (gia' installate, leggere).
"""
import json, queue, socket, asyncio, threading, webbrowser, subprocess, shutil
from pathlib import Path

PAGINA = Path(__file__).resolve().parent / "interfaccia.html"
PORTA = 8765

_coda: "queue.Queue[str]" = queue.Queue()
_attiva = False


# ============================ API per jarvis.py ============================

def _manda(**dati):
    if _attiva:
        _coda.put(json.dumps(dati, ensure_ascii=False))


def stato(valore: str):
    """attesa | ascolto | pensa | parla"""
    _manda(tipo="stato", valore=valore)


def livello(v: float):
    """Volume del microfono in questo istante (0..1). Disegna l'onda."""
    _manda(tipo="livello", valore=round(float(v), 4))


def dice(chi: str, testo: str):
    """chi = 'tu' oppure 'jarvis'"""
    _manda(tipo=chi, testo=testo)


def misure(tempo=None, costo=None, modello=None, sessione=None):
    _manda(tipo="misure", tempo=tempo, costo=costo, modello=modello, sessione=sessione)


# ============================== il server ==============================

def _crea_app():
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse

    connessi: set = set()

    @asynccontextmanager
    async def ciclo_vita(app):
        async def giro():
            while True:
                try:
                    msg = _coda.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.03)
                    continue
                for s in list(connessi):
                    try:
                        await s.send_text(msg)
                    except Exception:
                        connessi.discard(s)
        compito = asyncio.create_task(giro())
        yield
        compito.cancel()

    app = FastAPI(lifespan=ciclo_vita)

    @app.get("/")
    def pagina():
        # Il nome arriva da jarvis.NOME: cambiando quello cambia anche la finestra.
        try:
            import jarvis
            nome = jarvis.NOME
        except Exception:
            nome = "Stefano"
        return HTMLResponse(PAGINA.read_text(encoding="utf-8").replace("{{NOME}}", nome))

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        await sock.accept()
        connessi.add(sock)
        try:
            while True:
                await sock.receive_text()      # la pagina non parla, resta solo in ascolto
        except Exception:
            pass
        finally:
            connessi.discard(sock)

    return app


def _porta_libera(p: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) != 0


def avvia(apri_finestra: bool = True) -> str | None:
    """Accende il server in un thread e apre la finestra. Ritorna l'indirizzo."""
    global _attiva
    if _attiva:
        return f"http://127.0.0.1:{PORTA}"
    if not PAGINA.exists():
        print(f"⚠️  Manca {PAGINA.name}: interfaccia non avviata.")
        return None
    if not _porta_libera(PORTA):
        print(f"⚠️  La porta {PORTA} e' gia' occupata: interfaccia non avviata.")
        return None

    import uvicorn
    app = _crea_app()

    def gira():
        uvicorn.run(app, host="127.0.0.1", port=PORTA, log_level="critical")

    threading.Thread(target=gira, daemon=True).start()
    _attiva = True

    url = f"http://127.0.0.1:{PORTA}"
    if apri_finestra:
        threading.Timer(1.2, lambda: _apri(url)).start()
    return url


def _apri(url: str):
    """Finestra dedicata, senza barra del browser. Se non riesce, apre una scheda normale."""
    for nome in ("msedge", "chrome"):
        exe = shutil.which(nome)
        if exe:
            try:
                subprocess.Popen([exe, f"--app={url}", "--window-size=760,880"])
                return
            except Exception:
                pass
    webbrowser.open(url)


if __name__ == "__main__":
    # Prova in solitaria: accende la finestra e simula un giro completo.
    import time, math, random
    print("Apro la finestra di prova...")
    avvia()
    time.sleep(2.5)
    stato("attesa"); time.sleep(1.5)

    stato("ascolto")
    for i in range(45):
        livello(abs(math.sin(i / 4)) * random.uniform(.4, .95))
        time.sleep(0.07)

    dice("tu", "Quali progetti ho aperti?")
    stato("pensa"); time.sleep(3)

    dice("jarvis", "Sei progetti. I principali sono il sito, l'app e la revisione dei contratti.")
    misure(tempo=6.7, costo=0.0044, modello="haiku", sessione=True)
    stato("parla"); time.sleep(4)
    stato("attesa")
    print("Giro completato. Ctrl+C per chiudere.")
    while True:
        time.sleep(1)
