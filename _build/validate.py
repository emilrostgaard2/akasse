#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validerer det byggede site. Køres efter build.py:
    python3 _build/validate.py
Fejl giver exit-kode 1, så GitHub Actions stopper før upload.
"""

import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
SPRING = {"_build", "assets", ".git", ".github", "node_modules"}

fejl = []
advarsler = []


class TekstUdtraek(HTMLParser):
    """Trækker synlig brødtekst ud, så vi kan tælle ord."""

    def __init__(self):
        super().__init__()
        self.dele = []
        self.spring = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self.spring += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header") and self.spring:
            self.spring -= 1

    def handle_data(self, data):
        if not self.spring:
            self.dele.append(data)

    def tekst(self):
        return re.sub(r"\s+", " ", " ".join(self.dele)).strip()


def find_sider():
    for sti in ROOT.rglob("*.html"):
        if any(d in SPRING for d in sti.relative_to(ROOT).parts):
            continue
        yield sti


def url_for(sti):
    rel = sti.relative_to(ROOT)
    if rel.name == "index.html":
        p = "/" + str(rel.parent).replace("\\", "/")
        return "/" if p in ("/.", "/") else p.rstrip("/") + "/"
    return "/" + str(rel).replace("\\", "/")


def main():
    sider = list(find_sider())
    if not sider:
        fejl.append("Ingen HTML-sider fundet — kørte build.py?")
        return

    kendte = {url_for(s) for s in sider}
    titler = {}
    beskrivelser = {}
    ordantal = {}

    for sti in sider:
        u = url_for(sti)
        h = sti.read_text(encoding="utf-8")

        # --- obligatoriske SEO-felter
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        if not t or not t.group(1).strip():
            fejl.append(f"{u}: mangler <title>")
        else:
            titel = t.group(1).strip()
            if len(titel) > 65:
                advarsler.append(f"{u}: title er {len(titel)} tegn (over 65) — {titel[:55]}…")
            titler.setdefault(titel, []).append(u)

        m = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
        if not m or not m.group(1).strip():
            fejl.append(f"{u}: mangler meta description")
        else:
            b = m.group(1).strip()
            if not (70 <= len(b) <= 175):
                advarsler.append(f"{u}: description er {len(b)} tegn (mål: 70-175)")
            beskrivelser.setdefault(b, []).append(u)

        if not re.search(r'<link rel="canonical"', h):
            fejl.append(f"{u}: mangler canonical")

        h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        if len(h1) != 1:
            fejl.append(f"{u}: har {len(h1)} h1-tags (skal være præcis 1)")

        if not re.search(r'lang="da"', h):
            fejl.append(f"{u}: mangler lang=\"da\"")

        if 'property="og:image"' not in h:
            advarsler.append(f"{u}: mangler og:image")

        # --- billeder uden alt
        for tag in re.findall(r"<img[^>]*>", h):
            if "alt=" not in tag:
                fejl.append(f"{u}: <img> uden alt-attribut — {tag[:70]}")

        # --- interne links
        for href in re.findall(r'href="(/[^"#?]*)"', h):
            if href.startswith("/assets/") or href.endswith((".xml", ".txt", ".webmanifest", ".svg", ".png")):
                if not (ROOT / href.lstrip("/")).exists():
                    fejl.append(f"{u}: dødt link til fil {href}")
                continue
            if href not in kendte:
                fejl.append(f"{u}: dødt internt link → {href}")

        # --- affiliate-links skal være mærket
        for tag in re.findall(r'<a[^>]*data-akasse[^>]*>', h):
            if "sponsored" not in tag or "nofollow" not in tag:
                fejl.append(f"{u}: affiliate-link uden rel=\"sponsored nofollow\"")
            if 'target="_blank"' in tag and "noopener" not in tag:
                fejl.append(f"{u}: target=_blank uden noopener")

        # --- ordantal
        p = TekstUdtraek()
        p.feed(h)
        ordantal[u] = len(p.tekst().split())

    # --- dubletter
    for titel, urls in titler.items():
        if len(urls) > 1:
            fejl.append(f"Dublet-title på {len(urls)} sider: {titel[:50]}… → {', '.join(urls[:3])}")
    for b, urls in beskrivelser.items():
        if len(urls) > 1:
            fejl.append(f"Dublet-description på {len(urls)} sider → {', '.join(urls[:3])}")

    # --- sitemap-dækning
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        fejl.append("sitemap.xml mangler")
    else:
        i_sitemap = set(re.findall(r"<loc>https?://[^/]+(/[^<]*)</loc>", sm.read_text(encoding="utf-8")))
        for u in kendte:
            if u == "/404.html":
                continue
            if u not in i_sitemap:
                advarsler.append(f"{u}: ikke i sitemap.xml")

    if not (ROOT / "robots.txt").exists():
        fejl.append("robots.txt mangler")

    # --- rapport
    print("=" * 62)
    print(f"  Validering: {len(sider)} sider")
    print("=" * 62)

    guides = sorted((u, n) for u, n in ordantal.items() if n >= 1500)
    korte = sorted((n, u) for u, n in ordantal.items() if n < 600 and u != "/404.html")

    print(f"\n  Ordantal: gennemsnit {sum(ordantal.values()) // len(ordantal)} ord/side, "
          f"i alt {sum(ordantal.values()):,} ord".replace(",", "."))
    print(f"  Sider over 2.500 ord: {sum(1 for n in ordantal.values() if n >= 2500)}")
    print(f"  Sider over 1.500 ord: {len(guides)}")
    if korte:
        print("\n  Korteste sider:")
        for n, u in korte[:6]:
            print(f"    {n:>5} ord  {u}")

    if advarsler:
        print(f"\n  ⚠ {len(advarsler)} advarsler:")
        for a in advarsler[:20]:
            print(f"    · {a}")
        if len(advarsler) > 20:
            print(f"    … og {len(advarsler) - 20} flere")

    if fejl:
        print(f"\n  ✖ {len(fejl)} FEJL:")
        for f in fejl[:30]:
            print(f"    · {f}")
        if len(fejl) > 30:
            print(f"    … og {len(fejl) - 30} flere")
        print()
        sys.exit(1)

    print("\n  ✔ Ingen fejl. Klar til upload.\n")


if __name__ == "__main__":
    main()
