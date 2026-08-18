#!/usr/bin/env python3
"""
Prova del microfono — 5 secondi. Dimmi se ti sente e a che volume.
Da lanciare PRIMA di Jarvis, se hai il dubbio che non ti senta.

    python "99_Meta/tools/prova_microfono.py"
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import sounddevice as sd
import jarvis

DURATA = 5


def main():
    print("=" * 58)
    print(f"  Microfono in uso: {sd.query_devices(kind='input')['name'][:40]}")
    print(f"  Soglia per capire che stai parlando: {jarvis.SOGLIA_VOCE}")
    print("=" * 58)
    print(f"\n  PARLA per {DURATA} secondi. Di' quello che vuoi.\n")

    livelli = []
    q = []

    def cb(indata, frames, t, status):
        q.append(indata.copy())
        v = jarvis._rms(indata)
        livelli.append(v)
        barre = int(min(v / 60, 40))
        stato = "PARLI" if v > jarvis.SOGLIA_VOCE else "     "
        print(f"\r  {stato} |{'#' * barre}{' ' * (40 - barre)}| {v:6.0f}", end="")

    with sd.InputStream(samplerate=jarvis.SAMPLE_RATE, channels=1, dtype="int16",
                        callback=cb, blocksize=int(jarvis.SAMPLE_RATE * 0.1)):
        time.sleep(DURATA)

    picco = max(livelli) if livelli else 0
    medio = sum(livelli) / len(livelli) if livelli else 0
    print("\n\n" + "=" * 58)
    print(f"  Volume massimo rilevato : {picco:.0f}")
    print(f"  Volume medio            : {medio:.0f}")
    print(f"  Soglia richiesta        : {jarvis.SOGLIA_VOCE}")
    print("=" * 58)

    if picco < 100:
        print("\n  [X] NON TI SENTE.")
        print("      Windows: Impostazioni > Privacy > Microfono ->")
        print("      'Consenti alle app desktop di accedere al microfono' deve essere ATTIVO.")
    elif picco < jarvis.SOGLIA_VOCE:
        nuova = int(picco * 0.4)
        print(f"\n  [!] Ti sente, ma PIANO: il picco ({picco:.0f}) non supera la soglia.")
        print(f"      Apri jarvis.py e metti  SOGLIA_VOCE = {nuova}")
    else:
        print("\n  [OK] Ti sente bene. Puoi lanciare Jarvis.")

    # Riascolto: cosi senti come ti sente lui
    if q:
        audio = np.concatenate(q, axis=0).astype("float32") / 32768.0
        print("\n  Riascolto di come ti ha sentito...")
        sd.play(audio, jarvis.SAMPLE_RATE); sd.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
