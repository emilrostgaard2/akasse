#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AkasseMatch – statisk site-generator.
Kører uden eksterne afhængigheder. Bygges med: python3 _build/build.py
"""

import json
import re
import shutil
import html
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_build" / "data"
CONTENT = ROOT / "_build" / "content"

SITE = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
AKASSER = json.loads((DATA / "akasser.json").read_text(encoding="utf-8"))
S = SITE["satser"]
DOMAENE = SITE["domaene"].rstrip("/")
AAR = SITE["prisaar"]

AKASSER.sort(key=lambda a: a["pris"])
BY_SLUG = {a["slug"]: a for a in AKASSER}
TVAERFAGLIGE = [a for a in AKASSER if a["type"] == "tvaerfaglig"]
FAGSPECIFIKKE = [a for a in AKASSER if a["type"] == "fagspecifik"]
SELVSTAENDIGE = [a for a in AKASSER if a["features"]["selvstaendige"]]

BILLIGST = AKASSER[0]
DYREST = AKASSER[-1]
BILLIGST_ALLE = TVAERFAGLIGE[0]
GNS = round(sum(a["pris"] for a in AKASSER) / len(AKASSER))
SPREDNING = DYREST["pris"] - BILLIGST["pris"]
AARLIG_FORSKEL = SPREDNING * 12

SIDER = []  # (url, prioritet, aendret)


# ---------------------------------------------------------------- hjælpere

def kr(n):
    return f"{n:,.0f}".replace(",", ".")


def kr_dec(n):
    s = f"{n:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return s


def efter_fradrag(pris):
    return round(pris * (1 - S["fradrag_marginalskat"]))


def logo_html(a, klasse="logo"):
    if a.get("logo"):
        return (f'<img class="{klasse}" src="/assets/img/logoer/{a["logo"]}" '
                f'alt="{html.escape(a["navn"])} logo" width="120" height="48" loading="lazy" decoding="async">')
    initialer = "".join(o[0] for o in a["kort"].split()[:2]).upper()
    return f'<span class="{klasse} logo--tekst" aria-hidden="true">{html.escape(initialer)}</span>'


def link_ud(a, tekst=None, klasse="knap knap--gaa"):
    url = a.get("affiliate_url") or a["hjemmeside"]
    tekst = tekst or f"Se pris hos {a['kort']}"
    return (f'<a class="{klasse}" href="{url}" target="_blank" rel="sponsored nofollow noopener" '
            f'data-akasse="{a["slug"]}">{html.escape(tekst)}<span class="knap__pil" aria-hidden="true">→</span></a>')


def ja_nej(v):
    return '<span class="ja">Ja</span>' if v else '<span class="nej">Nej</span>'


def _raa_score(a):
    p = 3.0 * (DYREST["pris"] - a["pris"]) / (DYREST["pris"] - BILLIGST["pris"])
    f = a["features"]
    if f["aaben_for_alle"]:
        p += 0.5
    if f["selvstaendige"]:
        p += 0.4
    if a.get("fagforening_tillaeg") and a["fagforening_tillaeg"] <= 200:
        p += 0.5
    elif f["fagforening"]:
        p += 0.3
    if f["loensikring"]:
        p += 0.2
    if f["gratis_studie"]:
        p += 0.2
    if f["efterloen"]:
        p += 0.2
    return p


_RAA = {a["slug"]: _raa_score(a) for a in AKASSER}
_RAA_MIN, _RAA_MAKS = min(_RAA.values()), max(_RAA.values())


def score(a):
    """AkasseMatch-score 3,0-4,9. Beregnes udelukkende ud fra data — aldrig ud fra samarbejde.
    Skalaen er relativ: markedets stærkeste sætter toppen. Metoden står på
    /redaktionelle-principper/#saadan-beregner-vi-scoren."""
    raa = _RAA[a["slug"]]
    andel = (raa - _RAA_MIN) / (_RAA_MAKS - _RAA_MIN) if _RAA_MAKS > _RAA_MIN else 1
    return round(3.0 + andel * 1.9, 1)


def stjerner(v, vis_tal=True):
    pct = v / 5 * 100
    tal = f'<span class="stjerne-tal">{str(v).replace(".", ",")}</span>' if vis_tal else ""
    return (f'<span class="stjerner" role="img" aria-label="{str(v).replace(".", ",")} ud af 5 point">'
            f'<span class="stjerne-bund">★★★★★</span>'
            f'<span class="stjerne-fyld" style="width:{pct:.0f}%">★★★★★</span></span>{tal}')


def hoejdepunkt(a):
    """Ét kort salgsargument, udledt af data."""
    if a["pris"] == BILLIGST["pris"]:
        return "Landets laveste kontingent"
    if a["pris"] == BILLIGST_ALLE["pris"]:
        return "Billigst med adgang for alle"
    if a.get("fagforening_tillaeg") and a["fagforening_tillaeg"] <= 100:
        return f"Fagforening for kun {a['fagforening_tillaeg']} kr."
    if a["slug"] == "ase":
        return "Stærkest til selvstændige"
    if a["features"]["aaben_for_alle"] and a["features"]["selvstaendige"]:
        return "Åben for alle · tager selvstændige"
    if a.get("medlemmer") and a["medlemmer"] >= 150000:
        return f"{kr(a['medlemmer'])} medlemmer"
    return a["fordele"][0]


def type_label(a):
    return "Åben for alle" if a["type"] == "tvaerfaglig" else "Fagspecifik"


# ---------------------------------------------------------------- komponenter

def tabel(liste, id_="pristabel", vis_filter=True, vis_fagforening=True):
    """Sammenligningsliste — én række pr. a-kasse, bygget som kort frem for bred tabel."""
    filt = ""
    if vis_filter:
        filt = f"""
<div class="liste-styring">
  <div class="filter-gruppe" role="group" aria-label="Filtrér a-kasser">
    <button class="chip chip--aktiv" data-filter="alle">Alle ({len(liste)})</button>
    <button class="chip" data-filter="tvaerfaglig">Åben for alle</button>
    <button class="chip" data-filter="selvstaendig">Selvstændige</button>
    <button class="chip" data-filter="fagforening">Med fagforening</button>
  </div>
  <div class="styring-hoejre">
    <label class="soeg">
      <span class="soeg__ikon" aria-hidden="true">⌕</span>
      <input type="search" placeholder="Søg a-kasse eller fag …" data-soeg="{id_}" aria-label="Søg efter a-kasse eller fag">
    </label>
    <label class="sorter">
      <span class="visuelt-skjult">Sortér efter</span>
      <select data-sorter>
        <option value="pris">Laveste pris</option>
        <option value="score">Højeste score</option>
      </select>
    </label>
  </div>
</div>"""

    raekker = []
    for i, a in enumerate(liste, 1):
        ff = (f'{a["fagforening_tillaeg"]} kr./md.' if a.get("fagforening_tillaeg")
              else ('Inkluderet' if a["features"]["fagforening"] else 'Tilbydes ikke'))
        badge = f'<span class="badge">{html.escape(a["badge"])}</span>' if a.get("badge") else ""
        s = score(a)
        knap_tekst = "Bliv medlem" if a.get("partner") else "Se hos udbyder"
        medl = kr(a["medlemmer"]) if a.get("medlemmer") else "—"
        raekker.append(f"""
  <li class="ak-raekke" data-raekke
      data-type="{a['type']}" data-selvstaendig="{str(a['features']['selvstaendige']).lower()}"
      data-fagforening="{str(a['features']['fagforening']).lower()}"
      data-navn="{html.escape(a['navn'].lower())} {html.escape(a['maalgruppe'].lower())}"
      data-pris="{a['pris']}" data-score="{s}">
    <span class="ak-nr" aria-hidden="true">{i}</span>
    <div class="ak-brand">
      <span class="ak-logo">{logo_html(a, 'logo')}</span>
      <span class="ak-score">{stjerner(s)}</span>
      <a class="ak-anmeldelse" href="/a-kasser/{a['slug']}/">Læs anmeldelse</a>
    </div>
    <div class="ak-info">
      <h3 class="ak-navn"><a href="/a-kasser/{a['slug']}/">{html.escape(a['kort'])}</a>{badge}</h3>
      <p class="ak-maal">{html.escape(a['maalgruppe'])}</p>
      <dl class="ak-fakta">
        <div><dt>Adgang</dt><dd>{type_label(a)}</dd></div>
        <div><dt>Fagforening</dt><dd>{ff}</dd></div>
        <div><dt>Selvstændige</dt><dd>{'Ja' if a['features']['selvstaendige'] else 'Nej'}</dd></div>
        <div><dt>Medlemmer</dt><dd>{medl}</dd></div>
      </dl>
    </div>
    <div class="ak-handling">
      <div class="ak-prisboks">
        <span class="ak-prislabel">A-kasse pris</span>
        <span class="ak-pristal">{a['pris']}<small>kr./md.</small></span>
        <span class="ak-prisnet">{kr(efter_fradrag(a['pris']))} kr. efter fradrag</span>
      </div>
      {link_ud(a, knap_tekst, "knap knap--liste")}
    </div>
  </li>""")

    return f"""
<div class="liste-blok" id="{id_}" data-liste>
{filt}
<ol class="ak-liste">{''.join(raekker)}</ol>
<p class="tomt-resultat" hidden>Ingen a-kasser matcher din søgning. <button type="button" class="link-knap" data-nulstil>Nulstil filtre</button></p>
<p class="liste-note">Priser er kontingent for a-kassen alene pr. måned i {AAR}. «Efter fradrag» er den reelle udgift ved en marginalskat på ca. 31 %. Scoren beregnes ud fra pris, adgang og ydelser — <a href="/redaktionelle-principper/#saadan-beregner-vi-scoren">se metoden</a>. Sidst kontrolleret {SITE['opdateret']}. <a href="/saadan-tjener-vi-penge/">Sådan tjener vi penge</a>.</p>
</div>"""


def linjal():
    """Signaturelementet: kontingent-linjalen."""
    lav, hoej = BILLIGST["pris"], DYREST["pris"]
    spand = hoej - lav
    raekker = []
    for a in AKASSER:
        pct = (a["pris"] - lav) / spand * 100
        klasse = "linjal-raekke"
        if a["pris"] == lav:
            klasse += " er-billigst"
        raekker.append(f"""
    <li class="{klasse}" style="--pct:{pct:.1f}%">
      <a href="/a-kasser/{a['slug']}/">
        <span class="linjal-navn">{html.escape(a['kort'])}</span>
        <span class="linjal-spor"><span class="linjal-bar"></span><span class="linjal-prik"></span></span>
        <span class="linjal-pris">{a['pris']}<small>kr.</small></span>
      </a>
    </li>""")
    ticks = "".join(
        f'<span class="tick" style="--pct:{(v - lav) / spand * 100:.1f}%"><i></i>{v}</span>'
        for v in range(480, 581, 20) if lav <= v <= hoej)
    return f"""
<figure class="linjal" data-animeret>
  <figcaption class="linjal-titel">Kontingent pr. måned i {AAR} — alle {len(AKASSER)} a-kasser på samme skala</figcaption>
  <div class="linjal-akse" aria-hidden="true">{ticks}</div>
  <ol class="linjal-liste">{''.join(raekker)}</ol>
  <p class="linjal-fod">Fra <strong>{BILLIGST['pris']} kr.</strong> ({html.escape(BILLIGST['kort'])}) til <strong>{DYREST['pris']} kr.</strong> ({html.escape(DYREST['kort'])}). Forskel: <strong>{SPREDNING} kr./md.</strong> = {kr(AARLIG_FORSKEL)} kr. om året.</p>
</figure>"""


ANBEFALINGER = [
    ("det-faglige-hus", "Billigst for alle",
     "Landets laveste kontingent blandt de a-kasser, alle kan blive medlem af — og fagforening for kun 69 kr. oveni."),
    ("min-akasse", "Bedst uden fagforening",
     "En ren a-kasse uden fagforeningsbinding. Relevant hvis du allerede er organiseret et andet sted, eller bevidst fravælger fagforening."),
    ("ase", "Bedst til selvstændige",
     "Rådgivere der udelukkende arbejder med virksomhedsejere. Merprisen er tjent ind på én korrekt håndteret ophørssag."),
]


