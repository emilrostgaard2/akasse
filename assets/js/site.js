/* ============================================================
   AkasseMatch — site.js
   Ingen afhængigheder. Alt fungerer uden JS (progressive enhancement).
   ============================================================ */
(function () {
  'use strict';

  var reducer = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------- dropdown i menuen */
  var drops = document.querySelectorAll('[data-drop]');
  var erMobil = function () { return window.matchMedia('(max-width: 860px)').matches; };

  function lukAlle(undtagen) {
    Array.prototype.forEach.call(drops, function (d) {
      if (d === undtagen) return;
      d.classList.remove('er-aaben');
      var k = d.querySelector('.nav-knap');
      if (k) k.setAttribute('aria-expanded', 'false');
    });
  }

  Array.prototype.forEach.call(drops, function (d) {
    var knap = d.querySelector('.nav-knap');
    if (!knap) return;

    knap.addEventListener('click', function (e) {
      e.stopPropagation();
      var aaben = d.classList.contains('er-aaben');
      lukAlle(d);
      d.classList.toggle('er-aaben', !aaben);
      knap.setAttribute('aria-expanded', String(!aaben));
    });

    // hover på desktop
    d.addEventListener('mouseenter', function () {
      if (erMobil()) return;
      lukAlle(d);
      d.classList.add('er-aaben');
      knap.setAttribute('aria-expanded', 'true');
    });
    d.addEventListener('mouseleave', function () {
      if (erMobil()) return;
      d.classList.remove('er-aaben');
      knap.setAttribute('aria-expanded', 'false');
    });

    // luk ved tab ud af gruppen
    d.addEventListener('focusout', function (e) {
      if (erMobil()) return;
      if (!d.contains(e.relatedTarget)) {
        d.classList.remove('er-aaben');
        knap.setAttribute('aria-expanded', 'false');
      }
    });
  });

  if (drops.length) {
    document.addEventListener('click', function () { lukAlle(null); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') lukAlle(null);
    });
  }

  /* ---------------------------------------------- mobilmenu */
  var menuKnap = document.querySelector('[data-menu]');
  var nav = document.getElementById('hovedmenu');
  if (menuKnap && nav) {
    menuKnap.addEventListener('click', function () {
      var aaben = menuKnap.getAttribute('aria-expanded') === 'true';
      menuKnap.setAttribute('aria-expanded', String(!aaben));
      nav.classList.toggle('er-aaben', !aaben);
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        menuKnap.setAttribute('aria-expanded', 'false');
        nav.classList.remove('er-aaben');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('er-aaben')) {
        menuKnap.setAttribute('aria-expanded', 'false');
        nav.classList.remove('er-aaben');
        menuKnap.focus();
      }
    });
  }

  /* ---------------------------------------------- header-skygge ved scroll */
  var hoved = document.querySelector('[data-hoved]');
  if (hoved) {
    var sidstScroll = -1;
    var tick = function () {
      var y = window.scrollY;
      if (y !== sidstScroll) {
        hoved.classList.toggle('er-scrollet', y > 8);
        sidstScroll = y;
      }
    };
    window.addEventListener('scroll', function () {
      window.requestAnimationFrame(tick);
    }, { passive: true });
    tick();
  }

  /* ---------------------------------------------- tællere i hero */
  var taellere = document.querySelectorAll('[data-taeller]');
  function formatTal(n) {
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }
  function koerTaeller(el) {
    var maal = parseFloat(el.getAttribute('data-taeller')) || 0;
    if (reducer || maal === 0) { el.textContent = formatTal(maal); return; }
    var start = null, varighed = 1400;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / varighed, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = formatTal(maal * eased);
      if (p < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }
  if (taellere.length) {
    if ('IntersectionObserver' in window) {
      var tObs = new IntersectionObserver(function (poster) {
        poster.forEach(function (p) {
          if (p.isIntersecting) { koerTaeller(p.target); tObs.unobserve(p.target); }
        });
      }, { threshold: 0.4 });
      Array.prototype.forEach.call(taellere, function (el) { tObs.observe(el); });
    } else {
      Array.prototype.forEach.call(taellere, koerTaeller);
    }
  }

  /* ---------------------------------------------- linjal-animation */
  var linjaler = document.querySelectorAll('[data-animeret]');
  Array.prototype.forEach.call(linjaler, function (linjal) {
    var raekker = linjal.querySelectorAll('.linjal-raekke');
    Array.prototype.forEach.call(raekker, function (r, i) {
      r.style.setProperty('--i', i);
      var pct = r.style.getPropertyValue('--pct');
      var bar = r.querySelector('.linjal-bar');
      var prik = r.querySelector('.linjal-prik');
      if (bar) bar.style.setProperty('--pct', pct);
      if (prik) prik.style.setProperty('--pct', pct);
    });
    if ('IntersectionObserver' in window && !reducer) {
      var lObs = new IntersectionObserver(function (poster) {
        poster.forEach(function (p) {
          if (p.isIntersecting) { p.target.classList.add('er-synlig'); lObs.unobserve(p.target); }
        });
      }, { threshold: 0.2 });
      lObs.observe(linjal);
    } else {
      linjal.classList.add('er-synlig');
    }
  });

  /* ---------------------------------------------- filtrering, søgning og sortering */
  Array.prototype.forEach.call(document.querySelectorAll('[data-liste]'), function (blok) {
    var beholder = blok.querySelector('.ak-liste');
    if (!beholder) return;
    var raekker = Array.prototype.slice.call(beholder.querySelectorAll('[data-raekke]'));
    var chips = blok.querySelectorAll('[data-filter]');
    var soegFelt = blok.querySelector('[data-soeg]');
    var sorterFelt = blok.querySelector('[data-sorter]');
    var tomt = blok.querySelector('.tomt-resultat');
    var nulstilKnap = blok.querySelector('[data-nulstil]');
    var aktivtFilter = 'alle';

    function opdater() {
      var q = soegFelt ? soegFelt.value.trim().toLowerCase() : '';
      var synlige = 0;
      raekker.forEach(function (r) {
        var passerFilter =
          aktivtFilter === 'alle' ||
          (aktivtFilter === 'tvaerfaglig' && r.dataset.type === 'tvaerfaglig') ||
          (aktivtFilter === 'selvstaendig' && r.dataset.selvstaendig === 'true') ||
          (aktivtFilter === 'fagforening' && r.dataset.fagforening === 'true');
        var passerSoeg = !q || (r.dataset.navn || '').indexOf(q) !== -1;
        var vis = passerFilter && passerSoeg;
        r.hidden = !vis;
        if (vis) {
          synlige++;
          var nr = r.querySelector('.ak-nr');
          if (nr) nr.textContent = synlige;
        }
      });
      if (tomt) tomt.hidden = synlige !== 0;
    }

    function sorter() {
      if (!sorterFelt) return;
      var felt = sorterFelt.value;
      raekker.sort(function (a, b) {
        var va = parseFloat(a.dataset[felt]), vb = parseFloat(b.dataset[felt]);
        return felt === 'score' ? vb - va : va - vb;
      });
      raekker.forEach(function (r) { beholder.appendChild(r); });
      opdater();
    }

    Array.prototype.forEach.call(chips, function (chip) {
      chip.addEventListener('click', function () {
        Array.prototype.forEach.call(chips, function (c) { c.classList.remove('chip--aktiv'); });
        chip.classList.add('chip--aktiv');
        aktivtFilter = chip.dataset.filter;
        opdater();
      });
    });

    if (soegFelt) {
      var timer;
      soegFelt.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(opdater, 120);
      });
    }

    if (sorterFelt) sorterFelt.addEventListener('change', sorter);

    if (nulstilKnap) {
      nulstilKnap.addEventListener('click', function () {
        if (soegFelt) soegFelt.value = '';
        aktivtFilter = 'alle';
        Array.prototype.forEach.call(chips, function (c) {
          c.classList.toggle('chip--aktiv', c.dataset.filter === 'alle');
        });
        opdater();
      });
    }
  });

  /* ---------------------------------------------- dagpengeberegner */
  var SATSER = {
    maksFuld: 22041,
    maksDeltid: 14694,
    tillaegFuld: 26198,
    tillaegDeltid: 17465,
    dimF: 18074,
    dimU: 15759,
    marginalskat: 0.31
  };

  Array.prototype.forEach.call(document.querySelectorAll('[data-beregner]'), function (b) {
    var loen = b.querySelector('#b-loen');
    var type = b.querySelector('#b-type');
    var situation = b.querySelector('#b-situation');
    var kontingent = b.querySelector('#b-kontingent');
    var uSats = b.querySelector('#b-sats');
    var uDaekning = b.querySelector('#b-daekning');
    var uNet = b.querySelector('#b-net');
    var uAar = b.querySelector('#b-aar');
    var uForhold = b.querySelector('#b-forhold');
    var uNote = b.querySelector('#b-note');
    if (!loen || !uSats) return;

    function fmt(n) { return formatTal(n); }

    function beregn() {
      var l = Math.max(0, parseFloat(loen.value) || 0);
      var k = Math.max(0, parseFloat(kontingent.value) || 0);
      var deltid = type.value === 'deltid';
      var sit = situation.value;
      var maks = deltid ? SATSER.maksDeltid : SATSER.maksFuld;
      var sats, note;

      if (sit === 'dim-f') {
        sats = deltid ? Math.round(SATSER.dimF * (SATSER.maksDeltid / SATSER.maksFuld)) : SATSER.dimF;
        note = 'Dimittendsats med forsørgerpligt. Satsen er fast og beregnes ikke ud fra din løn.';
      } else if (sit === 'dim-u') {
        sats = deltid ? Math.round(SATSER.dimU * (SATSER.maksDeltid / SATSER.maksFuld)) : SATSER.dimU;
        note = 'Dimittendsats uden forsørgerpligt de første 3 måneder. Derefter falder satsen afhængigt af din alder.';
      } else {
        // 90 % af indkomst efter 8 % AM-bidrag, med loft
        var grundlag = l * 0.92;
        sats = Math.round(grundlag * 0.9);
        if (sit === 'tillaeg') {
          var maksT = deltid ? SATSER.tillaegDeltid : SATSER.tillaegFuld;
          sats = Math.min(sats > maks ? maksT : Math.round(sats * 1.1886), maksT);
          note = 'Med beskæftigelsestillæg de første 3 måneder. Tillægget bortfalder efter 481 timers ledighed.';
        } else {
          sats = Math.min(sats, maks);
          note = sats >= maks
            ? 'Du rammer maksimalsatsen. Tjener du mere, stiger dagpengene ikke — det er her lønsikring bliver relevant.'
            : 'Din sats er under maksimum, fordi dagpengene udgør 90 % af din indkomst efter AM-bidrag.';
        }
      }

      var daekning = l > 0 ? Math.round((sats / l) * 100) : 0;
      var net = Math.round(k * (1 - SATSER.marginalskat));
      var aar = net * 12;
      var forhold = aar > 0 ? (sats * 12 / aar) : 0;

      uSats.textContent = fmt(sats);
      uDaekning.textContent = daekning + ' %';
      uNet.textContent = fmt(net) + ' kr./md.';
      uAar.textContent = fmt(aar) + ' kr.';
      uForhold.textContent = forhold > 0 ? forhold.toFixed(1).replace('.', ',') + '×' : '—';
      if (uNote) uNote.textContent = note;
    }

    [loen, type, situation, kontingent].forEach(function (el) {
      if (el) {
        el.addEventListener('input', beregn);
        el.addEventListener('change', beregn);
      }
    });
    beregn();
  });

  /* ---------------------------------------------- klik-sporing på affiliate-links */
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[data-akasse]') : null;
    if (!a) return;
    if (window.dataLayer && typeof window.dataLayer.push === 'function') {
      window.dataLayer.push({
        event: 'akasse_klik',
        akasse: a.getAttribute('data-akasse'),
        placering: a.className
      });
    }
  });
})();
