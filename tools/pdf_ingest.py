#!/usr/bin/env python3
"""
pdf_ingest.py — estrae testo e rende le pagine di un PDF in PNG.
Uso:  python "99_Meta/tools/pdf_ingest.py" "raw/NomeFile.pdf" [scale]

Output:
  - <stem>.txt              : testo per pagina (marcatori ===== PAG n =====)
  - raw/assets/<stem>/pagNN.png : ogni pagina renderizzata (default scale 2.0 ~144dpi)

Dipendenze: pypdf, pypdfium2, pillow  (già installate).
"""
import sys, os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf_ingest.py <file.pdf> [scale]"); sys.exit(1)
    pdf_path = Path(sys.argv[1])
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    if not pdf_path.exists():
        print("File non trovato:", pdf_path); sys.exit(1)

    stem = pdf_path.stem
    # base vault = due livelli sopra 99_Meta/tools/, oppure cwd
    base = Path.cwd()
    assets = base / "raw" / "assets" / stem
    assets.mkdir(parents=True, exist_ok=True)

    # 1) TESTO con pypdf
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    n = len(reader.pages)
    txt_out = pdf_path.with_suffix(".txt")
    with open(txt_out, "w", encoding="utf-8") as f:
        for i, p in enumerate(reader.pages, 1):
            f.write(f"\n===== PAG {i} =====\n")
            f.write((p.extract_text() or "[nessun testo estraibile]") + "\n")
    print(f"[testo]  {n} pagine -> {txt_out}")

    # 2) IMMAGINI con pypdfium2
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    for i in range(len(pdf)):
        img = pdf[i].render(scale=scale).to_pil()
        img.save(assets / f"pag{i+1:02d}.png")
    print(f"[render] {len(pdf)} pagine -> {assets}")
    print("Fatto. Leggi il .txt e apri solo le pagine-immagine che servono.")

if __name__ == "__main__":
    main()