def kort_top(n=3, liste=None):
    if liste is not None:
        valgte = [(a, None, None) for a in liste[:n]]
    else:
        valgte = [(BY_SLUG[s], r, b) for s, r, b in ANBEFALINGER[:n]]
    kort = []
    for i, (a, rolle, begrundelse) in enumerate(valgte):
        frem = ' kort--frem' if i == 0 else ''
        punkter = "".join(f"<li>{html.escape(p)}</li>" for p in a["fordele"][:3])
        s = score(a)
        knap_tekst = "Meld dig ind" if a.get("partner") else "Se hos udbyder"
        kort.append(f"""
  <article class="kort{frem}">
    {f'<span class="kort-flag">{html.escape(rolle)}</span>' if rolle else ''}
    <div class="kort-logo">{logo_html(a)}</div>
    <h3 class="kort-navn"><a href="/a-kasser/{a['slug']}/">{html.escape(a['kort'])}</a></h3>
    <p class="kort-score">{stjerner(s)}<span class="kort-score-tekst">AkasseMatch-score</span></p>
    <p class="kort-pris"><span class="tal">{a['pris']}</span> kr./md.</p>
    <p class="kort-net">{kr(efter_fradrag(a['pris']))} kr. efter skattefradrag · {kr(a['pris'] * 12)} kr./år</p>
    {f'<p class="kort-hvorfor">{html.escape(begrundelse)}</p>' if begrundelse else ''}
    <ul class="kort-punkter">{punkter}</ul>
    {link_ud(a, knap_tekst)}
    <a class="kort-laes" href="/a-kasser/{a['slug']}/">Læs vores gennemgang af {html.escape(a['kort'])}</a>
  </article>""")
    return f'<div class="kort-grid">{"".join(kort)}</div>'


def satstabel():
    r = [
        ("Højeste dagpengesats, fuldtidsforsikret", S["maks_fuldtid"], "100 %"),
        ("Højeste dagpengesats, deltidsforsikret", S["maks_deltid"], "100 % (deltid)"),
        ("Med beskæftigelsestillæg, fuldtid (første 3 mdr.)", S["tillaeg_fuldtid"], "118,86 %"),
        ("Med beskæftigelsestillæg, deltid (første 3 mdr.)", S["tillaeg_deltid"], "118,86 % (deltid)"),
        ("Dimittend med forsørgerpligt", S["dimittend_forsoerger"], "82 %"),
        ("Dimittend uden forsørgerpligt (første 3 mdr.)", S["dimittend_ikke_forsoerger"], "71,5 %"),
        ("Dimittend uden forsørgerpligt, over 30 år (herefter)", S["dimittend_over30_efter"], "62,11 %"),
        ("Dimittend uden forsørgerpligt, under 30 år (herefter)", S["dimittend_under30_efter"], "49,17 %"),
    ]
    raekker = "".join(
        f'<tr><td>{n}</td><td class="tal-celle">{kr(v)} kr.</td><td class="tal-celle">{p}</td></tr>' for n, v, p in r)
    return f"""
<div class="tabel-wrap" role="region" aria-label="Dagpengesatser {AAR}" tabindex="0">
<table class="data data--enkel">
  <caption>Dagpengesatser {AAR} pr. måned før skat</caption>
  <thead><tr><th scope="col">Sats</th><th scope="col">Kr. pr. måned</th><th scope="col">Andel af maks.</th></tr></thead>
  <tbody>{raekker}</tbody>
</table>
</div>
<p class="tabel-note">Satserne er ens i alle a-kasser — de er fastsat ved lov. Beløbene er før skat og reguleres hvert år pr. 1. januar. Kilde: Beskæftigelsesministeriets satsvejledning for {AAR}.</p>"""


def fagforeningstabel():
    liste = [a for a in AKASSER if a.get("fagforening_tillaeg")]
    liste.sort(key=lambda a: a["pris"] + a["fagforening_tillaeg"])
    raekker = "".join(
        f'<tr><td><a href="/a-kasser/{a["slug"]}/">{html.escape(a["kort"])}</a></td>'
        f'<td class="tal-celle">{a["pris"]} kr.</td>'
        f'<td class="tal-celle">{a["fagforening_tillaeg"]} kr.</td>'
        f'<td class="tal-celle"><strong>{a["pris"] + a["fagforening_tillaeg"]} kr.</strong></td>'
        f'<td class="tal-celle">{kr((a["pris"] + a["fagforening_tillaeg"]) * 12)} kr.</td></tr>'
        for a in liste)
    return f"""
<div class="tabel-wrap" role="region" aria-label="A-kasse og fagforening samlet" tabindex="0">
<table class="data data--enkel">
  <caption>Hvad koster a-kasse + fagforening samlet i {AAR}?</caption>
  <thead><tr><th scope="col">Udbyder</th><th scope="col">A-kasse</th><th scope="col">Fagforening</th><th scope="col">Samlet pr. md.</th><th scope="col">Samlet pr. år</th></tr></thead>
  <tbody>{raekker}</tbody>
</table>
</div>
<p class="tabel-note">Fagforeningskontingent er ofte differentieret efter faggruppe, region og indkomst. Beløbene her er vejledende udgangspunkter — tjek den konkrete pris hos udbyderen, før du melder dig ind.</p>"""


def selvstaendigtabel():
    liste = sorted(SELVSTAENDIGE, key=lambda a: a["pris"])
    raekker = "".join(
        f'<tr><td><a href="/a-kasser/{a["slug"]}/">{html.escape(a["kort"])}</a></td>'
        f'<td class="tal-celle">{a["pris"]} kr.</td>'
        f'<td>{html.escape(a["maalgruppe"])}</td>'
        f'<td>{type_label(a)}</td>'
        f'<td class="c-cta">{link_ud(a, "Se pris", "knap knap--lille")}</td></tr>'
        for a in liste)
    return f"""
<div class="tabel-wrap" role="region" aria-label="A-kasser der optager selvstændige" tabindex="0">
<table class="data data--enkel">
  <caption>A-kasser der optager selvstændige og freelancere ({AAR})</caption>
  <thead><tr><th scope="col">A-kasse</th><th scope="col">Pris/md.</th><th scope="col">Målgruppe</th><th scope="col">Adgang</th><th scope="col"><span class="visuelt-skjult">Link</span></th></tr></thead>
  <tbody>{raekker}</tbody>
</table>
</div>"""


def beregner():
    return f"""
<div class="beregner" data-beregner>
  <div class="beregner-hoved">
    <h3 class="beregner-titel">Beregn dine dagpenge og din reelle a-kasseudgift</h3>
    <p class="beregner-intro">Tallene opdateres, mens du skriver. Beregningen bruger {AAR}-satser og er vejledende.</p>
  </div>
  <div class="beregner-krop">
    <div class="beregner-felter">
      <label class="felt">
        <span class="felt-navn">Din månedsløn før skat</span>
        <span class="felt-input"><input type="number" id="b-loen" value="38000" min="0" step="500" inputmode="numeric"><span class="felt-enhed">kr.</span></span>
      </label>
      <label class="felt">
        <span class="felt-navn">Forsikring</span>
        <span class="felt-input"><select id="b-type"><option value="fuld">Fuldtidsforsikret</option><option value="deltid">Deltidsforsikret</option></select></span>
      </label>
      <label class="felt">
        <span class="felt-navn">Din situation</span>
        <span class="felt-input"><select id="b-situation">
          <option value="normal">Almindelig lønmodtager</option>
          <option value="tillaeg">Har ret til beskæftigelsestillæg</option>
          <option value="dim-f">Nyuddannet med forsørgerpligt</option>
          <option value="dim-u">Nyuddannet uden forsørgerpligt</option>
        </select></span>
      </label>
      <label class="felt">
        <span class="felt-navn">A-kassens kontingent</span>
        <span class="felt-input"><input type="number" id="b-kontingent" value="{BILLIGST_ALLE['pris']}" min="0" step="1" inputmode="numeric"><span class="felt-enhed">kr./md.</span></span>
      </label>
    </div>
    <div class="beregner-resultat" aria-live="polite">
      <p class="res-label">Dine dagpenge pr. måned før skat</p>
      <p class="res-tal"><span id="b-sats">0</span> <small>kr.</small></p>
      <ul class="res-liste">
        <li><span>Dækning af din nuværende løn</span><strong id="b-daekning">0 %</strong></li>
        <li><span>A-kasse efter skattefradrag</span><strong id="b-net">0 kr./md.</strong></li>
        <li><span>Kontingent pr. år efter fradrag</span><strong id="b-aar">0 kr.</strong></li>
        <li><span>Dagpenge i forhold til årets kontingent</span><strong id="b-forhold">0×</strong></li>
      </ul>
      <p class="res-note" id="b-note"></p>
    </div>
  </div>
  <p class="beregner-fod">Beregneren viser et estimat. Din endelige sats fastsættes af din a-kasse ud fra indberettede lønoplysninger i indkomstregistret. Maksimal sats i {AAR}: {kr(S['maks_fuldtid'])} kr. (fuldtid) og {kr(S['maks_deltid'])} kr. (deltid).</p>
</div>"""


def cta_box(titel=None, tekst=None):
    titel = titel or "Klar til at vælge?"
    tekst = tekst or (f"Den billigste a-kasse, alle kan blive medlem af, er {BILLIGST_ALLE['kort']} til "
                      f"{BILLIGST_ALLE['pris']} kr./md. Er du sundhedsfaglig eller akademiker, kan du komme endnu lavere ned.")
    return f"""
<aside class="cta-box">
  <div class="cta-tekst">
    <h3>{html.escape(titel)}</h3>
    <p>{tekst}</p>
  </div>
  <div class="cta-handling">
    {link_ud(BILLIGST_ALLE, f"Gå til {BILLIGST_ALLE['kort']}")}
    <a class="knap knap--sekundaer" href="/sammenlign/">Sammenlign alle {len(AKASSER)}</a>
  </div>
</aside>"""


def faktaboks():
    return f"""
<div class="fakta">
  <h2 class="fakta-titel">Kort fortalt</h2>
  <ul class="fakta-liste">
    <li><strong>{BILLIGST['pris']} kr./md.</strong> er landets laveste kontingent ({html.escape(BILLIGST['kort'])}).</li>
    <li><strong>{BILLIGST_ALLE['pris']} kr./md.</strong> er billigst blandt dem, alle kan blive medlem af ({html.escape(BILLIGST_ALLE['kort'])}).</li>
    <li><strong>{kr(AARLIG_FORSKEL)} kr.</strong> er forskellen på billigste og dyreste a-kasse over et år.</li>
    <li><strong>{kr(S['maks_fuldtid'])} kr./md.</strong> er den højeste dagpengesats i {AAR} — den er ens i alle a-kasser.</li>
    <li><strong>0 kr.</strong> koster det at skifte a-kasse, og du beholder din anciennitet.</li>
  </ul>
</div>"""


def akasse_liste_grid():
    grupper = [("Åben for alle", TVAERFAGLIGE), ("Fagspecifikke a-kasser", FAGSPECIFIKKE)]
    ud = []
    for titel, liste in grupper:
        elementer = "".join(f"""
    <li class="gitter-kort">
      <a href="/a-kasser/{a['slug']}/">
        <span class="gitter-logo">{logo_html(a, 'logo logo--lille')}</span>
        <span class="gitter-navn">{html.escape(a['kort'])}</span>
        <span class="gitter-pris">{a['pris']} kr./md.</span>
        <span class="gitter-maal">{html.escape(a['maalgruppe'])}</span>
      </a>
    </li>""" for a in liste)
        ud.append(f'<h2 id="{"aaben-for-alle" if "alle" in titel else "fagspecifikke"}">{titel}</h2>'
                  f'<ul class="gitter">{elementer}</ul>')
    return "".join(ud)


