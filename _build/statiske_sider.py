# -*- coding: utf-8 -*-
"""Statiske sider: EEAT-, tillids- og jurasider."""


def byg(g):
    side = g["side"]
    byg_simpel = g["byg_simpel"]
    forfatterboks = g["forfatterboks"]
    brodkrumme = g["brodkrumme"]
    AKASSER = g["AKASSER"]
    BILLIGST = g["BILLIGST"]
    BILLIGST_ALLE = g["BILLIGST_ALLE"]
    SITE = g["SITE"]
    AAR = g["AAR"]
    DOMAENE = g["DOMAENE"]
    kr = g["kr"]
    S = g["S"]
    cta_box = g["cta_box"]
    import json

    # ---------------------------------------------------------- forfatterside
    person_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Emil Rostgaard",
        "url": DOMAENE + "/om/emil-rostgaard/",
        "image": DOMAENE + "/assets/img/emil-rostgaard.webp",
        "jobTitle": "Ansvarshavende redaktør",
        "email": SITE["email"],
        "knowsAbout": ["A-kasser", "Dagpenge", "Arbejdsløshedsforsikring", "Fagforeninger", "Efterløn"],
        "worksFor": {"@type": "Organization", "name": SITE["navn"], "url": DOMAENE + "/"},
        "sameAs": ["https://www.linkedin.com/in/emil-rostgaard-702809195/"],
    }, ensure_ascii=False)

    nav_krumme, krumme_ld = brodkrumme([("Redaktionen", None), ("Emil Rostgaard", None)])
    hero = f"""
<section class="artikel-hero artikel-hero--profil">
  <div class="ramme">
    {nav_krumme}
    <div class="profil-top">
      <img class="profil-foto" src="/assets/img/emil-rostgaard.webp" alt="Emil Rostgaard, ansvarshavende redaktør på AkasseMatch" width="160" height="160" fetchpriority="high" decoding="async">
      <div>
        <p class="artikel-kicker">Redaktionen</p>
        <h1>Emil Rostgaard</h1>
        <p class="artikel-manchet">Ansvarshavende redaktør på AkasseMatch. Skriver og faktatjekker alt indhold om a-kasser, dagpenge og kontingenter.</p>
        <p class="profil-links">
          <a class="knap knap--lille" href="https://www.linkedin.com/in/emil-rostgaard-702809195/" rel="me noopener" target="_blank">LinkedIn</a>
          <a class="knap knap--lille knap--sekundaer" href="mailto:{SITE['email']}">{SITE['email']}</a>
        </p>
      </div>
    </div>
  </div>
</section>"""

    profil_krop = f"""
<div class="ramme ramme--artikel">
  <article class="prose">
    <h2>Baggrund</h2>
    <p class="ingress">Jeg har arbejdet med sammenligning af danske forbrugerprodukter siden 2018 — først med forsikringer og teleabonnementer, siden med medlemsprodukter som a-kasser og fagforeninger. Fællestrækket er, at markederne er svære at gennemskue, fordi udbyderne sælger på følelser, mens forskellen i praksis handler om ganske få tal.</p>
    <p>A-kasseområdet er et af de mest ekstreme eksempler. Ydelsen — dagpengene — er identisk hos alle {len(AKASSER)} udbydere, fordi den er fastsat ved lov. Alligevel er der {g['SPREDNING']} kr. om måneden mellem den billigste og den dyreste. Det er den slags forskelle, jeg synes folk fortjener at kunne se på ét skærmbillede.</p>

    <h2>Sådan arbejder jeg med tallene</h2>
    <ul>
      <li><strong>Priser hentes hos kilden.</strong> Kontingenter kommer fra a-kassernes egne offentliggjorte prislister, ikke fra andre sammenligningssider.</li>
      <li><strong>Satser kommer fra myndighederne.</strong> Dagpengesatser, indkomstkrav og beskæftigelsestillæg følger Beskæftigelsesministeriets satsvejledning og STAR's regler.</li>
      <li><strong>Alt bliver kontrolleret ved årsskiftet.</strong> Kontingenter og satser reguleres pr. 1. januar. Derudover stikprøvekontrollerer jeg løbende gennem året.</li>
      <li><strong>Rækkefølgen er ikke til salg.</strong> Tabellerne sorteres efter pris. Ingen a-kasse kan betale sig til en bedre placering.</li>
    </ul>

    <h2>Hvorfor jeg lavede AkasseMatch</h2>
    <p>Da jeg selv skulle vælge a-kasse, brugte jeg en eftermiddag på at klikke rundt på sider, der enten var ejet af en a-kasse eller placerede den bedst betalende øverst. Ingen af dem svarede på det spørgsmål, jeg faktisk havde: hvad koster det, hvad får jeg, og er der nogen reel forskel?</p>
    <p>AkasseMatch er svaret på det. Ét sted med alle priser, ærlige ulemper og en tydelig markering af, hvornår du bør betale mere — og hvornår du ikke bør.</p>

    <h2>Kontakt og rettelser</h2>
    <p>Har du fundet en pris, der ikke passer, eller en formulering der er misvisende? Skriv til mig på <a href="mailto:{SITE['email']}">{SITE['email']}</a>. Jeg retter fejl inden for få hverdage og noterer større rettelser på siden om <a href="/redaktionelle-principper/">redaktionelle principper</a>.</p>
    <p>Du kan også skrive til mig på <a href="https://www.linkedin.com/in/emil-rostgaard-702809195/" rel="me noopener" target="_blank">LinkedIn</a>.</p>

    <h2>Artikler af Emil Rostgaard</h2>
    <ul class="link-liste">
      <li><a href="/billig-a-kasse/">Billigste a-kasse {AAR}</a></li>
      <li><a href="/a-kasse-priser/">A-kasse priser {AAR}</a></li>
      <li><a href="/skift-a-kasse/">Sådan skifter du a-kasse</a></li>
      <li><a href="/dagpengesatser/">Dagpengesatser {AAR}</a></li>
      <li><a href="/dimittend-dagpenge/">Dagpenge som nyuddannet</a></li>
      <li><a href="/a-kasse-selvstaendig/">A-kasse for selvstændige</a></li>
      <li><a href="/a-kasse-studerende/">A-kasse som studerende</a></li>
    </ul>
  </article>
</div>"""

    side("/om/emil-rostgaard/", f"Emil Rostgaard — ansvarshavende redaktør på AkasseMatch",
         "Emil Rostgaard er ansvarshavende redaktør på AkasseMatch og har arbejdet med sammenligning af danske forbrugerprodukter siden 2018.",
         profil_krop, jsonld=[person_ld, krumme_ld], hero=hero, prioritet="0.5")

    # ---------------------------------------------------------- om os
    org_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE["navn"],
        "url": DOMAENE + "/",
        "logo": DOMAENE + "/assets/img/favicon.svg",
        "email": SITE["email"],
        "foundingDate": "2026",
        "areaServed": "DK",
        "description": SITE["beskrivelse"],
        "employee": {"@type": "Person", "name": "Emil Rostgaard", "url": DOMAENE + "/om/emil-rostgaard/"},
    }, ensure_ascii=False)

    om_nav, om_krumme = brodkrumme([("Om AkasseMatch", None)])
    om_hero = f"""
<section class="artikel-hero">
  <div class="ramme">
    {om_nav}
    <p class="artikel-kicker">Om os</p>
    <h1>Om AkasseMatch</h1>
    <p class="artikel-manchet">Vi er ikke en a-kasse. Vi er en uafhængig sammenligningstjeneste, der samler priser og vilkår for alle {len(AKASSER)} danske a-kasser ét sted.</p>
  </div>
</section>"""
    om_krop = f"""
<div class="ramme ramme--artikel">
  <article class="prose">
    <h2>Hvad AkasseMatch er</h2>
    <p class="ingress">AkasseMatch er en dansk sammenligningstjeneste for a-kasser. Vi indsamler kontingenter, målgrupper, fagforeningstillæg og vilkår fra alle {len(AKASSER)} statsanerkendte a-kasser i Danmark og præsenterer dem, så du kan se forskellene på ét skærmbillede.</p>
    <p>Vi sælger ikke medlemskaber, vi administrerer ikke dagpenge, og vi er ikke en a-kasse. Vi kan ikke behandle din sag eller give dig bindende svar om din personlige situation — det kan kun din egen a-kasse.</p>

    <h2>Det, vi mener, er kernen</h2>
    <p>Dagpengesatsen er fastsat ved lov og er derfor identisk i alle a-kasser. Den højeste sats i {AAR} er {kr(S['maks_fuldtid'])} kr. om måneden før skat, uanset hvor du er medlem. Alligevel er der {g['SPREDNING']} kr. om måneden i forskel mellem billigste og dyreste kontingent — {kr(g['AARLIG_FORSKEL'])} kr. over et år.</p>
    <p>Det betyder ikke, at billigst altid er bedst. Det betyder, at du skal kunne pege på, hvad du får for merprisen. Kan du ikke det, betaler du for noget, du ikke bruger. Den skelnen er hele grundlaget for den måde, vi skriver på.</p>

    <h2>Sådan indsamler vi data</h2>
    <ol class="trin">
      <li><strong>Kontingenter</strong> hentes fra a-kassernes egne offentliggjorte prislister, ikke fra tredjepartssider.</li>
      <li><strong>Satser og krav</strong> følger Beskæftigelsesministeriets satsvejledning og reglerne fra Styrelsen for Arbejdsmarked og Rekruttering.</li>
      <li><strong>Medlemstal</strong> stammer fra a-kassernes egne oplysninger og offentlige opgørelser og er afrundede.</li>
      <li><strong>Fuld kontrol</strong> gennemføres ved hvert årsskifte, hvor både statsbidrag og kontingenter reguleres. Derudover foretager vi stikprøver løbende.</li>
    </ol>
    <p>Datoen for seneste kontrol står i bunden af hver tabel. Aktuelt: {SITE['opdateret']}.</p>

    <h2>Vores uafhængighed</h2>
    <p>AkasseMatch finansieres via annoncelinks. Det betyder, at vi i nogle tilfælde modtager en kommission, hvis du klikker videre til en a-kasse og melder dig ind. Det ændrer ikke prisen for dig, og det ændrer ikke rækkefølgen i vores tabeller, som altid sorteres efter pris.</p>
    <p>Vi skriver om alle {len(AKASSER)} a-kasser — også dem, vi ikke har et kommercielt samarbejde med. Vi skriver ulemper for alle, også for dem vi tjener penge på. Du kan læse hele modellen på siden <a href="/saadan-tjener-vi-penge/">Sådan tjener vi penge</a>.</p>

    <h2>Redaktionen</h2>
    <p>Alt indhold er skrevet og faktatjekket af Emil Rostgaard, som er ansvarshavende redaktør. Du kan læse mere om baggrund og arbejdsmetode på <a href="/om/emil-rostgaard/">hans profil</a>.</p>

    <h2>Fejl og rettelser</h2>
    <p>Vi retter fejl hurtigt og åbent. Finder du en pris eller en oplysning, der ikke passer, så skriv til <a href="mailto:{SITE['email']}">{SITE['email']}</a>. Vores fulde metode står beskrevet under <a href="/redaktionelle-principper/">redaktionelle principper</a>.</p>

    <h2>Kontakt</h2>
    <p>{SITE['firma']}<br>{SITE['adresse']}<br>E-mail: <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
  </article>
  {forfatterboks()}
  {cta_box()}
</div>"""
    side("/om-os/", "Om AkasseMatch — uafhængig sammenligning af danske a-kasser",
         f"AkasseMatch sammenligner priser og vilkår for alle {len(AKASSER)} danske a-kasser. Læs om vores metode, datakilder og uafhængighed.",
         om_krop, jsonld=[org_ld, om_krumme], hero=om_hero, prioritet="0.5")

    # ---------------------------------------------------------- principper
    byg_simpel(
        "/redaktionelle-principper/",
        "Redaktionelle principper — sådan arbejder AkasseMatch",
        "Redaktionelle principper",
        "Vores metode for indsamling af priser, faktatjek, rettelser og håndtering af kommercielle samarbejder.",
        "Metode og transparens",
        "Vi lægger vores arbejdsgange åbent frem, så du kan vurdere, om du kan stole på tallene.",
        f"""
<h2>1. Data kommer fra primærkilden</h2>
<p class="ingress">Vi henter kontingenter direkte fra a-kassernes egne offentliggjorte prislister. Vi kopierer ikke tal fra andre sammenligningssider, fordi fejl der spredes videre er umulige at spore tilbage.</p>
<p>Dagpengesatser, indkomstkrav, timekrav og beskæftigelsestillæg følger Beskæftigelsesministeriets satsvejledning og reglerne fra Styrelsen for Arbejdsmarked og Rekruttering. Hvor et tal er afrundet eller vejledende, skriver vi det.</p>

<h2>2. Alle priser er daterede</h2>
<p>Under hver tabel står datoen for seneste kontrol. Kontingenter og satser reguleres normalt pr. 1. januar, hvor vi gennemgår hele markedet igen. Derudover laver vi stikprøver gennem året, særligt når vi bliver gjort opmærksom på ændringer.</p>
<p>Vi skriver aldrig «opdateret i dag» automatisk for at se friske ud. Datoen afspejler, hvornår tallene faktisk er kontrolleret.</p>

<h2>3. Rækkefølgen er ikke til salg</h2>
<p>Vores tabeller sorteres som udgangspunkt efter pris, fra billigst til dyrest. Ingen a-kasse kan betale for en bedre placering, en fremhævning eller en pænere formulering. Hvor vi fremhæver et valg som anbefaling, står begrundelsen altid i teksten ved siden af.</p>
<p>På forsiden fremhæver vi tre a-kasser med hver sin begrundelse: billigst med adgang for alle, bedst uden fagforening og bedst til selvstændige. Vi har kommercielle samarbejder med alle tre, og det skriver vi ved siden af kortene. Begrundelserne er efterprøvelige — Det Faglige Hus <em>er</em> den billigste, alle kan blive medlem af, og Ase <em>har</em> den mest specialiserede rådgivning til selvstændige. Er du uenig i vurderingen, kan du se hele markedet sorteret efter pris i tabellen lige nedenfor.</p>

<h2>Sådan beregner vi scoren</h2>
<p>Hver a-kasse får en AkasseMatch-score. <strong>Scoren er ikke en brugeranmeldelse.</strong> Vi indsamler ikke kundetilfredshed, og vi viser aldrig stjerner, der giver indtryk af, at medlemmer har bedømt a-kassen. Scoren er beregnet ud fra data, som du selv kan kontrollere:</p>
<div class="tabel-wrap" role="region" tabindex="0" aria-label="Scoremodel">
<table class="data data--enkel">
  <caption>Sådan fordeler de 5 point sig</caption>
  <thead><tr><th scope="col">Parameter</th><th scope="col">Maks. point</th><th scope="col">Sådan tildeles de</th></tr></thead>
  <tbody>
    <tr><th scope="row">Pris</th><td class="tal-celle">3,0</td><td>Lineært fra dyreste a-kasse (0 point) til billigste (3 point)</td></tr>
    <tr><th scope="row">Åben for alle</th><td class="tal-celle">0,5</td><td>Gives hvis du kan blive medlem uanset uddannelse og branche</td></tr>
    <tr><th scope="row">Fagforeningstillæg</th><td class="tal-celle">0,5</td><td>0,5 hvis tillægget er under 200 kr./md., 0,3 hvis fagforening er inkluderet</td></tr>
    <tr><th scope="row">Optager selvstændige</th><td class="tal-celle">0,4</td><td>Gives hvis a-kassen tager selvstændige og freelancere</td></tr>
    <tr><th scope="row">Lønsikring kan tilkøbes</th><td class="tal-celle">0,2</td><td>Gives hvis a-kassen tilbyder lønsikring</td></tr>
    <tr><th scope="row">Gratis for studerende</th><td class="tal-celle">0,2</td><td>Gives ved gratis studiemedlemskab</td></tr>
    <tr><th scope="row">Efterlønsordning</th><td class="tal-celle">0,2</td><td>Gives hvis a-kassen administrerer efterløn</td></tr>
  </tbody>
</table>
</div>
<p>De syv parametre giver tilsammen et råtal. Råtallet omregnes derefter til en <strong>relativ skala fra 3,0 til 4,9</strong>, hvor markedets stærkeste a-kasse sætter toppen og den svageste bunden. Det betyder to ting, du bør kende: scoren siger noget om, hvordan a-kasserne ligger <em>i forhold til hinanden</em> — ikke om de er gode eller dårlige i absolut forstand. Og scoren kan ikke sammenlignes på tværs af år, fordi skalaen justeres, når priserne ændrer sig.</p>
<p>Modellen vægter pris tungest, fordi dagpengene er ens i alle a-kasser — prisen er reelt den største objektive forskel. Det betyder også, at scoren har en indbygget begrænsning: den kan ikke måle kvaliteten af rådgivningen eller sagsbehandlingstiden, og en fagspecifik a-kasse med stærk brancheviden bliver ikke belønnet for det. Derfor står der en skriftlig vurdering på hver a-kasses side, og derfor skriver vi konsekvent, at scoren ikke skal stå alene.</p>
<p>Scoren er den samme, uanset om vi har et kommercielt samarbejde med a-kassen. Formlen ligger åbent i sitets kildekode.</p>

<h2>4. Vi skriver ulemper for alle</h2>
<p>Hver a-kasse har både fordele og ulemper på sin side — også dem, vi har et kommercielt samarbejde med. En anmeldelse uden ulemper er ikke en anmeldelse, det er en annonce.</p>

<h2>5. Vi skelner mellem fakta og vurdering</h2>
<p>Priser, satser og adgangskrav er fakta og skal kunne dokumenteres. Vurderinger som «bedst til selvstændige» er redaktionelle skøn, og vi begrunder dem i teksten, så du selv kan vurdere, om argumentet holder for din situation.</p>

<h2>6. Vi giver ikke individuel rådgivning</h2>
<p>Indholdet på AkasseMatch er generel information. Vi kan ikke vurdere din konkrete sag, og vi kan ikke give bindende svar om din ret til dagpenge. Det kan kun din a-kasse, og i sidste instans Styrelsen for Arbejdsmarked og Rekruttering. Er du i tvivl, så ring til a-kassen, før du træffer et valg.</p>

<h2>7. Rettelser sker åbent</h2>
<p>Finder du en fejl, retter vi den inden for få hverdage. Ved væsentlige rettelser, der kan have påvirket en læsers beslutning, noterer vi ændringen i artiklen. Skriv til <a href="mailto:{SITE['email']}">{SITE['email']}</a>.</p>

<h2>8. Kunstig intelligens</h2>
<p>Vi bruger værktøjer til at strukturere og opdatere data, men alt offentliggjort indhold er gennemgået og godkendt af et menneske — konkret af <a href="/om/emil-rostgaard/">Emil Rostgaard</a>, der er ansvarshavende redaktør. Ingen tekst om priser eller regler går live uden manuel kontrol mod kilden.</p>

<h2>Spørgsmål</h2>
<div class="faq">
<details><summary>Er AkasseMatch ejet af en a-kasse?</summary><div><p>Nej. AkasseMatch er uafhængig og ejes ikke af en a-kasse, en fagforening eller et forbund. Vi finansieres af annoncelinks, hvilket er beskrevet i detaljer på siden <a href="/saadan-tjener-vi-penge/">Sådan tjener vi penge</a>.</p></div></details>
<details><summary>Kan en a-kasse betale for at ligge øverst?</summary><div><p>Nej. Tabellerne sorteres efter pris. Hvis vi fremhæver en a-kasse som anbefaling, står begrundelsen i teksten, og den bygger altid på pris, adgang eller en konkret ydelse.</p></div></details>
<details><summary>Hvor ofte opdateres priserne?</summary><div><p>Fuld gennemgang ved hvert årsskifte, hvor kontingenter og statsbidrag reguleres, samt løbende stikprøver. Seneste kontrol står under hver tabel — aktuelt {SITE['opdateret']}.</p></div></details>
</div>
""", prioritet="0.4")

    # ---------------------------------------------------------- tjener penge
    byg_simpel(
        "/saadan-tjener-vi-penge/",
        "Sådan tjener AkasseMatch penge — annoncelinks forklaret",
        "Sådan tjener vi penge",
        "AkasseMatch finansieres af annoncelinks. Her forklarer vi præcis, hvordan det fungerer, og hvad det ikke påvirker.",
        "Transparens",
        "Du skal kunne gennemskue, hvordan vi tjener penge, før du beslutter, om du vil stole på vores anbefalinger.",
        f"""
<h2>Den korte version</h2>
<p class="ingress">AkasseMatch er gratis at bruge. Vi tjener penge, når du klikker videre til en a-kasse gennem et af vores links og melder dig ind. A-kassen betaler os en kommission. Du betaler ikke en krone mere, end hvis du havde fundet dem selv.</p>

<h2>Hvad det ikke påvirker</h2>
<ul>
  <li><strong>Din pris.</strong> Kontingentet er præcis det samme, uanset om du kommer via os eller direkte.</li>
  <li><strong>Rækkefølgen.</strong> Vores tabeller sorteres efter pris, ikke efter kommission.</li>
  <li><strong>Hvem vi skriver om.</strong> Vi dækker alle {len(AKASSER)} danske a-kasser — også dem, vi ikke tjener en krone på.</li>
  <li><strong>Ulemperne.</strong> Hver a-kasse får skrevet sine ulemper frem, også vores samarbejdspartnere.</li>
</ul>

<h2>Hvordan et annoncelink ser ud</h2>
<p>Alle links, der kan give os en kommission, åbner i et nyt vindue og er teknisk mærket med <code>rel="sponsored nofollow"</code>. Det er den standard, søgemaskiner bruger til at identificere kommercielle links, og den gør det muligt for alle at kontrollere vores mærkning ved at se sidens kildekode.</p>
<p>Vi har ikke skjulte links inde i brødteksten, som du ikke kan se er kommercielle.</p>

<h2>Hvorfor vi ikke bare tager betaling for placering</h2>
<p>Fordi produktet så mister sin værdi. Hele pointen med en sammenligningsside er, at rækkefølgen betyder noget. I det øjeblik nummer ét er den, der betaler mest, er siden reelt en annonce forklædt som rådgivning — og den slags gennemskuer folk hurtigere, end branchen tror.</p>

<h2>Hvad du selv kan gøre</h2>
<p>Vil du ikke bruge vores links, så skriv a-kassens navn direkte i browseren. Du får samme pris, og vi har det fint med det. Vores mål er, at du træffer det rigtige valg — ikke at du klikker.</p>

<h2>Spørgsmål og svar</h2>
<div class="faq">
<details><summary>Koster det mig noget at bruge AkasseMatch?</summary><div><p>Nej. Siden er gratis, og du betaler nøjagtig samme kontingent hos a-kassen, uanset om du klikker via os eller går direkte til deres hjemmeside.</p></div></details>
<details><summary>Har I samarbejde med alle a-kasser?</summary><div><p>Nej. Vi har kommercielle samarbejder med nogle af dem, men vi omtaler og sammenligner alle {len(AKASSER)}. En a-kasse uden samarbejde bliver hverken skjult eller nedprioriteret i tabellerne.</p></div></details>
<details><summary>Påvirker kommissionen jeres anbefalinger?</summary><div><p>Nej. Vores anbefalinger bygger på pris, adgang og konkrete ydelser, og begrundelsen står altid i teksten. Landets billigste a-kasse er for eksempel {BILLIGST['kort']}, og det skriver vi, uanset samarbejdsforhold.</p></div></details>
</div>
""", prioritet="0.4")

    # ---------------------------------------------------------- kontakt
    byg_simpel(
        "/kontakt/", "Kontakt AkasseMatch", "Kontakt os",
        "Kontakt AkasseMatch med spørgsmål, rettelser til priser eller forslag til nyt indhold.",
        "Kontakt",
        "Har du fundet en fejl, eller mangler du noget på siden? Skriv til os — vi svarer typisk inden for to hverdage.",
        f"""
<h2>Skriv til redaktionen</h2>
<p class="ingress">E-mail: <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
<p>Vi læser alle henvendelser og svarer typisk inden for to hverdage. Skriver du om en pris, der ikke passer, så tag gerne et link eller et skærmbillede med — så går rettelsen hurtigere.</p>

<h2>Det kan vi hjælpe med</h2>
<ul>
  <li>Rettelser til priser, satser eller faktuelle oplysninger</li>
  <li>Forslag til emner og guides, du savner</li>
  <li>Presse- og samarbejdshenvendelser</li>
  <li>Spørgsmål om vores metode og datakilder</li>
</ul>

<h2>Det kan vi ikke hjælpe med</h2>
<p>Vi er ikke en a-kasse og kan derfor ikke behandle din sag, ændre din sats, udbetale dagpenge eller give bindende svar om din personlige situation. Har du en konkret sag, skal du kontakte din egen a-kasse — de har adgang til dine oplysninger og pligt til at vejlede dig.</p>
<p>Er du i tvivl om reglerne generelt, kan du også finde officiel vejledning hos Styrelsen for Arbejdsmarked og Rekruttering og på borger.dk.</p>

<h2>Virksomhedsoplysninger</h2>
<p>{SITE['firma']}<br>{SITE['adresse']}<br>E-mail: <a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
<p>Ansvarshavende redaktør: <a href="/om/emil-rostgaard/">Emil Rostgaard</a></p>
""", prioritet="0.3")

    # ---------------------------------------------------------- privatliv
    byg_simpel(
        "/privatlivspolitik/", "Privatlivspolitik — AkasseMatch", "Privatlivspolitik",
        "Sådan behandler AkasseMatch personoplysninger. Læs om dataansvar, retsgrundlag og dine rettigheder efter GDPR.",
        "Jura",
        "Vi behandler så få personoplysninger som overhovedet muligt. Her står præcis hvilke, hvorfor og hvor længe.",
        f"""
<h2>Dataansvarlig</h2>
<p>{SITE['firma']}, {SITE['adresse']}. E-mail: <a href="mailto:{SITE['email']}">{SITE['email']}</a>. Vi er dataansvarlige for de personoplysninger, vi behandler om dig i forbindelse med din brug af akassematch.dk.</p>

<h2>Hvilke oplysninger vi behandler</h2>
<ul>
  <li><strong>Tekniske oplysninger.</strong> Ved besøg registreres oplysninger som IP-adresse, browsertype, enhedstype, henvisende side og tidspunkt. Det sker som led i almindelig serverdrift og sikkerhed.</li>
  <li><strong>Statistik.</strong> Hvis du samtykker til statistiske cookies, indsamler vi aggregerede oplysninger om, hvilke sider der læses, og hvor længe.</li>
  <li><strong>Henvendelser.</strong> Skriver du til os, behandler vi din e-mailadresse og indholdet af din henvendelse for at kunne svare.</li>
</ul>
<p>Vi indsamler ikke CPR-numre, indkomstoplysninger eller andre følsomme oplysninger. Du kan bruge alle beregnere på siden uden at oprette en profil — indtastede tal behandles i din browser og sendes ikke til os.</p>

<h2>Retsgrundlag</h2>
<p>Behandlingen sker efter databeskyttelsesforordningens artikel 6, stk. 1, litra a (samtykke, for statistik og markedsføring) og litra f (legitim interesse, for drift, sikkerhed og besvarelse af henvendelser).</p>

<h2>Videregivelse</h2>
<p>Vi sælger ikke personoplysninger. Oplysninger kan behandles af databehandlere som hosting- og statistikleverandører, der handler efter vores instruks og på grundlag af databehandleraftaler. Klikker du på et link til en a-kasse, forlader du vores site, og a-kassens egen privatlivspolitik gælder derefter.</p>

<h2>Opbevaring</h2>
<p>Tekniske logfiler opbevares i op til 12 måneder. E-mailkorrespondance opbevares, så længe det er nødvendigt for at behandle henvendelsen, og som udgangspunkt højst 24 måneder.</p>

<h2>Dine rettigheder</h2>
<ul>
  <li>Ret til indsigt i de oplysninger, vi behandler om dig</li>
  <li>Ret til berigtigelse af urigtige oplysninger</li>
  <li>Ret til sletning</li>
  <li>Ret til begrænsning af behandling</li>
  <li>Ret til dataportabilitet</li>
  <li>Ret til at gøre indsigelse mod behandlingen</li>
  <li>Ret til at trække et samtykke tilbage — det påvirker ikke lovligheden af behandling før tilbagetrækningen</li>
</ul>
<p>Kontakt <a href="mailto:{SITE['email']}">{SITE['email']}</a> for at gøre brug af dine rettigheder. Du kan klage til Datatilsynet, Carl Jacobsens Vej 35, 2500 Valby, hvis du er utilfreds med vores behandling.</p>

<h2>Ændringer</h2>
<p>Politikken kan blive opdateret. Seneste version: {SITE['opdateret']}.</p>
""", prioritet="0.2", vis_forfatter=False)

    # ---------------------------------------------------------- cookies
    byg_simpel(
        "/cookiepolitik/", "Cookiepolitik — AkasseMatch", "Cookiepolitik",
        "Hvilke cookies bruger akassematch.dk, hvad de gør, og hvordan du ændrer eller sletter dit samtykke.",
        "Jura",
        "Vi bruger så få cookies som muligt, og du kan bruge hele siden uden at acceptere andet end de nødvendige.",
        f"""
<h2>Hvad er en cookie?</h2>
<p>En cookie er en lille tekstfil, som gemmes i din browser, når du besøger et website. Den kan bruges til at huske dine indstillinger, måle trafik eller registrere, at du er klikket videre fra én side til en anden.</p>

<h2>Hvilke cookies vi bruger</h2>
<div class="tabel-wrap" role="region" tabindex="0" aria-label="Cookies">
<table class="data data--enkel">
  <caption>Cookies på akassematch.dk</caption>
  <thead><tr><th scope="col">Type</th><th scope="col">Formål</th><th scope="col">Levetid</th><th scope="col">Kræver samtykke</th></tr></thead>
  <tbody>
    <tr><td>Nødvendige</td><td>Sikrer at siden fungerer, husker dit cookievalg</td><td>Op til 12 mdr.</td><td>Nej</td></tr>
    <tr><td>Statistik</td><td>Aggregeret måling af besøg og sidevisninger</td><td>Op til 24 mdr.</td><td>Ja</td></tr>
    <tr><td>Markedsføring</td><td>Registrering af klik videre til en a-kasse (affiliate)</td><td>Op til 12 mdr.</td><td>Ja</td></tr>
  </tbody>
</table>
</div>

<h2>Affiliate-cookies</h2>
<p>Klikker du på et link til en a-kasse, kan der blive sat en cookie hos a-kassen eller deres annoncenetværk, som registrerer, at du kom fra os. Det er den mekanisme, der gør, at vi kan modtage en kommission. Cookien indeholder ikke oplysninger om din identitet, og den ændrer ikke din pris. Læs mere under <a href="/saadan-tjener-vi-penge/">Sådan tjener vi penge</a>.</p>

<h2>Sådan ændrer eller sletter du dit samtykke</h2>
<p>Du kan til enhver tid trække dit samtykke tilbage ved at slette cookies i din browser. Vejledningen findes under browserens indstillinger for privatliv og sikkerhed. Alle større browsere tilbyder desuden en privat tilstand, hvor cookies slettes automatisk, når du lukker vinduet.</p>
<p>Bemærk, at afvisning af statistikcookies ikke begrænser din adgang til indholdet. Alle tabeller, guides og beregnere fungerer uændret.</p>

<h2>Kontakt</h2>
<p>Spørgsmål til vores brug af cookies kan rettes til <a href="mailto:{SITE['email']}">{SITE['email']}</a>. Se også vores <a href="/privatlivspolitik/">privatlivspolitik</a>. Seneste opdatering: {SITE['opdateret']}.</p>
""", prioritet="0.2", vis_forfatter=False)

    # ---------------------------------------------------------- 404
    krop_404 = f"""
<div class="ramme ramme--artikel">
  <article class="prose fejl-side">
    <p class="fejl-kode">404</p>
    <h1>Siden findes ikke</h1>
    <p class="ingress">Linket er enten forkert, eller også er siden flyttet. Her er de steder, folk oftest skal hen:</p>
    <ul class="link-liste">
      <li><a href="/sammenlign/">Sammenlign alle {len(AKASSER)} a-kasser</a></li>
      <li><a href="/billig-a-kasse/">Billigste a-kasse i {AAR}</a></li>
      <li><a href="/a-kasser/">Oversigt over alle a-kasser</a></li>
      <li><a href="/dagpengeberegner/">Beregn dine dagpenge</a></li>
      <li><a href="/">Forsiden</a></li>
    </ul>
    <p>Mener du, der burde være en side her? Skriv til <a href="mailto:{SITE['email']}">{SITE['email']}</a>.</p>
  </article>
</div>"""
    side("/404.html", "Siden findes ikke — AkasseMatch",
         "Siden kunne ikke findes. Find i stedet vores sammenligning af alle danske a-kasser.",
         krop_404, noindex=True)
