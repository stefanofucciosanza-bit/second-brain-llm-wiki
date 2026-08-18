#!/usr/bin/env python3
"""
Dove se ne vanno i secondi. Misura OGNI pezzo della catena separatamente.

    python "99_Meta/tools/misura_tempi.py"
"""
import sys, time, wave, tempfile, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, soundfile as sf, jarvis

RISPOSTA_TIPO = ("Ne hai sei aperti. I principali sono il sito, l'app di fatturazione "
                 "e la revisione dei contratti. Poi c'e' il corso che stai seguendo.")


def sintetizza(voce, testo):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    with wave.open(tmp, "wb") as w:
        voce.synthesize_wav(testo, w)
    d, sr = sf.read(tmp, dtype="float32")
    os.unlink(tmp)
    return d, sr


def main():
    print("=" * 60)
    print("  DOVE SE NE VANNO I SECONDI")
    print("=" * 60)

    # 1. attesa fissa del silenzio
    print(f"\n1. Attesa silenzio (fissa)      {jarvis.SILENZIO_STOP:5.1f}s   <- SILENZIO_STOP")

    # 2. trascrizione: simulo 4 secondi di parlato
    from faster_whisper import WhisperModel
    print(f"\n2. Trascrizione — modello '{jarvis.WHISPER_MODEL}'")
    t = time.time()
    stt = WhisperModel(jarvis.WHISPER_MODEL, device="cpu", compute_type="int8")
    print(f"   caricamento (una volta sola)  {time.time()-t:5.1f}s")

    from piper import PiperVoice
    voce = PiperVoice.load(str(jarvis.VOICE))
    finta, sr_v = sintetizza(voce, "Quali progetti ho aperti in questo momento?")
    finta16 = np.interp(np.linspace(0, len(finta), int(len(finta) * 16000 / sr_v)),
                        np.arange(len(finta)), finta).astype("float32")
    t = time.time()
    jarvis.trascrivi((finta16 * 32767).astype("int16").reshape(-1, 1), stt)
    t_stt = time.time() - t
    print(f"   PER OGNI FRASE                {t_stt:5.1f}s   <- pesa a ogni turno")

    # 3. Claude (gia' misurato)
    print(f"\n3. Claude (indice precaricato)   ~6.7s   <- misurato prima")

    # 4. sintesi della voce
    print(f"\n4. Sintesi voce — {jarvis.VOICE.stem}")
    t = time.time()
    audio, sr = sintetizza(voce, RISPOSTA_TIPO)
    t_tts = time.time() - t
    durata = len(audio) / sr
    print(f"   generare l'audio              {t_tts:5.1f}s   <- silenzio prima di sentire una parola")
    print(f"   durata dell'audio             {durata:5.1f}s   <- quanto parla")

    # 5. confronto con la voce piu' leggera
    altra = jarvis.VOICE.parent / "it_IT-paola-medium.onnx"
    if altra.exists():
        v2 = PiperVoice.load(str(altra))
        t = time.time(); sintetizza(v2, RISPOSTA_TIPO); t2 = time.time() - t
        print(f"\n   (paola-medium ci mette        {t2:5.1f}s, cioe' {t_tts/t2:.1f}x meno)")

    tot = jarvis.SILENZIO_STOP + t_stt + 6.7 + t_tts + durata
    print("\n" + "=" * 60)
    print(f"  TOTALE da quando smetti di parlare: {tot:.1f}s")
    print("=" * 60)
    print(f"""
  Ripartizione:
    silenzio      {jarvis.SILENZIO_STOP:5.1f}s  ({jarvis.SILENZIO_STOP/tot*100:4.1f}%)
    trascrizione  {t_stt:5.1f}s  ({t_stt/tot*100:4.1f}%)
    Claude         6.7s  ({6.7/tot*100:4.1f}%)
    sintesi voce  {t_tts:5.1f}s  ({t_tts/tot*100:4.1f}%)
    lettura       {durata:5.1f}s  ({durata/tot*100:4.1f}%)  <- di solito il piu' grosso
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