SHORTCODES = {
    "tabel:alle": lambda: tabel(AKASSER, "pristabel"),
    "tabel:tvaerfaglige": lambda: tabel(TVAERFAGLIGE, "tvaerfagligtabel", vis_filter=False),
    "tabel:top5": lambda: tabel(AKASSER[:5], "top5tabel", vis_filter=False),
    "tabel:fagforening": fagforeningstabel,
    "tabel:selvstaendige": selvstaendigtabel,
    "tabel:satser": satstabel,
    "linjal": linjal,
    "kort:top3": lambda: kort_top(3),
    "kort:selvstaendige": lambda: kort_top(3, SELVSTAENDIGE),
    "beregner": beregner,
    "cta": lambda: cta_box(),
    "fakta": faktaboks,
    "akasseliste": akasse_liste_grid,
}


def erstat_shortcodes(tekst):
    def sub(m):
        navn = m.group(1).strip()
        if navn in SHORTCODES:
            return SHORTCODES[navn]()
        raise SystemExit(f"FEJL: ukendt shortcode {{{{{navn}}}}}")
    return re.sub(r"\{\{([a-z0-9:_]+)\}\}", sub, tekst)


def erstat_variabler(tekst):
    v = {
        "aar": str(AAR),
        "antal": str(len(AKASSER)),
        "billigst": BILLIGST["kort"],
        "billigst_pris": str(BILLIGST["pris"]),
        "billigst_alle": BILLIGST_ALLE["kort"],
        "billigst_alle_pris": str(BILLIGST_ALLE["pris"]),
        "dyrest": DYREST["kort"],
        "dyrest_pris": str(DYREST["pris"]),
        "gns": str(GNS),
        "spredning": str(SPREDNING),
        "aarlig_forskel": kr(AARLIG_FORSKEL),
        "maks_sats": kr(S["maks_fuldtid"]),
        "maks_deltid": kr(S["maks_deltid"]),
        "tillaeg": kr(S["tillaeg_fuldtid"]),
        "dim_f": kr(S["dimittend_forsoerger"]),
        "dim_u": kr(S["dimittend_ikke_forsoerger"]),
        "statsbidrag": str(S["statsbidrag_atp"]),
        "efterloen": str(S["efterloensbidrag"]),
        "indkomstkrav": kr(S["indkomstkrav_3aar"]),
        "loenkrav": kr(S["loenkrav_maks_sats"]),
        "maks_medregnet": kr(S.get("maks_medregnet_md", 23886)),
        "timekrav": kr(S.get("timekrav_genoptjening", 1924)),
        "opdateret": SITE["opdateret"],
    }
    for k, val in v.items():
        tekst = tekst.replace("[[" + k + "]]", val)
    return tekst


# ---------------------------------------------------------------- layout

INTERNE_LINKS = [
    ("billigste a-kasse", "/billigste-a-kasse/"),
    ("billigste a-kasser", "/billigste-a-kasse/"),
    ("skifte a-kasse", "/skift-a-kasse/"),
    ("skifter a-kasse", "/skift-a-kasse/"),
    ("dagpengesatsen", "/dagpengesatser/"),
    ("dagpengesatser", "/dagpengesatser/"),
    ("maksimalsatsen", "/dagpengesatser/"),
    ("beskæftigelsestillæg", "/dagpengesatser/"),
    ("dimittendsats", "/dimittend-dagpenge/"),
    ("nyuddannet", "/dimittend-dagpenge/"),
    ("gratis studiemedlemskab", "/a-kasse-studerende/"),
    ("studiemedlem", "/a-kasse-studerende/"),
    ("selvstændig", "/a-kasse-selvstaendig/"),
    ("freelancer", "/a-kasse-selvstaendig/"),
    ("kontingentet", "/a-kasse-priser/"),
    ("Det Faglige Hus", "/a-kasser/det-faglige-hus/"),
    ("Min A-kasse", "/a-kasser/min-akasse/"),
    ("Akademikernes A-kasse", "/a-kasser/akademikernes/"),
    ("Krifa", "/a-kasser/krifa/"),
    ("Ase", "/a-kasser/ase/"),
    ("dagpengeberegner", "/dagpengeberegner/"),
]

MAKS_AUTOLINKS = 7


def auto_link(krop, egen_url):
    """Linker første forekomst af udvalgte begreber i brødteksten.
    Springer over: eksisterende links, overskrifter, tabeller, knapper og FAQ-spørgsmål."""
    dele = re.split(r"(<[^>]+>)", krop)
    forbudt = 0
    brugt = set()
    antal = 0
    aabne = []

    for i, del_ in enumerate(dele):
        if del_.startswith("<"):
            m = re.match(r"</?\s*([a-zA-Z0-9]+)", del_)
            if m:
                tag = m.group(1).lower()
                if tag in ("a", "h1", "h2", "h3", "h4", "table", "summary", "button", "figcaption", "nav", "script", "style", "caption"):
                    if del_.startswith("</"):
                        if aabne and aabne[-1] == tag:
                            aabne.pop()
                            forbudt = max(0, forbudt - 1)
                    elif not del_.rstrip().endswith("/>"):
                        aabne.append(tag)
                        forbudt += 1
            continue

        if forbudt or antal >= MAKS_AUTOLINKS or not del_.strip():
            continue

        for begreb, url in INTERNE_LINKS:
            if antal >= MAKS_AUTOLINKS:
                break
            if url == egen_url or url in brugt:
                continue
            m = re.search(r"(?<![\w-])(" + re.escape(begreb) + r")(?![\w-])", del_)
            if not m:
                continue
            del_ = del_[:m.start()] + f'<a href="{url}">{m.group(1)}</a>' + del_[m.end():]
            brugt.add(url)
            antal += 1
        dele[i] = del_

    return "".join(dele)


def relaterede(egen_url, antal=4):
    alle = [
        ("/billigste-a-kasse/", "Billigste a-kasse " + str(AAR), "Hele prisoversigten og hvornår billigst faktisk er bedst"),
        ("/a-kasse-priser/", f"A-kasse priser {AAR}", "Hvad kontingentet består af, og hvorfor priserne steg"),
        ("/skift-a-kasse/", "Skift a-kasse", "Gratis, tager fem minutter, anciennitet følger med"),
        ("/dagpengesatser/", f"Dagpengesatser {AAR}", f"Højeste sats er {kr(S['maks_fuldtid'])} kr./md."),
        ("/dimittend-dagpenge/", "Dagpenge som nyuddannet", "Dimittendsats, 14-dages fristen og karensmåneden"),
        ("/a-kasse-selvstaendig/", "A-kasse for selvstændige", "Reglerne ved eget CVR-nummer"),
        ("/a-kasse-studerende/", "A-kasse som studerende", "Gratis medlemskab og hvad det er værd"),
        ("/dagpengeberegner/", "Dagpengeberegner", "Beregn din sats og dækningsgrad"),
        ("/sammenlign/", f"Sammenlign alle {len(AKASSER)}", "Filtrér på pris, adgang og selvstændige"),
    ]
    valg = [x for x in alle if x[0] != egen_url][:antal]
    kort = "".join(
        f'<a class="rel-kort" href="{u}"><span class="rel-titel">{html.escape(t)}</span>'
        f'<span class="rel-tekst">{html.escape(b)}</span></a>' for u, t, b in valg)
    return f"""
<aside class="relaterede">
  <h2 class="rel-overskrift">Læs også</h2>
  <div class="rel-grid">{kort}</div>
</aside>"""


def slugify(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    for a, b in [("æ", "ae"), ("ø", "oe"), ("å", "aa"), ("é", "e"), ("&", "og")]:
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "afsnit"


def tilfoej_overskrift_id(krop):
    def sub(m):
        tag, attrs, indhold = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        return f'<{tag}{attrs} id="{slugify(indhold)}">{indhold}</{tag}>'
    return re.sub(r"<(h2|h3)([^>]*)>(.*?)</\1>", sub, krop, flags=re.S)


def byg_toc(krop):
    fund = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', krop, flags=re.S)
    if len(fund) < 3:
        return ""
    punkter = "".join(f'<li><a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a></li>' for i, t in fund)
    return f"""
<details class="toc">
  <summary>Indhold på siden <span class="toc-antal">{len(fund)} afsnit</span></summary>
  <ol class="toc-liste">{punkter}</ol>
</details>"""


def faq_jsonld(krop):
    par = re.findall(r'<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>', krop, flags=re.S)
    if not par:
        return "", krop
    poster = []
    for sp, sv in par:
        sp_ren = re.sub(r"<[^>]+>", "", sp).strip()
        sv_ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sv)).strip()
        poster.append({
            "@type": "Question",
            "name": sp_ren,
            "acceptedAnswer": {"@type": "Answer", "text": sv_ren},
        })
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": poster}
    return json.dumps(data, ensure_ascii=False), krop


def forfatterboks():
    return f"""
<aside class="forfatter" itemscope itemtype="https://schema.org/Person">
  <img class="forfatter-foto" src="/assets/img/emil-rostgaard.webp" alt="Emil Rostgaard, redaktør på AkasseMatch" width="96" height="96" loading="lazy" decoding="async" itemprop="image">
  <div class="forfatter-tekst">
    <p class="forfatter-label">Skrevet og faktatjekket af</p>
    <p class="forfatter-navn"><a href="/om/emil-rostgaard/" itemprop="url"><span itemprop="name">Emil Rostgaard</span></a></p>
    <p class="forfatter-rolle" itemprop="jobTitle">Ansvarshavende redaktør, AkasseMatch</p>
    <p class="forfatter-bio">Har arbejdet med sammenligning af danske forsikrings- og medlemsprodukter siden 2018 og gennemgår kontingenter og satser fra a-kassernes egne prislister og Beskæftigelsesministeriets satsvejledning.</p>
    <p class="forfatter-links"><a href="https://www.linkedin.com/in/emil-rostgaard-702809195/" rel="me noopener" target="_blank" itemprop="sameAs">LinkedIn</a> · <a href="/om/emil-rostgaard/">Profil</a> · <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
  </div>
</aside>"""


def brodkrumme(sti):
    """sti: liste af (titel, url|None)"""
    dele = ['<li><a href="/">Forside</a></li>']
    poster = [{"@type": "ListItem", "position": 1, "name": "Forside", "item": DOMAENE + "/"}]
    for i, (t, u) in enumerate(sti, 2):
        if u:
            dele.append(f'<li><a href="{u}">{html.escape(t)}</a></li>')
            poster.append({"@type": "ListItem", "position": i, "name": t, "item": DOMAENE + u})
        else:
            dele.append(f'<li><span aria-current="page">{html.escape(t)}</span></li>')
            poster.append({"@type": "ListItem", "position": i, "name": t})
    nav = f'<nav class="brodkrumme" aria-label="Brødkrumme"><ol>{"".join(dele)}</ol></nav>'
    ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": poster},
                    ensure_ascii=False)
    return nav, ld


def nav_html(aktiv):
    ud = []
    for i, n in enumerate(SITE["nav"]):
        aria = ' aria-current="page"' if n["url"] == aktiv else ''
        if n.get("boern"):
            aktiv_i_gruppe = aktiv in [b["url"] for b in n["boern"]] or n["url"] == aktiv
            punkter = "".join(
                f'<li><a href="{b["url"]}"><span class="drop-titel">{html.escape(b["titel"])}</span>'
                f'<span class="drop-tekst">{html.escape(b.get("tekst", ""))}</span></a></li>'
                for b in n["boern"])
            ud.append(f"""<li class="har-drop" data-drop>
        <button type="button" class="nav-knap{' er-aktiv' if aktiv_i_gruppe else ''}" aria-expanded="false" aria-controls="drop-{i}">
          {html.escape(n['titel'])}<span class="drop-pil" aria-hidden="true">▾</span>
        </button>
        <div class="drop" id="drop-{i}">
          <ul>{punkter}</ul>
          <a class="drop-alle" href="{n['url']}">Se alle guides →</a>
        </div>
      </li>""")
        else:
            ud.append(f'<li><a href="{n["url"]}"{aria}>{html.escape(n["titel"])}</a></li>')
    return "".join(ud)


