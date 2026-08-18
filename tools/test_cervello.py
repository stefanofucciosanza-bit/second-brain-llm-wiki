#!/usr/bin/env python3
"""
Test del cervello di Jarvis — SENZA microfono e SENZA voce.
Verifica tre cose: che la sessione resti viva, che abbia memoria, e quanto costa.

    python "99_Meta/tools/test_cervello.py"
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import jarvis   # riusa la classe Cervello vera, non una copia


DOMANDE = [
    ("Rispondi solo con la parola: uno",                      "il turno base"),
    ("Che parola ti ho appena chiesto di dire?",              "LA MEMORIA"),
    ("In una frase: a cosa serve questo vault?",              "l'accesso al vault"),
]


def main():
    print("=" * 62)
    print(f"  Modello: {jarvis.MODELLO}   |   Vault: {jarvis.VAULT.name}")
    print("=" * 62)

    t0 = time.time()
    cervello = jarvis.Cervello()
    print(f"\n[avvio processo: {time.time()-t0:.1f}s]  vivo={cervello.vivo()}\n")

    # ATTENZIONE: total_cost_usd e' CUMULATIVO sulla sessione, non il costo del singolo turno.
    # Il costo del turno e' la differenza rispetto al turno precedente.
    precedente = 0.0
    for i, (domanda, cosa) in enumerate(DOMANDE, 1):
        print(f"--- {i}/{len(DOMANDE)} — {cosa}")
        print(f"    tu:     {domanda}")
        r = cervello.chiedi(domanda)
        marginale = r.costo - precedente
        precedente = r.costo
        print(f"    jarvis: {r.testo[:220]}")
        print(f"    tempo {r.secondi:.1f}s | prima parola {r.primo_token:.1f}s | "
              f"costo di QUESTO turno ${marginale:.4f} (sessione ${r.costo:.4f})\n")

    print("=" * 62)
    print(f"  Costo totale della sessione: ${precedente:.4f}")
    print(f"  Sessione: {cervello.session_id}")
    print(f"  Processo ancora vivo: {cervello.vivo()}   <-- deve essere True")
    print("=" * 62)
    print("\n  Confronto: con il metodo vecchio (Opus, processo riavviato ogni volta)")
    print("  il solo primo turno costava $0,0870.\n")
    cervello.chiudi()


if __name__ == "__main__":
    main()
