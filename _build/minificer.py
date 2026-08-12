#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minificerer CSS og JS uden eksterne afhængigheder.
Kaldes fra build.py. Skriver style.min.css og site.min.js ved siden af kilderne.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def minificer_css(kilde):
    t = kilde
    # fjern kommentarer (bevar ikke /*! ... */ da vi ikke bruger dem)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    # whitespace omkring tegnsætning
    t = re.sub(r"\s*([{}:;,>~])\s*", r"\1", t)
    # kombinator + skal have plads i selektorer, men ikke i calc()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r";\}", "}", t)
    # 0.5 → .5
    t = re.sub(r"(:|\s)0\.(\d)", r"\1.\2", t)
    return t.strip()


def minificer_js(kilde):
    # 1) fjern blokkommentarer i ét hug (kilden indeholder ikke "/*" i strenge)
    t = re.sub(r"/\*.*?\*/", "", kilde, flags=re.S)
    # 2) fjern hele linjer der kun er en //-kommentar (aldrig midt i en linje,
    #    så URL'er som https:// og regex-literaler ikke ødelægges)
    linjer = [l for l in t.splitlines() if l.strip() and not l.strip().startswith("//")]
    # 3) fjern indrykning, men behold linjeskift af hensyn til ASI
    return "\n".join(l.strip() for l in linjer)


def koer():
    resultat = []
    par = [
        (ROOT / "assets/css/style.css", ROOT / "assets/css/style.min.css", minificer_css),
        (ROOT / "assets/js/site.js", ROOT / "assets/js/site.min.js", minificer_js),
    ]
    for ind, ud, fn in par:
        if not ind.exists():
            continue
        raa = ind.read_text(encoding="utf-8")
        lille = fn(raa)
        ud.write_text(lille, encoding="utf-8")
        spar = 100 - round(len(lille) / len(raa) * 100)
        resultat.append(f"{ud.name}: {len(raa)//1024} KB → {len(lille)//1024} KB (−{spar} %)")
    return resultat


if __name__ == "__main__":
    for r in koer():
        print(" ", r)