def side(url, titel, beskrivelse, krop, *, jsonld=None, aktiv=None, klasse="",
         hero=None, opdateret=None, prioritet="0.7", noindex=False):
    """Skriver en HTML-side til disk."""
    kanonisk = DOMAENE + url
    jsonld = [j for j in (jsonld or []) if j]
    ld_html = "".join(f'<script type="application/ld+json">{j}</script>' for j in jsonld)
    aar_nu = date.today().year

    footer_kolonner = f"""
      <div class="fod-kol">
        <h2 class="fod-titel">Sammenlign</h2>
        <ul>
          <li><a href="/sammenlign/">Alle a-kasser og priser</a></li>
          <li><a href="/billigste-a-kasse/">Billigste a-kasse {AAR}</a></li>
          <li><a href="/a-kasse-priser/">A-kasse priser {AAR}</a></li>
          <li><a href="/a-kasser/">Oversigt over a-kasser</a></li>
          <li><a href="/dagpengeberegner/">Dagpengeberegner</a></li>
        </ul>
      </div>
      <div class="fod-kol">
        <h2 class="fod-titel">Guides</h2>
        <ul>
          <li><a href="/skift-a-kasse/">Skift a-kasse</a></li>
          <li><a href="/dagpengesatser/">Dagpengesatser {AAR}</a></li>
          <li><a href="/dimittend-dagpenge/">Dagpenge som nyuddannet</a></li>
          <li><a href="/a-kasse-selvstaendig/">A-kasse for selvstændige</a></li>
          <li><a href="/a-kasse-studerende/">A-kasse som studerende</a></li>
        </ul>
      </div>
      <div class="fod-kol">
        <h2 class="fod-titel">Om AkasseMatch</h2>
        <ul>
          <li><a href="/om-os/">Om os</a></li>
          <li><a href="/om/emil-rostgaard/">Redaktionen</a></li>
          <li><a href="/redaktionelle-principper/">Redaktionelle principper</a></li>
          <li><a href="/saadan-tjener-vi-penge/">Sådan tjener vi penge</a></li>
          <li><a href="/kontakt/">Kontakt</a></li>
        </ul>
      </div>"""

    doc = f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<meta name="description" content="{html.escape(beskrivelse)}">
<link rel="canonical" href="{kanonisk}">
{'<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">'}
<meta property="og:type" content="{'article' if url not in ('/',) else 'website'}">
<meta property="og:site_name" content="{SITE['navn']}">
<meta property="og:locale" content="da_DK">
<meta property="og:title" content="{html.escape(titel)}">
<meta property="og:description" content="{html.escape(beskrivelse)}">
<meta property="og:url" content="{kanonisk}">
<meta property="og:image" content="{DOMAENE}/assets/img/og-billede.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Emil Rostgaard">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/favicon.svg">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0d4f47">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<link rel="stylesheet" href="/assets/css/style.css?v=6">
{ld_html}
</head>
<body class="{klasse}">
<a class="spring" href="#indhold">Spring til indhold</a>
<header class="site-hoved" data-hoved>
  <div class="ramme hoved-inder">
    <a class="brand" href="/" aria-label="{SITE['navn']} forside">
      <svg class="brand-logo" width="34" height="34" viewBox="0 0 34 34" aria-hidden="true" focusable="false">
        <rect width="34" height="34" rx="9" fill="var(--akcent)"/>
        <path d="M8 23.5 13.4 10h3.1l5.4 13.5h-3.2l-1-2.8h-5.6l-1 2.8H8Zm5-5.4h3.8L15 12.9l-2 5.2Z" fill="#fff"/>
        <circle cx="24.5" cy="20.5" r="3.2" fill="var(--signal)"/>
      </svg>
      <span class="brand-navn">Akasse<span class="brand-navn-2">Match</span></span>
    </a>
    <button class="menu-knap" type="button" aria-expanded="false" aria-controls="hovedmenu" data-menu>
      <span class="menu-streger" aria-hidden="true"><i></i><i></i><i></i></span>
      <span class="menu-tekst">Menu</span>
    </button>
    <nav class="hoved-nav" id="hovedmenu" aria-label="Hovedmenu">
      <ul>{nav_html(aktiv)}</ul>
    </nav>
    <a class="hoved-cta" href="/sammenlign/">Find din a-kasse</a>
  </div>
</header>
{hero or ''}
<main id="indhold">
{krop}
</main>
<footer class="site-fod">
  <div class="ramme">
    <div class="fod-top">
      <div class="fod-kol fod-kol--brand">
        <p class="fod-brand">Akasse<span>Match</span></p>
        <p class="fod-slogan">{html.escape(SITE['slogan'])}.</p>
        <p class="fod-note">Uafhængig sammenligning af alle {len(AKASSER)} danske a-kasser. Vi er ikke en a-kasse og sælger ikke medlemskaber.</p>
      </div>
      {footer_kolonner}
    </div>
    <div class="fod-bund">
      <p>© {aar_nu} {SITE['navn']}. Priser kontrolleret {SITE['opdateret']}.</p>
      <ul class="fod-links">
        {''.join(f'<li><a href="{l["url"]}">{html.escape(l["titel"])}</a></li>' for l in SITE['footer_links'])}
      </ul>
    </div>
    <p class="fod-disclaimer">AkasseMatch indeholder annoncelinks. Klikker du videre til en a-kasse, kan vi modtage en kommission. Det påvirker ikke priserne for dig og ikke rækkefølgen i vores tabeller, som altid sorteres efter pris. Indholdet er generel information og erstatter ikke individuel rådgivning fra din a-kasse.</p>
  </div>
</footer>
<script src="/assets/js/site.js?v=6" defer></script>
</body>
</html>"""

    maalsti = ROOT / (url.strip("/") or "index")
    if url == "/":
        fil = ROOT / "index.html"
    elif url.endswith(".html"):
        fil = ROOT / url.lstrip("/")
    else:
        maalsti.mkdir(parents=True, exist_ok=True)
        fil = maalsti / "index.html"
    fil.write_text(doc, encoding="utf-8")
    if not noindex:
        SIDER.append((url, prioritet, opdateret or SITE["opdateret"]))
    return fil


def artikel_jsonld(url, titel, beskrivelse, opdateret):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": titel[:110],
        "description": beskrivelse,
        "inLanguage": "da-DK",
        "datePublished": "2026-01-15",
        "dateModified": opdateret or SITE["opdateret"],
        "mainEntityOfPage": {"@type": "WebPage", "@id": DOMAENE + url},
        "author": {
            "@type": "Person",
            "name": "Emil Rostgaard",
            "url": DOMAENE + "/om/emil-rostgaard/",
            "jobTitle": "Ansvarshavende redaktør",
            "sameAs": ["https://www.linkedin.com/in/emil-rostgaard-702809195/"],
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE["navn"],
            "url": DOMAENE + "/",
            "logo": {"@type": "ImageObject", "url": DOMAENE + "/assets/img/favicon.svg"},
        },
    }, ensure_ascii=False)


# ---------------------------------------------------------------- indhold

def laes_indholdsfil(sti):
    raa = sti.read_text(encoding="utf-8")
    hoved, krop = raa.split("\n---\n", 1)
    meta = {}
    for linje in hoved.strip().splitlines():
        if ":" in linje:
            k, v = linje.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, krop.strip()


def byg_artikel(sti):
    meta, krop = laes_indholdsfil(sti)
    meta = {k: erstat_variabler(v) for k, v in meta.items()}
    url = meta["url"]
    krop = erstat_variabler(krop)

    # sider med "top: ja" får samme opbygning som forsiden:
    # anbefalinger → liste → indholdsfortegnelse → artikel
    top_blok = ""
    if meta.get("top") == "ja":
        krop = krop.replace("{{tabel:alle}}", "", 1)
        top_blok = f"""
<section class="sektion sektion--anbefaling">
  <div class="ramme">
    <header class="sektion-hoved sektion-hoved--midt">
      <h2>{html.escape(meta.get('top_titel', 'Tre a-kasser vi anbefaler'))}</h2>
      <p>{meta.get('top_tekst', 'Valgt ud fra hver sin situation. Hele markedet ligger i listen nedenfor.')}</p>
    </header>
    {kort_top(3)}
    <p class="anbefaling-note">Vi modtager kommission, hvis du melder dig ind via disse links. Det ændrer ikke din pris og ikke rækkefølgen i listen nedenfor, som altid sorteres efter kontingent. <a href="/saadan-tjener-vi-penge/">Læs hvordan vi tjener penge</a>.</p>
  </div>
</section>

<section class="sektion sektion--liste">
  <div class="ramme">
    <header class="sektion-hoved">
      <h2 id="alle-priser">Alle {len(AKASSER)} a-kasser og priser i {AAR}</h2>
      <p>Sorteret fra billigst til dyrest. Filtrér på adgang og selvstændige, søg efter dit fag, eller sortér efter score.</p>
    </header>
    {tabel(AKASSER, "pristabel")}
  </div>
</section>"""

    krop = erstat_shortcodes(krop)
    krop = auto_link(krop, url)
    krop = tilfoej_overskrift_id(krop)
    toc = byg_toc(krop)
    faq_ld, krop = faq_jsonld(krop)
    nav_krumme, krumme_ld = brodkrumme([(meta.get("krumme", meta["h1"]), None)])
    opdateret = meta.get("opdateret", SITE["opdateret"])

    hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">{html.escape(meta.get('kicker', 'Guide'))}</p>
    <h1>{meta['h1']}</h1>
    <p class="artikel-manchet">{meta['manchet']}</p>
    <p class="artikel-meta">
      <img class="meta-foto" src="/assets/img/emil-rostgaard.webp" alt="" width="28" height="28" loading="lazy" decoding="async">
      Af <a href="/om/emil-rostgaard/">Emil Rostgaard</a>
      <span class="prik">·</span> Opdateret <time datetime="{opdateret}">{opdateret}</time>
      <span class="prik">·</span> <span>{meta.get('laestid', '9')} min. læsning</span>
      <span class="prik">·</span> <span class="verificeret">Priser faktatjekket</span>
    </p>
  </div>
</section>"""

    indhold = f"""
{top_blok}
<div class="ramme ramme--artikel">
  <article class="prose">
    {toc}
    {krop}
  </article>
  {forfatterboks()}
  {cta_box()}
  {relaterede(url)}
</div>"""

    side(url, meta["titel"], meta["beskrivelse"], indhold,
         jsonld=[artikel_jsonld(url, meta["titel"], meta["beskrivelse"], opdateret), faq_ld, krumme_ld],
         aktiv=meta.get("aktiv"), hero=hero, klasse="side-artikel",
         opdateret=opdateret, prioritet=meta.get("prioritet", "0.8"))


# ---------------------------------------------------------------- a-kasse-sider

