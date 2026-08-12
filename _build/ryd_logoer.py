#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beskærer luft omkring logoer og normaliserer dem til ens højde.
Køres når der er tilføjet nye logoer:  python3 _build/ryd_logoer.py
Skriver .webp-udgaver ved siden af originalerne.
"""

from pathlib import Path
from PIL import Image, ImageChops

MAPPE = Path(__file__).resolve().parent.parent / "assets/img/logoer"
MAALHOEJDE = 96   # 2x visningshøjde
MAKSBREDDE = 340


def trim(im):
    """Fjerner ensfarvet kant — både transparent og hvid."""
    im = im.convert("RGBA")
    alfa = im.getchannel("A")
    boks = alfa.getbbox() if alfa.getextrema()[0] < 255 else None
    if boks is None:
        rgb = im.convert("RGB")
        baggrund = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
        diff = ImageChops.difference(rgb, baggrund)
        boks = diff.getbbox()
    return im.crop(boks) if boks else im


def main():
    for sti in sorted(MAPPE.iterdir()):
        if sti.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        im = trim(Image.open(sti))

        skala = MAALHOEJDE / im.height
        if im.width * skala > MAKSBREDDE:
            skala = MAKSBREDDE / im.width
        ny = im.resize((max(1, round(im.width * skala)), max(1, round(im.height * skala))),
                       Image.LANCZOS)

        ud = sti.with_suffix(".webp")
        ny.save(ud, "WEBP", quality=92, method=6)
        print(f"  {sti.name:32} → {ud.name:28} {ny.width}×{ny.height}px  {ud.stat().st_size // 1024} KB")

    print("\n✔ Færdig. Husk at bruge .webp-filnavnene i akasser.json.")


if __name__ == "__main__":
    main()
