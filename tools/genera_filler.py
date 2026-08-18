#!/usr/bin/env python3
"""
Genera UNA VOLTA SOLA le frasi-tampone di Jarvis e le salva come file audio.

Perche': quando smetti di parlare, Claude ci mette 2-4 secondi. In quel buco Jarvis deve
dire subito qualcosa ("un attimo", "controllo") come farebbe una persona. Se il TTS le
generasse al momento, aggiungerebbe latenza invece di toglierla. Generandole prima:
    - partono in 0 ms (sono gia' audio, caricato in memoria)
    - costano zero
    - hanno la STESSA voce delle risposte, quindi non si sente lo stacco

    python "99_Meta/tools/genera_filler.py"          genera quelle mancanti
    python "99_Meta/tools/genera_filler.py" --tutte  rigenera tutto da capo
"""
import sys, wave
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
VOICE = TOOLS / "piper_voices/it_IT-serena-high.onnx"
DEST = TOOLS / "filler"

# Divise per situazione: sentire "lo annoto" quando chiedi una cosa stona.
FRASI = {
    "attesa": [          # domanda generica
        "Un attimo.",
        "Mmh, fammi vedere.",
        "Ci penso un secondo.",
        "Vediamo.",
        "Aspetta che controllo.",
    ],
    "cerca": [           # domande: cosa, quando, dove, quanto
        "Controllo subito.",
        "Guardo nel vault.",
        "Vado a vedere.",
    ],
    "annota": [          # annota, salva, scrivi, aggiungi, ricordami
        "Recepito, provvedo.",
        "Annotato.",
        "Provvedo subito.",
    ],
    "saluto": [          # avvio
        "Un momento, Stefano.",
    ],
}


def main():
    tutte = "--tutte" in sys.argv
    if not VOICE.exists():
        print(f"[X] Voce non trovata: {VOICE}")
        return 1

    print("Carico Piper...")
    from piper import PiperVoice
    voce = PiperVoice.load(str(VOICE))
    DEST.mkdir(exist_ok=True)

    fatti = saltati = 0
    for categoria, frasi in FRASI.items():
        for i, frase in enumerate(frasi):
            out = DEST / f"{categoria}_{i}.wav"
            if out.exists() and not tutte:
                saltati += 1
                continue
            with wave.open(str(out), "wb") as w:
                voce.synthesize_wav(frase, w)
            print(f"  [ok] {out.name:<14} \"{frase}\"")
            fatti += 1

    # Marchio la cartella con la voce usata: se un giorno cambi voce, Jarvis se ne accorge
    # e ti avverte, invece di farti sentire due persone diverse nella stessa frase.
    (DEST / "voce_usata.txt").write_text(VOICE.name, encoding="utf-8")

    print(f"\nGenerati {fatti}, gia' presenti {saltati}.")
    print(f"Voce usata: {VOICE.name}  (uguale a quella delle risposte)")
    print(f"Cartella: {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