def byg_akasse(a):
    url = f"/a-kasser/{a['slug']}/"
    plads = AKASSER.index(a) + 1
    diff_billigst = a["pris"] - BILLIGST["pris"]
    diff_gns = a["pris"] - GNS
    net = efter_fradrag(a["pris"])
    aar_pris = a["pris"] * 12
    aar_net = net * 12

    alternativer = [x for x in AKASSER if x["slug"] != a["slug"] and (
        x["type"] == a["type"] or x["features"]["selvstaendige"] == a["features"]["selvstaendige"])][:5]
    alt_raekker = "".join(
        f'<tr><td><a href="/a-kasser/{x["slug"]}/">{html.escape(x["kort"])}</a></td>'
        f'<td class="tal-celle">{x["pris"]} kr.</td>'
        f'<td class="tal-celle">{"−" if x["pris"] < a["pris"] else "+"}{abs(x["pris"] - a["pris"])} kr.</td>'
        f'<td class="tal-celle">{"−" if x["pris"] < a["pris"] else "+"}{kr(abs(x["pris"] - a["pris"]) * 12)} kr.</td>'
        f'<td>{html.escape(x["maalgruppe"])}</td></tr>' for x in alternativer)

    fordele = "".join(f"<li>{html.escape(p)}</li>" for p in a["fordele"])
    ulemper = "".join(f"<li>{html.escape(p)}</li>" for p in a["ulemper"])
    om = "".join(f"<p>{html.escape(p)}</p>" for p in a["om"])

    ff_tekst = (f"Fagforening kan tilkøbes for {a['fagforening_tillaeg']} kr. om måneden, "
                f"så det samlede kontingent bliver {a['pris'] + a['fagforening_tillaeg']} kr."
                if a.get("fagforening_tillaeg") else
                ("Fagforening er inkluderet i kontingentet." if a["features"]["fagforening"]
                 else "Der er ingen fagforening tilknyttet — du betaler kun for a-kassen."))

    medlem_tekst = (f"cirka {kr(a['medlemmer'])} medlemmer" if a.get("medlemmer") else "et ikke offentliggjort medlemstal")

    spec = f"""
<div class="tabel-wrap" role="region" aria-label="Nøgletal" tabindex="0">
<table class="data data--enkel">
  <caption>{html.escape(a['navn'])} — nøgletal {AAR}</caption>
  <tbody>
    <tr><th scope="row">Kontingent pr. måned</th><td class="tal-celle"><strong>{a['pris']} kr.</strong></td></tr>
    <tr><th scope="row">Kontingent pr. år</th><td class="tal-celle">{kr(aar_pris)} kr.</td></tr>
    <tr><th scope="row">Reel udgift efter skattefradrag</th><td class="tal-celle">{kr(net)} kr./md. ({kr(aar_net)} kr./år)</td></tr>
    <tr><th scope="row">Placering på pris</th><td class="tal-celle">Nr. {plads} af {len(AKASSER)}</td></tr>
    <tr><th scope="row">I forhold til billigste ({html.escape(BILLIGST['kort'])})</th><td class="tal-celle">{'Billigst i landet' if diff_billigst == 0 else f'+{diff_billigst} kr./md. ({kr(diff_billigst * 12)} kr./år)'}</td></tr>
    <tr><th scope="row">I forhold til gennemsnittet ({GNS} kr.)</th><td class="tal-celle">{'−' if diff_gns < 0 else '+'}{abs(diff_gns)} kr./md.</td></tr>
    <tr><th scope="row">Fagforening</th><td>{f'+{a["fagforening_tillaeg"]} kr./md.' if a.get('fagforening_tillaeg') else ('Inkluderet' if a['features']['fagforening'] else 'Ikke tilknyttet')}</td></tr>
    <tr><th scope="row">Adgang</th><td>{type_label(a)}</td></tr>
    <tr><th scope="row">Optager selvstændige</th><td>{ja_nej(a['features']['selvstaendige'])}</td></tr>
    <tr><th scope="row">Gratis for studerende</th><td>{ja_nej(a['features']['gratis_studie'])}</td></tr>
    <tr><th scope="row">Lønsikring kan tilkøbes</th><td>{ja_nej(a['features']['loensikring'])}</td></tr>
    <tr><th scope="row">Efterlønsordning</th><td>{ja_nej(a['features']['efterloen'])}</td></tr>
    <tr><th scope="row">Medlemmer</th><td class="tal-celle">{kr(a['medlemmer']) if a.get('medlemmer') else '—'}</td></tr>
    <tr><th scope="row">Stiftet</th><td class="tal-celle">{a.get('stiftet', '—')}</td></tr>
  </tbody>
</table>
</div>"""

    faq = f"""
<h2>Ofte stillede spørgsmål om {html.escape(a['kort'])}</h2>
<div class="faq">
<details><summary>Hvad koster {html.escape(a['kort'])} om måneden i {AAR}?</summary>
<div><p>{html.escape(a['kort'])} koster {a['pris']} kr. om måneden for a-kassen alene, svarende til {kr(aar_pris)} kr. om året. Kontingentet er fradragsberettiget, så den reelle udgift er cirka {kr(net)} kr. om måneden ved en marginalskat på 31 %. {ff_tekst}</p></div></details>
<details><summary>Er {html.escape(a['kort'])} billig i forhold til de andre a-kasser?</summary>
<div><p>{html.escape(a['kort'])} ligger på plads nr. {plads} ud af {len(AKASSER)} a-kasser målt på pris. Gennemsnittet er {GNS} kr. om måneden, så {html.escape(a['kort'])} ligger {'under' if diff_gns < 0 else 'over'} gennemsnittet med {abs(diff_gns)} kr. Landets billigste a-kasse er {html.escape(BILLIGST['kort'])} til {BILLIGST['pris']} kr., og den billigste, alle kan blive medlem af, er {html.escape(BILLIGST_ALLE['kort'])} til {BILLIGST_ALLE['pris']} kr.</p></div></details>
<details><summary>Hvem kan blive medlem af {html.escape(a['kort'])}?</summary>
<div><p>{html.escape(a['maalgruppe'])}. {'A-kassen er tværfaglig og optager alle uanset uddannelse og branche.' if a['type'] == 'tvaerfaglig' else 'A-kassen er fagspecifik, så du skal have en relevant uddannelse eller beskæftigelse inden for området.'} {'Selvstændige og freelancere kan også blive medlem.' if a['features']['selvstaendige'] else 'A-kassen optager ikke selvstændige erhvervsdrivende på samme vilkår som lønmodtagere.'}</p></div></details>
<details><summary>Får jeg flere dagpenge hos {html.escape(a['kort'])} end hos andre a-kasser?</summary>
<div><p>Nej. Dagpengesatsen er fastsat ved lov og er præcis den samme i alle danske a-kasser. Den højeste sats i {AAR} er {kr(S['maks_fuldtid'])} kr. om måneden før skat for fuldtidsforsikrede. Forskellen mellem a-kasserne ligger i prisen, rådgivningen, kurserne og sagsbehandlingstiden — ikke i udbetalingen.</p></div></details>
<details><summary>Kan jeg skifte til {html.escape(a['kort'])} fra min nuværende a-kasse?</summary>
<div><p>Ja. Du kan skifte a-kasse når som helst, og det er gratis. Din anciennitet følger med, så du mister ikke retten til dagpenge eller efterløn. Du melder dig ind hos {html.escape(a['kort'])}, og de sørger selv for at melde dig ud af den gamle a-kasse. Du skal aldrig selv melde dig ud først — det kan skabe et hul i dækningen.</p></div></details>
</div>"""

    krop_html = f"""
<div class="ramme ramme--artikel">
  <article class="prose">
    <div class="ak-top">
      <div class="ak-top-logo">{logo_html(a, 'logo logo--stor')}</div>
      <div class="ak-top-tal">
        <p class="ak-pris"><span class="tal">{a['pris']}</span> <small>kr./md.</small></p>
        <p class="ak-pris-net">{kr(net)} kr. efter skattefradrag · {kr(aar_pris)} kr. om året</p>
        <p class="ak-plads">Nr. {plads} af {len(AKASSER)} på pris</p>
      </div>
      <div class="ak-top-score">
        {stjerner(score(a))}
        <span class="ak-score-label">AkasseMatch-score</span>
        <a class="ak-score-link" href="/redaktionelle-principper/#saadan-beregner-vi-scoren">Sådan beregnes den</a>
      </div>
      <div class="ak-top-cta">
        {link_ud(a, "Gå til " + a['kort'])}
        <span class="ak-top-note">Åbner {a['hjemmeside'].split('/')[2]} i et nyt vindue</span>
      </div>
    </div>

    <h2>Er {html.escape(a['kort'])} det rigtige valg for dig?</h2>
    <p class="ingress">{html.escape(a['hvem'])} A-kassen har {medlem_tekst} og koster {a['pris']} kr. om måneden i {AAR}.</p>
    {om}

    <h2>Fordele og ulemper ved {html.escape(a['kort'])}</h2>
    <div class="fu">
      <div class="fu-kol fu-kol--plus"><h3>Fordele</h3><ul>{fordele}</ul></div>
      <div class="fu-kol fu-kol--minus"><h3>Ulemper</h3><ul>{ulemper}</ul></div>
    </div>

    <h2>Nøgletal og priser for {html.escape(a['kort'])}</h2>
    {spec}

    <h2>Hvad får du for kontingentet?</h2>
    <p>Grundydelsen er den samme i alle a-kasser: retten til dagpenge, hvis du bliver ledig, og den lovpligtige rådgivning og opfølgning, som følger med. Cirka {S['statsbidrag_atp']} kr. af dit månedlige kontingent går direkte videre til staten som statsbidrag og ATP. De resterende {a['pris'] - S['statsbidrag_atp']} kr. dækker a-kassens egen administration og de ydelser, den vælger at tilbyde oveni.</p>
    <p>Hos {html.escape(a['kort'])} betyder det konkret {html.escape(a['maalgruppe'].lower())} som primær målgruppe, {'mulighed for at tilkøbe lønsikring' if a['features']['loensikring'] else 'ingen tilkøbsmulighed for lønsikring'} og {'gratis medlemskab under uddannelsen' if a['features']['gratis_studie'] else 'almindeligt kontingent for studerende'}. {ff_tekst}</p>

    <h2>Hvad koster {html.escape(a['kort'])} på lang sigt?</h2>
    <p>Et a-kassemedlemskab er en langvarig udgift, og det er derfor værd at se prisen over mere end en måned. Tabellen viser, hvad {html.escape(a['kort'])} koster over tid — både i listepris og i den reelle udgift, når skattefradraget er trukket fra.</p>
    <div class="tabel-wrap" role="region" aria-label="Pris over tid" tabindex="0">
    <table class="data data--enkel">
      <caption>Samlet udgift til {html.escape(a['kort'])} over tid ({AAR}-pris)</caption>
      <thead><tr><th scope="col">Periode</th><th scope="col">Listepris</th><th scope="col">Efter skattefradrag</th><th scope="col">Merpris vs. {html.escape(BILLIGST_ALLE['kort'])}</th></tr></thead>
      <tbody>
        <tr><th scope="row">1 måned</th><td class="tal-celle">{kr(a['pris'])} kr.</td><td class="tal-celle">{kr(net)} kr.</td><td class="tal-celle">{'−' if a['pris'] < BILLIGST_ALLE['pris'] else '+'}{kr(abs(a['pris'] - BILLIGST_ALLE['pris']))} kr.</td></tr>
        <tr><th scope="row">1 år</th><td class="tal-celle">{kr(aar_pris)} kr.</td><td class="tal-celle">{kr(aar_net)} kr.</td><td class="tal-celle">{'−' if a['pris'] < BILLIGST_ALLE['pris'] else '+'}{kr(abs(a['pris'] - BILLIGST_ALLE['pris']) * 12)} kr.</td></tr>
        <tr><th scope="row">5 år</th><td class="tal-celle">{kr(aar_pris * 5)} kr.</td><td class="tal-celle">{kr(aar_net * 5)} kr.</td><td class="tal-celle">{'−' if a['pris'] < BILLIGST_ALLE['pris'] else '+'}{kr(abs(a['pris'] - BILLIGST_ALLE['pris']) * 60)} kr.</td></tr>
        <tr><th scope="row">10 år</th><td class="tal-celle">{kr(aar_pris * 10)} kr.</td><td class="tal-celle">{kr(aar_net * 10)} kr.</td><td class="tal-celle">{'−' if a['pris'] < BILLIGST_ALLE['pris'] else '+'}{kr(abs(a['pris'] - BILLIGST_ALLE['pris']) * 120)} kr.</td></tr>
      </tbody>
    </table>
    </div>
    <p>Beregningen bruger en marginalskat på 31 procent og forudsætter uændrede priser. I praksis reguleres kontingenterne hvert år pr. 1. januar, primært fordi statsbidraget ændrer sig politisk. Tallene skal derfor læses som en sammenligning mellem a-kasser — ikke som en præcis fremskrivning.</p>

    <h2>Sådan er prisen sammensat</h2>
    <p>Af de {a['pris']} kr., du betaler hver måned til {html.escape(a['kort'])}, går {S['statsbidrag_atp']} kr. direkte videre til staten som statsbidrag og ATP-bidrag. Den del er politisk fastsat og fuldstændig ens i alle danske a-kasser — ingen a-kasse kan konkurrere på den.</p>
    <p>Tilbage bliver {a['pris'] - S['statsbidrag_atp']} kr. om måneden, som er {html.escape(a['kort'])}s eget administrationsbidrag. Det dækker sagsbehandlere, rådgivning, kurser, it-systemer og medlemsservice. Det er reelt kun her, a-kasserne adskiller sig prismæssigt fra hinanden — og det sætter forskellen i perspektiv: hvor {html.escape(BILLIGST_ALLE['kort'])} bruger {BILLIGST_ALLE['pris'] - S['statsbidrag_atp']} kr. på administration, bruger {html.escape(a['kort'])} {a['pris'] - S['statsbidrag_atp']} kr.</p>
    <p>Hele kontingentet er fradragsberettiget, og {html.escape(a['kort'])} indberetter automatisk beløbet til Skattestyrelsen. Du skal altså ikke selv gøre noget for at få fradraget med på årsopgørelsen.</p>

    <h2>Hvilke dagpenge får du som medlem af {html.escape(a['kort'])}?</h2>
    <p>Præcis de samme som i alle andre a-kasser. Dagpengesatserne er fastsat ved lov, og de reguleres hvert år pr. 1. januar. Det betyder, at {html.escape(a['kort'])} hverken kan give dig mere eller mindre end en a-kasse til {BILLIGST['pris']} eller {DYREST['pris']} kr. om måneden.</p>
    {satstabel()}
    <p>Det, {html.escape(a['kort'])} kan påvirke, er noget andet: hvor hurtigt din sag bliver behandlet, om din sats bliver beregnet rigtigt første gang, og hvilken rådgivning du får undervejs. En dagpengesats, der er sat 1.000 kr. for lavt om måneden, koster dig cirka 24.000 kr. over en toårig dagpengeperiode — mange gange mere end forskellen på kontingenterne.</p>

    <h2>{html.escape(a['kort'])} sammenlignet med lignende a-kasser</h2>
    <p>Nedenfor ser du, hvordan prisen står i forhold til de nærmeste alternativer. Husk, at dagpengene er identiske — så en merpris skal modsvares af ydelser, du reelt bruger.</p>
    <div class="tabel-wrap" role="region" aria-label="Alternativer" tabindex="0">
    <table class="data data--enkel">
      <caption>Alternativer til {html.escape(a['kort'])} ({AAR})</caption>
      <thead><tr><th scope="col">A-kasse</th><th scope="col">Pris/md.</th><th scope="col">Forskel/md.</th><th scope="col">Forskel/år</th><th scope="col">Målgruppe</th></tr></thead>
      <tbody>{alt_raekker}</tbody>
    </table>
    </div>

    <h2>Sådan melder du dig ind i {html.escape(a['kort'])}</h2>
    <ol class="trin">
      <li><strong>Tjek at du opfylder betingelserne.</strong> {'A-kassen er åben for alle, så du behøver hverken en bestemt uddannelse eller branche.' if a['type'] == 'tvaerfaglig' else 'A-kassen er fagspecifik, så du skal have en relevant uddannelse eller være beskæftiget inden for området.'}</li>
      <li><strong>Meld dig ind online.</strong> Det tager typisk under fem minutter med MitID. Du skal bruge dit CPR-nummer og oplysninger om din nuværende a-kasse, hvis du skifter.</li>
      <li><strong>Lad {html.escape(a['kort'])} klare overflytningen.</strong> Du skal ikke selv melde dig ud af din gamle a-kasse. Den nye sørger for overflytningen, så du undgår et hul i dækningen.</li>
      <li><strong>Kontrollér din anciennitet.</strong> Når overflytningen er gennemført, kan du se din samlede medlemsanciennitet i selvbetjeningen. Den afgør blandt andet retten til beskæftigelsestillæg og efterløn.</li>
      <li><strong>Tag stilling til efterløn og lønsikring.</strong> Efterlønsbidraget koster {S['efterloensbidrag']} kr. om måneden oveni og er et selvstændigt valg — det er ikke en del af a-kassekontingentet.</li>
    </ol>

    {cta_box(f"Vil du videre med {a['kort']}?", f"{html.escape(a['kort'])} koster {a['pris']} kr. om måneden. Du kan melde dig ind online med MitID, og a-kassen sørger selv for at flytte dig fra din nuværende a-kasse.")}

    {faq}

    <h2>Vores vurdering</h2>
    <p>{html.escape(a['kort'])} er {'et af landets billigste valg' if plads <= 5 else ('et mellemdyrt valg' if plads <= 15 else 'et af de dyrere valg')} med {a['pris']} kr. om måneden. {html.escape(a['hvem'])} Er du i tvivl, så husk hovedreglen: dagpengene er ens overalt, så du skal vælge ud fra pris plus de ydelser, du realistisk kommer til at bruge.</p>
    <p>Overvejer du alternativer, kan du <a href="/sammenlign/">sammenligne alle {len(AKASSER)} a-kasser side om side</a> eller læse vores gennemgang af <a href="/billigste-a-kasse/">den billigste a-kasse i {AAR}</a>.</p>
  </article>
  {forfatterboks()}
  {relaterede(url)}
</div>"""

    nav_krumme, krumme_ld = brodkrumme([("A-kasser", "/a-kasser/"), (a["kort"], None)])
    hero = f"""
<section class="artikel-hero artikel-hero--ak">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">A-kasse anmeldelse · {AAR}</p>
    <h1>{html.escape(a['navn'])}: pris, fordele og anmeldelse {AAR}</h1>
    <p class="artikel-manchet">{html.escape(a['kort'])} koster {a['pris']} kr. om måneden i {AAR} og henvender sig til {html.escape(a['maalgruppe'].lower())}. Her er nøgletallene, fordelene, ulemperne og hvordan prisen står i forhold til de {len(AKASSER)} andre a-kasser.</p>
    <p class="artikel-meta">
      <img class="meta-foto" src="/assets/img/emil-rostgaard.webp" alt="" width="28" height="28" loading="lazy" decoding="async">
      Af <a href="/om/emil-rostgaard/">Emil Rostgaard</a>
      <span class="prik">·</span> Opdateret <time datetime="{SITE['opdateret']}">{SITE['opdateret']}</time>
      <span class="prik">·</span> <span class="verificeret">Pris kontrolleret hos udbyder</span>
    </p>
  </div>
</section>"""

    faq_ld, krop_html = faq_jsonld(krop_html)
    titel = f"{a['kort']} a-kasse {AAR} — pris {a['pris']} kr./md."
    besk = (f"{a['navn']} koster {a['pris']} kr./md. i {AAR}. Se fordele, ulemper, "
            f"målgruppe og hvordan prisen ligger mod de {len(AKASSER)} andre a-kasser.")
    side(url, titel, besk, krop_html,
         jsonld=[artikel_jsonld(url, titel, besk, SITE["opdateret"]), faq_ld, krumme_ld],
         aktiv="/a-kasser/", hero=hero, klasse="side-akasse", prioritet="0.7")


