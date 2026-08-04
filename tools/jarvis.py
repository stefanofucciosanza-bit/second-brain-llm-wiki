#!/usr/bin/env python3
"""
JARVIS — layer vocale del secondo cervello (Fase 1)
Flusso:  microfono -> faster-whisper (STT) -> Claude Code headless nel vault -> Piper (TTS)

Uso:
    python "99_Meta/tools/jarvis.py"

Comandi vocali utili:
    "annota che ..."                    -> crea/aggiorna una nota nel vault
    "cosa dice la tesi di mercato?"     -> interroga il secondo cervello
    "esci" / "stop"                     -> chiude Jarvis
"""
import os, sys, wave, queue, shutil, tempfile, subprocess
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

# ----------------------------- CONFIG -----------------------------
VAULT = Path(__file__).resolve().parents[2]           # root del vault
VOICE = VAULT / "99_Meta/tools/piper_voices/it_IT-paola-medium.onnx"
WHISPER_MODEL = "small"      # base = piu' veloce | small = piu' preciso in italiano
MIC = None                   # None = microfono di default; oppure indice (es. 7 per Jabra)
SAMPLE_RATE = 16000
CLAUDE_TIMEOUT = 240         # secondi

PERSONA = (
    "Sei Jarvis, l'assistente vocale del secondo cervello di Stefano. "
    "Segui le regole di CLAUDE.md in questo vault. "
    "IMPORTANTE: la tua risposta verra' LETTA AD ALTA VOCE, quindi rispondi in italiano, "
    "in massimo 3 frasi, con tono naturale parlato, senza markdown, senza elenchi puntati, "
    "senza percorsi di file. Se ti viene chiesto di annotare o salvare qualcosa, "
    "crea o aggiorna la nota nel vault seguendo le convenzioni, poi conferma a voce in una frase."
)
# ------------------------------------------------------------------


def registra() -> np.ndarray | None:
    """Registra dal microfono finche' l'utente non preme INVIO."""
    q: queue.Queue = queue.Queue()

    def cb(indata, frames, time_info, status):
        q.put(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        device=MIC, callback=cb):
        input("🎙️  Sto ascoltando... premi INVIO per fermare.\n")

    blocchi = []
    while not q.empty():
        blocchi.append(q.get())
    if not blocchi:
        return None
    return np.concatenate(blocchi, axis=0)


def trascrivi(audio: np.ndarray, model) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    sf.write(tmp, audio, SAMPLE_RATE)
    segmenti, _ = model.transcribe(tmp, language="it", vad_filter=True)
    testo = " ".join(s.text for s in segmenti).strip()
    os.unlink(tmp)
    return testo


def chiedi_a_claude(domanda: str) -> str:
    """Esegue Claude Code headless DENTRO il vault (legge e scrive le note)."""
    exe = shutil.which("claude") or "claude"
    prompt = f"{PERSONA}\n\nRichiesta di Stefano: {domanda}"
    try:
        r = subprocess.run(
            [exe, "-p", prompt, "--permission-mode", "acceptEdits"],
            cwd=str(VAULT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=CLAUDE_TIMEOUT,
        )
        out = (r.stdout or "").strip()
        return out or (r.stderr or "Non ho ricevuto risposta.").strip()
    except subprocess.TimeoutExpired:
        return "La richiesta ha impiegato troppo tempo, riprova."


def pulisci_per_voce(t: str) -> str:
    import re
    t = re.sub(r"```.*?```", " ", t, flags=re.S)     # blocchi di codice
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)         # wikilink
    t = re.sub(r"[*_#`>|-]", " ", t)                  # markdown
    t = re.sub(r"\s+", " ", t)
    return t.strip()[:1200]


def parla(testo: str, voce):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    with wave.open(tmp, "wb") as w:
        voce.synthesize_wav(testo, w)
    dati, sr = sf.read(tmp, dtype="float32")
    sd.play(dati, sr); sd.wait()
    os.unlink(tmp)


def main():
    print(f"📂 Vault: {VAULT}")
    print("⏳ Carico i modelli (la prima volta scarica Whisper)...")
    from faster_whisper import WhisperModel
    from piper import PiperVoice
    stt = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    voce = PiperVoice.load(str(VOICE))
    print("✅ Jarvis è online.\n")
    parla("Ciao Stefano, sono Jarvis. Sono in ascolto.", voce)

    while True:
        input("\n▶️  Premi INVIO per parlare (Ctrl+C per uscire)...")
        audio = registra()
        if audio is None or len(audio) < SAMPLE_RATE // 2:
            print("… non ho sentito nulla.")
            continue

        testo = trascrivi(audio, stt)
        if not testo:
            print("… non ho capito.")
            continue
        print(f"🗣️  Tu: {testo}")

        if any(k in testo.lower() for k in ("esci", "chiudi jarvis", "stop jarvis")):
            parla("A dopo, Stefano.", voce)
            break

        print("🧠 Sto pensando...")
        risposta = pulisci_per_voce(chiedi_a_claude(testo))
        print(f"🤖 Jarvis: {risposta}\n")
        parla(risposta, voce)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Jarvis chiuso.")
