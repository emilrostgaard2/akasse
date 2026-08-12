# AkasseMatch — akassematch.dk

Statisk sammenligningssite for danske a-kasser. Alt HTML genereres fra data, så priser kun skal rettes ét sted.

## Sådan virker det

```
_build/
  data/site.json        ← satser, domæne, menu, kontaktinfo
  data/akasser.json     ← alle 24 a-kasser: pris, målgruppe, fordele, ulemper
  content/*.html        ← de lange guides (front matter + HTML)
  build.py              ← genererer hele sitet
  statiske_sider.py     ← om os, profil, jura, 404
  validate.py           ← tjekker links, SEO-felter, alt-tekster, ordantal
  lav_og_billede.py     ← genererer OG-billedet (kræver Pillow, køres sjældent)
assets/                 ← css, js, logoer, billeder
```

Alt andet i roden (`index.html`, `/a-kasser/`, `/billig-a-kasse/` osv.) er **genereret**. Ret aldrig i de filer — de bliver overskrevet ved næste build.

## Byg lokalt

```bash
python3 _build/build.py      # bygger alle sider
python3 _build/validate.py   # tjekker for fejl
```

Ingen afhængigheder ud over Python 3.10+. Åbn `index.html` i browseren for at se resultatet.

## Deploy

Push til `main` → GitHub Actions bygger, validerer og uploader via FTP til Simply.

Nødvendige secrets (Settings → Secrets and variables → Actions):

| Navn | Værdi |
|---|---|
| `FTP_SERVER` | FTP-værten fra Simply |
| `FTP_USERNAME` | FTP-brugernavn |
| `FTP_PASSWORD` | FTP-adgangskode |

Valgfri variabel `FTP_TARGET_DIR` (standard: `public_html`).

Validering kører **før** upload. Er der en fejl — et dødt link, en manglende title — stopper deployet, og der uploades ikke noget ødelagt.

## Årlig opdatering (vigtigst)

Priser og satser reguleres 1. januar. Sådan opdaterer du:

1. Ret `pris` (og evt. `fagforening_tillaeg`) for hver a-kasse i `_build/data/akasser.json`.
2. Ret satserne i `_build/data/site.json` under `satser`.
3. Ret `prisaar` og `opdateret` i `_build/data/site.json`.
4. Kør `python3 _build/build.py && python3 _build/validate.py`.
5. Commit og push.

Alle 44 sider, alle tabeller, alle FAQ-svar og hele sitemappet opdateres automatisk. Årstal i tekster skrives som `[[aar]]` og udskiftes ved build.

## Tilføj en a-kasse

Tilføj et objekt i `akasser.json` med samme felter som de øvrige. Der genereres automatisk en fuld anmeldelsesside, og a-kassen indgår i alle tabeller, linjalen og sitemappet.

Har du et logo, læg det i `assets/img/logoer/` og skriv filnavnet i feltet `logo`. Uden logo vises initialerne i en pæn boks.

## Affiliate-links

Feltet `affiliate_url` er `null` for alle a-kasser, så der linkes til `hjemmeside`. Når du får et partnerlink, skriv det i `affiliate_url` — så bruges det automatisk overalt.

Alle udgående links får `rel="sponsored nofollow noopener"` og `data-akasse="<slug>"`. Sidstnævnte sendes til `dataLayer` ved klik, så du kan måle konverteringer i GTM/GA4.

## Skabeloner og variabler i indhold

I `_build/content/*.html` kan du bruge:

**Variabler:** `[[aar]]`, `[[antal]]`, `[[billigst]]`, `[[billigst_pris]]`, `[[billigst_alle]]`, `[[billigst_alle_pris]]`, `[[dyrest]]`, `[[gns]]`, `[[spredning]]`, `[[aarlig_forskel]]`, `[[maks_sats]]`, `[[maks_deltid]]`, `[[tillaeg]]`, `[[dim_f]]`, `[[dim_u]]`, `[[statsbidrag]]`, `[[efterloen]]`, `[[indkomstkrav]]`, `[[loenkrav]]`, `[[maks_medregnet]]`, `[[timekrav]]`, `[[opdateret]]`

**Komponenter:** `{{tabel:alle}}`, `{{tabel:tvaerfaglige}}`, `{{tabel:top5}}`, `{{tabel:fagforening}}`, `{{tabel:selvstaendige}}`, `{{tabel:satser}}`, `{{linjal}}`, `{{kort:top3}}`, `{{beregner}}`, `{{cta}}`, `{{fakta}}`, `{{akasseliste}}`

FAQ skrives som `<details><summary>Spørgsmål</summary><div><p>Svar</p></div></details>` — så bliver den automatisk til FAQPage-schema.

## Redaktionelt

Priser hentes fra a-kassernes egne prislister, satser fra Beskæftigelsesministeriets satsvejledning. Datoen i `opdateret` skal afspejle, hvornår tallene faktisk er kontrolleret — ikke hvornår sitet sidst blev bygget.
