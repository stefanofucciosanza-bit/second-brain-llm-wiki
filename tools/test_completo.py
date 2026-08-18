#!/usr/bin/env python3
"""
TEST COMPLETO della catena di Jarvis — tutto tranne il microfono.

Domanda scritta -> tampone -> Claude che cerca nel vault -> risposta letta ad alta voce.
Serve a verificare che l'impianto regga PRIMA di provare a voce: se qualcosa si rompe,
si vede qui e non mentre stai parlando.

    python "99_Meta/tools/test_completo.py"
    python "99_Meta/tools/test_completo.py" "la tua domanda"
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import jarvis
import sounddevice as sd

DOMANDA_DEFAULT = ("Cerca nel vault e dimmi in una sola frase qual e' il prossimo passo "
                   "del progetto principale.")


def main():
    domanda = " ".join(sys.argv[1:]) or DOMANDA_DEFAULT
    print("=" * 66)
    print("  TEST COMPLETO — tutto tranne il microfono")
    print("=" * 66)

    # --- 1. microfono presente? (non lo usiamo, ma serve sapere che c'e') ---
    print("\n[1/5] Microfoni disponibili")
    try:
        ingressi = [(i, d["name"]) for i, d in enumerate(sd.query_devices())
                    if d["max_input_channels"] > 0]
        for i, nome in ingressi[:6]:
            print(f"      {i}: {nome[:58]}")
        predefinito = sd.query_devices(kind="input")["name"]
        print(f"      -> predefinito: {predefinito[:55]}")
    except Exception as e:
        print(f"      [!] problema con l'audio in ingresso: {e}")

    # --- 2. voce ---
    print("\n[2/5] Voce (Piper)")
    t = time.time()
    from piper import PiperVoice
    voce = PiperVoice.load(str(jarvis.VOICE))
    print(f"      caricata in {time.time()-t:.1f}s — {jarvis.VOICE.name}")

    # --- 3. tampone ---
    print("\n[3/5] Frasi-tampone")
    filler = jarvis.Filler(jarvis.VAULT / "99_Meta/tools/filler", voce_attesa=jarvis.VOICE.name)
    if filler.pronto:
        print(f"      {sum(len(v) for v in filler.banca.values())} frasi, stessa voce: "
              f"{'SI' if filler.voce_ok else 'NO'}")
    else:
        print("      [!] nessuna tampone caricata")

    # --- 3bis. sottofondo ---
    musica = jarvis.Sottofondo(jarvis.VAULT / "99_Meta/tools/musica")
    if musica.pronto:
        musica.avvia()
        print(f"\n[3b ] Sottofondo: {musica.brano[:45]}")

    # --- 4. cervello ---
    print("\n[4/5] Cervello (sessione viva)")
    t = time.time()
    cervello = jarvis.Cervello()
    print(f"      processo avviato in {time.time()-t:.1f}s, vivo={cervello.vivo()}, "
          f"modello={cervello.modello}")

    # --- 5. il giro completo ---
    print("\n[5/5] GIRO COMPLETO")
    print(f'      domanda: "{domanda}"\n')

    t0 = time.time()
    categoria = jarvis.Filler.categoria(domanda)
    musica.abbassa()
    filler.suona(categoria)
    print(f"      [{time.time()-t0:5.2f}s] 🔊 tampone ({categoria}) — dovresti sentirla ADESSO")

    r = cervello.chiedi(domanda)
    print(f"      [{time.time()-t0:5.2f}s] 🧠 risposta arrivata")

    sd.wait()
    tetto = jarvis.tetto_parole(domanda)
    risposta, tagliata = jarvis.accorcia(jarvis.pulisci_per_voce(r.testo), tetto)
    print(f'      [tetto: {tetto} parole]')
    print(f"\n      Jarvis: {risposta}\n")

    t1 = time.time()
    jarvis.parla(risposta, voce)
    print(f"      [{time.time()-t0:5.2f}s] 🔊 finito di parlare "
          f"(la lettura e' durata {time.time()-t1:.1f}s)")
    musica.alza(); time.sleep(1.5); musica.ferma()

    print("\n" + "=" * 66)
    print(f"  Tempo di Claude       : {r.secondi:.1f}s (prima parola {r.primo_token:.1f}s)")
    print(f"  Costo della sessione  : ${r.costo:.4f}")
    print(f"  Silenzio percepito    : ~0s (coperto dalla tampone)")
    print("=" * 66)
    print("\n  Se hai sentito DUE frasi con la STESSA voce e la risposta")
    print("  viene davvero dal vault, l'impianto regge. Poi si prova a voce:")
    print('      python "99_Meta/tools/jarvis.py"')
    cervello.chiudi()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
