#!/usr/bin/env python3
"""
Test delle frasi-tampone — senza microfono, senza Claude.
Verifica: che siano della stessa voce, che partano subito, che ruotino, e SIMULA
il buco di attesa reale (3 secondi) per farti sentire l'effetto.

    python "99_Meta/tools/test_filler.py"
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import jarvis
import sounddevice as sd

PROVE = [
    ("Annota che domani ho il dentista alle quattro", "dovrebbe dire: lo annoto"),
    ("Cosa dice la tesi di mercato?",                 "dovrebbe dire: controllo"),
    ("Fammi un riassunto",                            "generica: un attimo"),
    ("Salva questa cosa nel vault",                   "annota (ruota sulla frase dopo)"),
]


def main():
    print("=" * 64)
    filler = jarvis.Filler(jarvis.VAULT / "99_Meta/tools/filler", voce_attesa=jarvis.VOICE.name)

    if not filler.pronto:
        print("  Nessuna frase-tampone caricata.")
        print("  Genera con:  python \"99_Meta/tools/genera_filler.py\"")
        return 1

    print(f"  Voce delle risposte : {jarvis.VOICE.name}")
    print(f"  Voce delle tampone  : {(jarvis.VAULT/'99_Meta/tools/filler/voce_usata.txt').read_text().strip()}")
    print(f"  Stessa voce         : {'SI' if filler.voce_ok else 'NO'}")
    print(f"  Categorie caricate  : { {k: len(v) for k, v in filler.banca.items()} }")
    print("=" * 64)

    for frase, atteso in PROVE:
        cat = jarvis.Filler.categoria(frase)
        print(f"\n  tu: \"{frase}\"")
        print(f"      categoria riconosciuta: {cat}   ({atteso})")

        t0 = time.time()
        filler.suona(cat)
        print(f"      la voce e' partita dopo {(time.time()-t0)*1000:.0f} ms   <-- deve essere ~0")

        time.sleep(3)      # finto tempo di Claude
        sd.wait()
        print("      [qui arriverebbe la risposta vera]")

    print("\n" + "=" * 64)
    print("  Se le tampone e la voce delle risposte suonano come la STESSA persona,")
    print("  il passo 2 e' a posto.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