# ---------------------------------------------------------------- forside

def byg_forside():
    hero = f"""
<section class="hero" data-hero>
  <div class="hero-baggrund" aria-hidden="true">
    <picture>
      <source media="(max-width: 700px)" srcset="/assets/img/hero-lille.webp">
      <img class="hero-foto" src="/assets/img/hero.webp" alt="" width="1800" height="1005" fetchpriority="high" decoding="async">
    </picture>
    <span class="hero-slør"></span>
    <svg class="hero-graf" viewBox="0 0 1200 200" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0,150 C150,110 260,140 380,100 C500,60 600,110 720,80 C840,50 960,90 1200,40 L1200,200 L0,200 Z"/>
    </svg>
  </div>
  <div class="ramme hero-inder">
    <p class="hero-kicker"><span class="puls" aria-hidden="true"></span>Priser kontrolleret {SITE['opdateret']} · alle {len(AKASSER)} a-kasser</p>
    <h1 class="hero-titel">Find den <em>rigtige</em> a-kasse<br>på under to minutter</h1>
    <p class="hero-manchet">Dagpengene er de samme i alle a-kasser — prisen er ikke. Spar op til <strong>{kr(AARLIG_FORSKEL)} kr. om året</strong> ved at vælge rigtigt.</p>
    <div class="hero-handling">
      <a class="knap knap--stor" href="#pristabel">Se priser for alle {len(AKASSER)} <span class="knap__pil" aria-hidden="true">↓</span></a>
      <a class="knap knap--linje" href="/dagpengeberegner/">Beregn dine dagpenge</a>
    </div>
    <ul class="hero-tal">
      <li><span class="tal-stor" data-taeller="{BILLIGST['pris']}">0</span><span class="tal-label">kr./md. er laveste pris</span></li>
      <li><span class="tal-stor" data-taeller="{AARLIG_FORSKEL}">0</span><span class="tal-label">kr./år i forskel</span></li>
      <li><span class="tal-stor">0</span><span class="tal-label">kr. koster et skift</span></li>
      <li class="hero-tal-tillid"><span>Uafhængig · vi er ikke en a-kasse</span></li>
    </ul>
  </div>
</section>"""

    krop = f"""
<section class="sektion sektion--anbefaling">
  <div class="ramme">
    <header class="sektion-hoved sektion-hoved--midt">
      <h2>Kan du vælge frit? Start her</h2>
      <p>Fra {BILLIGST_ALLE['pris']} kr./md. Tre a-kasser der optager alle uanset uddannelse og branche, valgt ud fra hver sin situation. Hele markedet med alle {len(AKASSER)} ligger <a href="#pristabel">i listen nedenfor</a>.</p>
    </header>
    {kort_top(3)}
    <p class="anbefaling-note">Vi modtager kommission, hvis du melder dig ind via disse links. Det ændrer ikke din pris, og det ændrer ikke rækkefølgen i prisstabellen nedenfor, som altid sorteres efter kontingent. <a href="/saadan-tjener-vi-penge/">Læs hvordan vi tjener penge</a>.</p>
  </div>
</section>

<section class="sektion sektion--tabel">
  <div class="ramme">
    <header class="sektion-hoved">
      <h2 id="pristabel-titel">Priser på alle a-kasser i {AAR}</h2>
      <p>Sorteret fra billigst til dyrest. Filtrér på adgang og selvstændige, søg efter dit fag, eller sortér efter score.</p>
    </header>
    {tabel(AKASSER, "pristabel")}
  </div>
</section>

<section class="sektion sektion--linjal">
  <div class="ramme">
    <header class="sektion-hoved">
      <h2>Hele markedet på én skala</h2>
      <p>Forskellen mellem den billigste og den dyreste a-kasse er {SPREDNING} kr. om måneden — {kr(AARLIG_FORSKEL)} kr. over et år, for præcis den samme dagpengeret.</p>
    </header>
    {linjal()}
  </div>
</section>

<section class="sektion">
  <div class="ramme">
    <header class="sektion-hoved">
      <h2>Hvad koster a-kasse og fagforening samlet?</h2>
      <p>Fagforening er et selvstændigt valg. Forskellen mellem de billige tillæg og de klassiske forbund er langt større end forskellen på a-kassekontingenterne.</p>
    </header>
    {fagforeningstabel()}
  </div>
</section>

<section class="sektion sektion--lys">
  <div class="ramme ramme--artikel">
    <article class="prose">
      <h2>Sådan vælger du den rigtige a-kasse</h2>
      <p class="ingress">En a-kasse er en frivillig arbejdsløshedsforsikring. Du betaler et fast beløb hver måned, og til gengæld har du ret til dagpenge, hvis du bliver ledig. Det centrale at forstå er, at <strong>dagpengene er fastsat ved lov og derfor er identiske i alle a-kasser</strong>. Den højeste sats i {AAR} er {kr(S['maks_fuldtid'])} kr. om måneden før skat — uanset om du betaler {BILLIGST['pris']} eller {DYREST['pris']} kr. om måneden i kontingent.</p>
      <p>Det gør valget enklere, end mange tror. Du skal grundlæggende svare på tre spørgsmål: Kan du vælge frit, eller er du bundet til et fagområde? Har du brug for en fagforening oveni? Og bruger du de ekstra ydelser, du betaler for?</p>

      <h3>1. Er du bundet til et bestemt fagområde?</h3>
      <p>Cirka halvdelen af landets a-kasser er fagspecifikke og kræver, at du har en bestemt uddannelse eller arbejder inden for et bestemt område. De er ofte billigere, fordi medlemsgruppen er ensartet og ledigheden lav. Er du sundhedsfaglig, kan du komme helt ned på {BILLIGST['pris']} kr. hos {html.escape(BILLIGST['kort'])}. Har du en videregående uddannelse, er Akademikernes A-kasse et af de billigste valg overhovedet.</p>
      <p>Kan du ikke placeres i en fagspecifik a-kasse — eller vil du bevare friheden til at skifte branche — skal du kigge på de tværfaglige. Der er {len(TVAERFAGLIGE)} af dem, og den billigste er {html.escape(BILLIGST_ALLE['kort'])} til {BILLIGST_ALLE['pris']} kr. om måneden.</p>

      <h3>2. Skal du have en fagforening med?</h3>
      <p>A-kasse og fagforening er to forskellige ting, selvom de ofte sælges sammen. A-kassen udbetaler dagpenge. Fagforeningen forhandler overenskomster, hjælper i konflikter med arbejdsgiveren og kan føre din sag ved en usaglig opsigelse. Du kan sagtens have det ene uden det andet.</p>
      <p>Prisforskellen er markant. Hos de tværfaglige koster fagforeningstillægget typisk 69-159 kr. om måneden, mens de klassiske forbund tager 400-510 kr. Forskellen ligger i, hvad du får: overenskomstdækning, konfliktunderstøttelse og tillidsrepræsentanter på arbejdspladsen. Arbejder du et sted med overenskomst, er det ofte pengene værd. Gør du ikke, betaler du for noget, du ikke bruger. Se <a href="#hvad-koster-a-kasse-og-fagforening-samlet">den samlede pris for a-kasse og fagforening</a> længere oppe på siden.</p>

      <h3>3. Bruger du de ydelser, du betaler for?</h3>
      <p>Prisforskellen mellem den billigste og dyreste a-kasse er {SPREDNING} kr. om måneden. Det svarer til {kr(AARLIG_FORSKEL)} kr. om året, eller cirka {kr(round(AARLIG_FORSKEL * (1 - S['fradrag_marginalskat'])))} kr. efter skattefradrag. Det er ikke et formue-spørgsmål, men det er heller ikke ingenting.</p>
      <p>Betaler du mere, skal du kunne pege på, hvad du får for det: branchespecifik rådgivning, kurser du faktisk tager, en fast kontaktperson, eller specialviden om din situation som selvstændig eller freelancer. Kan du ikke det, er der ingen faglig grund til at betale mere.</p>

      <h2>Hvad koster en a-kasse reelt?</h2>
      <p>Kontingentet er fuldt fradragsberettiget. Med en marginalskat omkring 31 % betyder det, at et kontingent på {BILLIGST_ALLE['pris']} kr. reelt koster dig cirka {kr(efter_fradrag(BILLIGST_ALLE['pris']))} kr. om måneden. Fradraget indberettes automatisk af a-kassen, så du skal ikke selv gøre noget.</p>
      <p>Af kontingentet går cirka {S['statsbidrag_atp']} kr. om måneden videre til staten som statsbidrag og ATP. Den del er ens for alle a-kasser og fastsat politisk. Resten — typisk 70-155 kr. — er a-kassens eget administrationsbidrag. Det er reelt kun den del, a-kasserne konkurrerer på.</p>
      {faktaboks()}

      <h2>Hvad laver en a-kasse egentlig?</h2>
      <p>En a-kasse er en privat forening, der er godkendt af staten til at administrere arbejdsløshedsforsikringen. Der er {len(AKASSER)} af dem i Danmark, og de er alle underlagt de samme love og det samme tilsyn fra Styrelsen for Arbejdsmarked og Rekruttering.</p>
      <p>Kerneopgaven er at udbetale dagpenge, hvis du bliver ledig. Men a-kassen har også en række lovbestemte opgaver undervejs: den skal holde rådighedssamtaler med dig, vurdere om du står til rådighed for arbejdsmarkedet, og hjælpe dig med jobsøgning. Bliver du ledig, er det a-kassen — ikke jobcentret — der afholder de første samtaler i de fleste tilfælde.</p>
      <p>Oveni den lovbestemte opgave lægger a-kasserne deres egne ydelser: kurser, karriererådgivning, CV-sparring, netværk, juridisk hjælp og i nogle tilfælde fagforening. Det er her, forskellene opstår — og det er derfor, prisen varierer.</p>

      <h3>A-kasse er frivilligt</h3>
      <p>Der er ingen pligt til at være medlem af en a-kasse. Vælger du det fra, er dit sikkerhedsnet ved ledighed i stedet kontanthjælp, som er behovsvurderet: din formue og din ægtefælles indkomst tæller med, og satsen er markant lavere end dagpenge. For de fleste med et almindeligt job og en almindelig økonomi er det argumentet for at være medlem.</p>

      <h3>Hvornår du tidligst kan bruge forsikringen</h3>
      <p>Du skal have været medlem i mindst et år og opfylde indkomstkravet på {kr(S['indkomstkrav_3aar'])} kr. inden for de seneste tre år, før du kan få dagpenge. Det er derfor, timingen betyder noget: du kan ikke melde dig ind, når opsigelsen ligger på bordet, og forvente dækning. Nyuddannede har særlige regler og kan få dagpenge efter en karensmåned, hvis de melder sig ind senest 14 dage efter endt uddannelse.</p>

      <h2>Ofte stillede spørgsmål om valg af a-kasse</h2>
      <div class="faq">
        <details open><summary>Får jeg flere dagpenge i en dyr a-kasse?</summary><div><p>Nej. Dagpengesatsen er fastsat ved lov og er den samme i alle a-kasser. Den højeste sats i {AAR} er {kr(S['maks_fuldtid'])} kr. om måneden før skat for fuldtidsforsikrede. En dyrere a-kasse giver dig ikke en krone mere i dagpenge — kun eventuelt flere ydelser og mere rådgivning.</p></div></details>
        <details><summary>Hvad er den billigste a-kasse i {AAR}?</summary><div><p>{html.escape(BILLIGST['navn'])} er landets billigste med {BILLIGST['pris']} kr. om måneden, men den optager kun sundhedsfaglige. Den billigste a-kasse, alle kan blive medlem af uanset uddannelse, er {html.escape(BILLIGST_ALLE['navn'])} til {BILLIGST_ALLE['pris']} kr. om måneden.</p></div></details>
        <details><summary>Koster det noget at skifte a-kasse?</summary><div><p>Nej, det er gratis, og du kan skifte når som helst. Din anciennitet følger med, så du mister hverken retten til dagpenge eller til efterløn. Du melder dig ind i den nye a-kasse, som selv sørger for at flytte dig fra den gamle. Har du forudbetalt kontingent, får du det tilbage.</p></div></details>
        <details><summary>Skal jeg have både a-kasse og fagforening?</summary><div><p>Det er to selvstændige valg. A-kassen giver ret til dagpenge, fagforeningen forhandler løn og vilkår og hjælper i sager mod arbejdsgiveren. Er du ansat på en overenskomstdækket arbejdsplads, er der god værdi i fagforeningen. Er du ikke, kan du nøjes med a-kassen — eller vælge et billigt fagforeningstillæg på 69-159 kr. om måneden.</p></div></details>
        <details><summary>Hvor lang tid skal jeg have været medlem for at få dagpenge?</summary><div><p>Som udgangspunkt skal du have været medlem i mindst et år og opfylde indkomstkravet på {kr(S['indkomstkrav_3aar'])} kr. inden for de seneste tre år. Som nyuddannet gælder særlige regler: melder du dig ind senest 14 dage efter, du er færdig med uddannelsen, kan du få dagpenge på dimittendsats efter en måneds karens.</p></div></details>
        <details><summary>Hvad er forskellen på en tværfaglig og en fagspecifik a-kasse?</summary><div><p>En tværfaglig a-kasse optager alle uanset uddannelse og branche — der er {len(TVAERFAGLIGE)} af dem. En fagspecifik a-kasse kræver, at du har en bestemt uddannelse eller arbejder inden for et bestemt område. De fagspecifikke er ofte billigere, fordi medlemsgruppen er ensartet, men de binder dig til faget: skifter du branche, skal du typisk også skifte a-kasse.</p></div></details>
        <details><summary>Hvor lang tid tager det at melde sig ind?</summary><div><p>Under fem minutter online med MitID. Du skal bruge dit CPR-nummer og oplysninger om din nuværende a-kasse, hvis du skifter. Selve overflytningen tager typisk 1-4 uger, men du er dækket hele vejen igennem — der opstår ikke et hul, så længe du melder dig ind i den nye a-kasse i stedet for at melde dig ud af den gamle først.</p></div></details>
        <details><summary>Kan selvstændige være med i en a-kasse?</summary><div><p>Ja. {len(SELVSTAENDIGE)} af landets a-kasser optager selvstændige og freelancere. Reglerne for, hvornår du kan få dagpenge som selvstændig, er dog mere komplicerede end for lønmodtagere, og det taler for at vælge en a-kasse med reel erfaring på området — for eksempel Ase, der har rådgivere dedikeret til virksomhedsejere.</p></div></details>
      </div>
    </article>
  </div>
</section>

<section class="sektion">
  <div class="ramme">
    <header class="sektion-hoved">
      <h2>Gå direkte til din situation</h2>
      <p>Vi har lavet dybdegående guides til de situationer, hvor valget af a-kasse har størst betydning.</p>
    </header>
    <div class="guide-grid">
      <a class="guide-kort" href="/billigste-a-kasse/"><span class="guide-nr">01</span><h3>Billigste a-kasse {AAR}</h3><p>Hele prisoversigten, den reelle udgift efter fradrag og hvornår billigst faktisk er bedst.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/a-kasse-priser/"><span class="guide-nr">02</span><h3>A-kasse priser {AAR}</h3><p>Hvad kontingentet består af, hvorfor priserne steg i {AAR}, og hvad du får for pengene.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/skift-a-kasse/"><span class="guide-nr">03</span><h3>Skift a-kasse</h3><p>Trin for trin, hvad der sker med anciennitet, efterløn og forudbetalt kontingent.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/dagpengesatser/"><span class="guide-nr">04</span><h3>Dagpengesatser {AAR}</h3><p>Alle satser, beskæftigelsestillæg og hvordan din personlige sats bliver beregnet.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/dimittend-dagpenge/"><span class="guide-nr">05</span><h3>Dagpenge som nyuddannet</h3><p>Dimittendsatser, 14-dages fristen og den karensmåned, der overrasker de fleste.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/a-kasse-selvstaendig/"><span class="guide-nr">06</span><h3>A-kasse for selvstændige</h3><p>Hvornår du kan få dagpenge med CVR-nummer, og hvilke a-kasser der reelt kan hjælpe.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/a-kasse-studerende/"><span class="guide-nr">07</span><h3>A-kasse som studerende</h3><p>Gratis studiemedlemskab, hvornår du skal melde dig ind, og hvad det er værd.</p><span class="guide-mere">Læs guiden →</span></a>
      <a class="guide-kort" href="/dagpengeberegner/"><span class="guide-nr">08</span><h3>Dagpengeberegner</h3><p>Beregn din sats, din dækningsgrad og hvad a-kassen reelt koster efter fradrag.</p><span class="guide-mere">Åbn beregneren →</span></a>
    </div>
  </div>
</section>

<section class="sektion sektion--lys">
  <div class="ramme ramme--artikel">
    {forfatterboks()}
  </div>
</section>"""

    ld_site = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE["navn"],
        "url": DOMAENE + "/",
        "inLanguage": "da-DK",
        "description": SITE["beskrivelse"],
        "publisher": {"@type": "Organization", "name": SITE["navn"], "url": DOMAENE + "/"},
    }, ensure_ascii=False)

    ld_liste = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"A-kasser i Danmark sorteret efter pris {AAR}",
        "numberOfItems": len(AKASSER),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": a["navn"], "url": f"{DOMAENE}/a-kasser/{a['slug']}/"}
            for i, a in enumerate(AKASSER, 1)],
    }, ensure_ascii=False)

    faq_ld, krop = faq_jsonld(krop)

    side("/", f"Sammenlign a-kasser {AAR} — priser på alle {len(AKASSER)} danske a-kasser",
         f"Sammenlign priser på alle {len(AKASSER)} danske a-kasser i {AAR}. Fra {BILLIGST['pris']} kr./md. Se kontingent, målgruppe, fagforeningstillæg og find den billigste a-kasse til dit fag.",
         krop, jsonld=[ld_site, ld_liste, faq_ld], aktiv="/", hero=hero, klasse="side-forside", prioritet="1.0")


