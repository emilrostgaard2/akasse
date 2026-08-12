#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genererer /assets/img/og-billede.png. Køres én gang; PNG'en committes med i repoet."""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "_build/data/site.json").read_text(encoding="utf-8"))
AKASSER = json.loads((ROOT / "_build/data/akasser.json").read_text(encoding="utf-8"))
AKASSER.sort(key=lambda a: a["pris"])

W, H = 1200, 630
INK = (13, 47, 43)
AKCENT = (13, 79, 71)
SIGNAL = (214, 242, 75)
LYS = (169, 196, 189)

F = "/usr/share/fonts/truetype/google-fonts/"
D = "/usr/share/fonts/truetype/dejavu/"


def font(navn, stoerrelse):
    for sti in (F + navn, D + navn):
        try:
            return ImageFont.truetype(sti, stoerrelse)
        except OSError:
            continue
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), INK)
d = ImageDraw.Draw(img, "RGBA")

# dekorative cirkler
d.ellipse((880, -140, 1400, 380), fill=AKCENT + (150,))
d.ellipse((-120, 400, 340, 860), fill=AKCENT + (110,))

f_kicker = font("Poppins-Medium.ttf", 30)
f_titel = font("Poppins-Bold.ttf", 76)
f_under = font("Poppins-Regular.ttf", 34)
f_pris = font("DejaVuSansMono.ttf", 64)
f_lille = font("Poppins-Medium.ttf", 24)

d.text((80, 78), "AKASSEMATCH.DK", font=f_kicker, fill=SIGNAL)
d.text((80, 170), "Sammenlign alle", font=f_titel, fill=(255, 255, 255))
d.text((80, 262), f"{len(AKASSER)} a-kasser i {SITE['prisaar']}", font=f_titel, fill=(255, 255, 255))
d.text((80, 388), "Dagpengene er ens overalt — prisen er ikke.", font=f_under, fill=LYS)

# prisboks
d.rounded_rectangle((80, 458, 470, 566), radius=18, fill=(255, 255, 255, 26),
                    outline=(255, 255, 255, 46), width=2)
d.text((104, 470), "Billigst pr. måned", font=f_lille, fill=LYS)
d.text((104, 496), f"{AKASSER[0]['pris']} kr.", font=f_pris, fill=SIGNAL)

d.text((510, 470), "Åben for alle fra", font=f_lille, fill=LYS)
tvaer = [a for a in AKASSER if a["type"] == "tvaerfaglig"][0]
d.text((510, 496), f"{tvaer['pris']} kr.", font=f_pris, fill=(255, 255, 255))

# signal-streg
d.rectangle((0, H - 12, W, H), fill=SIGNAL)

ud = ROOT / "assets/img/og-billede.png"
img.save(ud, "PNG", optimize=True)
print(f"✔ {ud} ({ud.stat().st_size // 1024} KB)")
