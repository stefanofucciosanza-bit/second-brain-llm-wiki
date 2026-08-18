#!/usr/bin/env python3
"""
Fa sentire la STESSA frase con tutte le voci italiane disponibili, una dopo l'altra.
Serve a decidere con le orecchie, non con le specifiche.

    python "99_Meta/tools/confronta_voci.py"
"""
import time, wave, tempfile, os
from pathlib import Path

import sounddevice as sd
import soundfile as sf

VOCI_DIR = Path(__file__).resolve().parent / "piper_voices"

FRASE = ("Il fornitore ha confermato la consegna per giovedi'. "
         "Ho aggiornato la nota con i dettagli.")


def main():
    from piper import PiperVoice

    modelli = sorted(VOCI_DIR.glob("*.onnx"))
    if not modelli:
        print("Nessuna voce trovata in", VOCI_DIR)
        return 1

    print("=" * 62)
    print("  CONFRONTO VOCI — stessa frase, voci diverse")
    print("=" * 62)
    print(f'\n  Frase: "{FRASE}"\n')

    for m in modelli:
        peso = m.stat().st_size / 1_000_000
        print(f"  --- {m.stem}  ({peso:.0f} MB)")
        t = time.time()
        voce = PiperVoice.load(str(m))
        caricamento = time.time() - t

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = f.name
        t = time.time()
        with wave.open(tmp, "wb") as w:
            voce.synthesize_wav(FRASE, w)
        sintesi = time.time() - t

        dati, sr = sf.read(tmp, dtype="float32")
        durata = len(dati) / sr
        print(f"      caricamento {caricamento:.1f}s | sintesi {sintesi:.1f}s | audio {durata:.1f}s")
        print("      >>> ASCOLTA <<<")
        sd.play(dati, sr)
        sd.wait()
        os.unlink(tmp)
        time.sleep(0.6)
        print()

    print("=" * 62)
    print("  Quale ti convince di piu'? Se nessuna, si passa a una voce")
    print("  in cloud (ElevenLabs): piu' umana, ma a pagamento.")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