# ---------------------------------------------------------------- oversigter

def byg_sammenlign():
    nav_krumme, krumme_ld = brodkrumme([("Sammenlign a-kasser", None)])
    hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">Sammenligning · {AAR}</p>
    <h1>Sammenlign alle {len(AKASSER)} a-kasser i Danmark</h1>
    <p class="artikel-manchet">Filtrér på adgang, selvstændige og fagforening. Sortér efter pris. Alle kontingenter er kontrolleret {SITE['opdateret']} hos a-kassernes egne prislister.</p>
  </div>
</section>"""
    krop = f"""
<section class="sektion sektion--tabel">
  <div class="ramme">
    {tabel(AKASSER, "pristabel")}
  </div>
</section>
<section class="sektion sektion--lys">
  <div class="ramme">
    <header class="sektion-hoved"><h2>Prisen på tværs af hele markedet</h2></header>
    {linjal()}
  </div>
</section>
<section class="sektion">
  <div class="ramme ramme--artikel">
    <article class="prose">
      <h2>A-kasse + fagforening samlet</h2>
      {fagforeningstabel()}
      <h2>A-kasser der optager selvstændige</h2>
      {selvstaendigtabel()}
      <h2>Dagpengesatser {AAR}</h2>
      <p>Satserne er ens i alle a-kasser. De er fastsat ved lov og reguleres hvert år pr. 1. januar.</p>
      {satstabel()}
    </article>
    {forfatterboks()}
    {cta_box()}
  </div>
</section>"""
    side("/sammenlign/", f"Sammenlign a-kasser {AAR} — priser, fordele og målgrupper",
         f"Sammenlign alle {len(AKASSER)} danske a-kasser på pris, målgruppe, fagforeningstillæg og adgang. Filtrér og sortér selv. Priser for {AAR}.",
         krop, jsonld=[krumme_ld], aktiv="/sammenlign/", hero=hero, prioritet="0.9")


def byg_akasse_oversigt():
    nav_krumme, krumme_ld = brodkrumme([("A-kasser", None)])
    hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">Oversigt</p>
    <h1>Alle a-kasser i Danmark</h1>
    <p class="artikel-manchet">Klik ind på den enkelte a-kasse og se pris, målgruppe, fordele, ulemper og nøgletal. {len(TVAERFAGLIGE)} a-kasser er åbne for alle, {len(FAGSPECIFIKKE)} er fagspecifikke.</p>
  </div>
</section>"""
    krop = f"""
<section class="sektion">
  <div class="ramme ramme--artikel">
    <article class="prose">
      {akasse_liste_grid()}
    </article>
    {cta_box()}
  </div>
</section>"""
    side("/a-kasser/", f"A-kasser i Danmark {AAR} — komplet oversigt over alle {len(AKASSER)}",
         f"Komplet oversigt over alle {len(AKASSER)} danske a-kasser med priser for {AAR}. Se hvilke der er åbne for alle, og hvilke der kræver en bestemt uddannelse.",
         krop, jsonld=[krumme_ld], aktiv="/a-kasser/", hero=hero, prioritet="0.8")


def byg_guides():
    nav_krumme, krumme_ld = brodkrumme([("Guides", None)])
    hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">Guides</p>
    <h1>Guides om a-kasse og dagpenge</h1>
    <p class="artikel-manchet">Dybdegående gennemgange af de situationer, hvor valget af a-kasse har størst betydning. Alle guides er opdateret med {AAR}-priser og -satser.</p>
  </div>
</section>"""
    poster = [
        ("/billigste-a-kasse/", "Billigste a-kasse " + str(AAR),
         f"Hele prisoversigten fra {BILLIGST['pris']} kr./md., den reelle udgift efter skattefradrag og de tre situationer, hvor billigst faktisk ikke er bedst."),
        ("/a-kasse-priser/", f"A-kasse priser {AAR}",
         "Hvad kontingentet består af, hvorfor priserne steg ved årsskiftet, og hvad du reelt betaler efter fradrag."),
        ("/skift-a-kasse/", "Skift a-kasse",
         "Processen trin for trin, hvad der sker med anciennitet og efterløn, og de fire fejl der koster penge."),
        ("/dagpengesatser/", f"Dagpengesatser {AAR}",
         f"Alle satser, beskæftigelsestillæg på op til {kr(S['tillaeg_fuldtid'])} kr. og hvordan din personlige sats beregnes."),
        ("/dimittend-dagpenge/", "Dagpenge som nyuddannet",
         "Dimittendsatser, 14-dages fristen og karensmåneden, der overrasker de fleste."),
        ("/a-kasse-selvstaendig/", "A-kasse for selvstændige",
         "Hvornår du kan få dagpenge med CVR-nummer, reglerne om ophør og bibeskæftigelse, og hvilke a-kasser der reelt kan hjælpe."),
        ("/a-kasse-studerende/", "A-kasse som studerende",
         "Gratis studiemedlemskab, hvornår du skal melde dig ind, og hvorfor det er cirka 15.700 kr. værd."),
        ("/dagpengeberegner/", "Dagpengeberegner",
         "Beregn din sats, din dækningsgrad og hvad a-kassen koster efter fradrag."),
    ]
    kort = "".join(f"""
      <a class="guide-kort" href="{u}"><span class="guide-nr">{i:02d}</span><h3>{html.escape(t)}</h3><p>{html.escape(b)}</p><span class="guide-mere">Læs guiden →</span></a>"""
                   for i, (u, t, b) in enumerate(poster, 1))
    krop = f"""
<section class="sektion">
  <div class="ramme">
    <div class="guide-grid">{kort}</div>
  </div>
</section>
<section class="sektion sektion--lys">
  <div class="ramme ramme--artikel">
    {forfatterboks()}
    {cta_box()}
  </div>
</section>"""
    side("/guides/", f"Guides om a-kasse og dagpenge {AAR} — AkasseMatch",
         f"Dybdegående guides om valg af a-kasse, priser, skift, dagpengesatser og dimittendregler. Opdateret med {AAR}-tal.",
         krop, jsonld=[krumme_ld], aktiv="/guides/", hero=hero, prioritet="0.7")


def byg_simpel(url, titel, h1, beskrivelse, kicker, manchet, indhold, prioritet="0.4", vis_forfatter=True):
    nav_krumme, krumme_ld = brodkrumme([(h1, None)])
    hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {nav_krumme}
    <p class="artikel-kicker">{html.escape(kicker)}</p>
    <h1>{h1}</h1>
    <p class="artikel-manchet">{manchet}</p>
  </div>
</section>"""
    indhold = tilfoej_overskrift_id(erstat_variabler(indhold))
    faq_ld, indhold = faq_jsonld(indhold)
    krop = f"""
<div class="ramme ramme--artikel">
  <article class="prose">{indhold}</article>
  {forfatterboks() if vis_forfatter else ''}
</div>"""
    side(url, titel, beskrivelse, krop, jsonld=[krumme_ld, faq_ld], hero=hero, prioritet=prioritet)


# ---------------------------------------------------------------- sitemap m.m.

def byg_sitemap():
    poster = "".join(
        f"\n  <url><loc>{DOMAENE}{u}</loc><lastmod>{m}</lastmod><changefreq>monthly</changefreq><priority>{p}</priority></url>"
        for u, p, m in SIDER)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{poster}\n</urlset>\n',
        encoding="utf-8")

    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\n"
        f"User-agent: GPTBot\nAllow: /\n\n"
        f"User-agent: PerplexityBot\nAllow: /\n\n"
        f"User-agent: ClaudeBot\nAllow: /\n\n"
        f"Sitemap: {DOMAENE}/sitemap.xml\n",
        encoding="utf-8")

    (ROOT / "site.webmanifest").write_text(json.dumps({
        "name": SITE["navn"],
        "short_name": SITE["navn"],
        "lang": "da",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f2f5f1",
        "theme_color": "#0d4f47",
        "icons": [{"src": "/assets/img/favicon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def byg_favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="16" fill="#0d4f47"/>
<path d="M14 45 24 19h6l10 26h-6.4l-2-5.4H22.4l-2 5.4H14Zm10.2-10.4h6.6L27.5 25l-3.3 9.6Z" fill="#ffffff"/>
<circle cx="47" cy="39" r="7" fill="#d6f24b"/>
</svg>"""
    (ROOT / "assets" / "img" / "favicon.svg").write_text(svg, encoding="utf-8")

    og = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#0d2f2b"/>
<circle cx="1050" cy="120" r="220" fill="#0d4f47" opacity="0.6"/>
<circle cx="150" cy="560" r="180" fill="#0d4f47" opacity="0.4"/>
<text x="80" y="200" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="34" fill="#d6f24b" letter-spacing="4">AKASSEMATCH.DK</text>
<text x="80" y="320" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="82" font-weight="800" fill="#ffffff">Sammenlign alle</text>
<text x="80" y="410" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="82" font-weight="800" fill="#ffffff">{len(AKASSER)} a-kasser i {AAR}</text>
<text x="80" y="500" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="36" fill="#a9c4bd">Fra {BILLIGST['pris']} kr./md. · dagpengene er ens overalt</text>
</svg>"""
    (ROOT / "assets" / "img" / "og-billede.svg").write_text(og, encoding="utf-8")


def byg_htaccess():
    (ROOT / ".htaccess").write_text("""# AkasseMatch – Apache-konfiguration
Options -Indexes
DirectoryIndex index.html

<IfModule mod_rewrite.c>
  RewriteEngine On
  # Permanente omdirigeringer af flyttede sider
  RewriteRule ^billig-a-kasse/?$ /billigste-a-kasse/ [R=301,L]
  # Tving https
  RewriteCond %{HTTPS} off
  RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
  # Fjern www
  RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]
  RewriteRule ^(.*)$ https://%1/$1 [R=301,L]
</IfModule>

ErrorDocument 404 /404.html

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css text/plain text/xml application/javascript application/json image/svg+xml
</IfModule>

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType image/png "access plus 6 months"
  ExpiresByType image/webp "access plus 6 months"
  ExpiresByType image/svg+xml "access plus 6 months"
  ExpiresByType text/html "access plus 1 hour"
</IfModule>

<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  Header set X-Frame-Options "SAMEORIGIN"
</IfModule>
""", encoding="utf-8")


# ---------------------------------------------------------------- kør

def ryd():
    for m in ["a-kasser", "sammenlign", "billig-a-kasse", "a-kasse-priser", "skift-a-kasse",
              "dagpengesatser", "dimittend-dagpenge", "a-kasse-selvstaendig", "a-kasse-studerende",
              "dagpengeberegner", "om-os", "om", "kontakt", "privatlivspolitik", "cookiepolitik",
              "saadan-tjener-vi-penge", "redaktionelle-principper", "guides"]:
        p = ROOT / m
        if p.exists():
            shutil.rmtree(p)


def main():
    ryd()
    byg_favicon()
    byg_forside()
    byg_sammenlign()
    byg_akasse_oversigt()
    byg_guides()
    for a in AKASSER:
        byg_akasse(a)
    for fil in sorted(CONTENT.glob("*.html")):
        byg_artikel(fil)
    import statiske_sider
    statiske_sider.byg(globals())
    byg_sitemap()
    byg_htaccess()
    print(f"✔ Byggede {len(SIDER)} sider ({len(AKASSER)} a-kasser).")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT / "_build"))
    main()
