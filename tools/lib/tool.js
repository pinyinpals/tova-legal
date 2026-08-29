/* Tova free romanization tools — shared engine.
 *
 * One script drives both /tools/pinyin-converter/ and /tools/jyutping-converter/.
 * The page picks the engine with <body data-tool="pinyin"> or "jyutping".
 *
 * Everything runs in the browser. No text is ever sent anywhere — that claim is
 * on the page, so do not add a network call to the conversion path.
 */
(function () {
  'use strict';

  var TOOL = document.body.dataset.tool;          // 'pinyin' | 'jyutping'
  var LIB = '/tools/lib/';
  var HAN = /[⺀-⻿⼀-⿟㐀-䶿一-鿿豈-﫿]|[\uD840-\uD87F][\uDC00-\uDFFF]|[\uD869-\uD87E][\uDC00-\uDFFF]/;

  var $ = function (s) { return document.querySelector(s); };

  // Localised runtime strings, handed over by build.js so that one cached
  // tool.js can serve every locale.
  var T = { copied: 'Copied', loadError: 'Could not load the dictionary.',
            emptyState: '', also: 'also' };
  try { Object.assign(T, JSON.parse(document.getElementById('i18n').textContent)); }
  catch (e) { /* keep the English defaults */ }
  var input = $('#in'), stacked = $('#stacked'), plain = $('#plain'), status = $('#status');
  var data = {};   // loaded dictionaries

  // ---------------------------------------------------------------- loading
  function loadJSON(name) {
    return fetch(LIB + name).then(function (r) {
      if (!r.ok) throw new Error(name + ' ' + r.status);
      return r.json();
    });
  }
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script');
      s.src = src; s.onload = res; s.onerror = function () { rej(new Error(src)); };
      document.head.appendChild(s);
    });
  }

  /* Two-stage load. Stage one is small and unlocks the input; stage two is the
     rest of the dictionary and arrives in the background, after which the page
     silently re-renders at full accuracy. Waiting for everything up front cost
     eleven seconds on a 3G connection before the user could type anything. */
  function boot() {
    data.t2s = {};      // pinyin: traditional lookup, refines when it lands
    data.words = {};    // jyutping: word-level readings, ditto
    data.primary = {};
    data.alts = {};

    var stage1 = TOOL === 'pinyin'
      ? loadScript(LIB + 'pinyin-pro.js')
      : loadJSON('jyutping-core.json').then(function (core) {
          data.primary = core.p;
          data.alts = core.a;
        });

    return stage1.then(function () {
      input.disabled = false;
      status.classList.remove('loading');
      status.textContent = '';
      var seeded = new URLSearchParams(location.search).get('text');
      if (seeded) input.value = seeded.slice(0, 5000);
      if (input.value.trim()) render(); else input.focus();
      refine();
    }).catch(function (e) {
      status.classList.remove('loading');
      status.classList.add('err');
      status.textContent = T.loadError;
      console.error(e);
    });
  }

  // Stage two: never blocks anything, and a failure just leaves the tool at
  // character-level accuracy rather than breaking it.
  function refine() {
    var note = document.getElementById('refining');
    if (note) note.hidden = false;
    var job = TOOL === 'pinyin'
      ? loadJSON('t2s.json').then(function (m) { data.t2s = m; })
      : loadJSON('jyutping-full.json').then(function (full) {
          Object.assign(data.primary, full.p);
          Object.assign(data.alts, full.a);
          data.words = full.w;
        });
    return job.then(function () {
      if (note) note.hidden = true;
      if (input.value.trim()) render();
    }).catch(function (e) {
      if (note) note.hidden = true;
      console.warn('refinement dictionary unavailable', e);
    });
  }

  // ------------------------------------------------------------- conversion
  // Returns [{ch, reading|null, alts|null}] with one entry per input character.
  function convertPinyin(text) {
    // pinyin-pro's phrase dictionary is simplified-only, so traditional input
    // loses polyphone disambiguation (音樂 -> "yin le"). Look the phrase up in
    // simplified, then paint the readings back onto the original characters.
    // kSimplifiedVariant is 1 char -> 1 char, so the alignment holds.
    var chars = Array.from(text);
    var shadow = chars.map(function (c) { return data.t2s[c] || c; }).join('');
    var tone = document.querySelector('input[name=tone]:checked').value; // symbol|num|none
    var out = window.pinyinPro.pinyin(shadow, {
      type: 'array', nonZh: 'spaced', toneType: tone
    });
    return chars.map(function (ch, i) {
      var r = out[i];
      return { ch: ch, reading: HAN.test(ch) && r && r !== ch ? r : null, alts: null };
    });
  }

  function convertJyutping(text) {
    var chars = Array.from(text);
    var showTones = $('#tones').checked;
    var showAlts = $('#alts').checked;
    var res = [];
    var i = 0;
    while (i < chars.length) {
      var hit = null;
      // longest-match first: the word list only holds entries that
      // character-by-character lookup gets wrong, so a hit is always a fix.
      for (var len = Math.min(6, chars.length - i); len >= 2; len--) {
        var w = chars.slice(i, i + len).join('');
        if (data.words[w]) { hit = { len: len, rs: data.words[w].split(' ') }; break; }
      }
      if (hit) {
        for (var k = 0; k < hit.len; k++) {
          res.push({ ch: chars[i + k], reading: hit.rs[k], alts: null });
        }
        i += hit.len;
        continue;
      }
      var c = chars[i];
      var p = data.primary[c] || null;
      res.push({ ch: c, reading: p, alts: p && showAlts ? (data.alts[c] || null) : null });
      i++;
    }
    if (!showTones) {
      res.forEach(function (r) {
        if (r.reading) r.reading = r.reading.replace(/\d/g, '');
        if (r.alts) r.alts = r.alts.map(function (a) { return a.replace(/\d/g, ''); });
      });
    }
    return res;
  }

  var convert = TOOL === 'pinyin' ? convertPinyin : convertJyutping;

  // ---------------------------------------------------------------- render
  function render() {
    var text = input.value;
    document.getElementById('count').textContent = Array.from(text).length + ' / 5000';
    if (!text.trim()) {
      stacked.innerHTML = '';
      var ph = document.createElement('p');
      ph.className = 'empty';
      ph.textContent = T.emptyState;
      stacked.appendChild(ph);
      plain.value = '';
      setCopyState(false);
      return;
    }
    var items = convert(text);

    // Group runs of non-Chinese so spaces and punctuation don't create gaps.
    var frag = document.createDocumentFragment();
    var buf = '';
    function flush() {
      if (!buf) return;
      var s = document.createElement('span');
      s.className = 'plainrun';
      s.textContent = buf;
      frag.appendChild(s);
      buf = '';
    }
    items.forEach(function (it) {
      if (!it.reading) { buf += it.ch; return; }
      flush();
      var cell = document.createElement('span');
      cell.className = 'cell';
      var r = document.createElement('span');
      r.className = 'rd';
      r.textContent = it.reading;
      var c = document.createElement('span');
      c.className = 'ch';
      c.textContent = it.ch;
      cell.appendChild(r);
      cell.appendChild(c);
      if (it.alts && it.alts.length) {
        var a = document.createElement('span');
        a.className = 'alt';
        a.textContent = T.also + ' ' + it.alts.slice(0, 3).join(' / ');
        cell.appendChild(a);
        cell.classList.add('poly');
      }
      frag.appendChild(cell);
    });
    flush();
    stacked.innerHTML = '';
    stacked.appendChild(frag);

    // Plain romanization line: readings joined, other text kept in place.
    var line = '', pending = '';
    items.forEach(function (it) {
      if (it.reading) {
        if (pending) { line += pending; pending = ''; }
        line += (line && !/[\s(]$/.test(line) ? ' ' : '') + it.reading;
      } else {
        pending += it.ch;
      }
    });
    plain.value = (line + pending).replace(/[ \t]+/g, ' ').trim();
    setCopyState(true);
  }

  function setCopyState(on) {
    document.querySelectorAll('.copy').forEach(function (b) { b.disabled = !on; });
  }

  // ------------------------------------------------------------------ copy
  function copyText(str, btn) {
    var done = function () {
      var was = btn.textContent;
      btn.textContent = T.copied;
      btn.classList.add('ok');
      setTimeout(function () { btn.textContent = was; btn.classList.remove('ok'); }, 1400);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(str).then(done, function () { fallback(str, done); });
    } else { fallback(str, done); }
  }
  function fallback(str, done) {
    var ta = document.createElement('textarea');
    ta.value = str; ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:absolute;left:-9999px';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); done(); } catch (e) { /* no-op */ }
    document.body.removeChild(ta);
  }

  function sideBySide() {
    return convert(input.value).map(function (it) {
      return it.reading ? it.ch + '(' + it.reading + ')' : it.ch;
    }).join('');
  }

  // ------------------------------------------------------------------ wire
  var t;
  input.addEventListener('input', function () {
    if (Array.from(input.value).length > 5000) {
      input.value = Array.from(input.value).slice(0, 5000).join('');
    }
    clearTimeout(t);
    t = setTimeout(render, 60);
  });

  document.querySelectorAll('.opt input').forEach(function (el) {
    el.addEventListener('change', render);
  });

  document.querySelectorAll('.sample').forEach(function (b) {
    b.addEventListener('click', function () {
      input.value = b.dataset.text;
      render();
      input.focus();
    });
  });

  $('#copy-rom').addEventListener('click', function () { copyText(plain.value, this); });
  $('#copy-both').addEventListener('click', function () { copyText(sideBySide(), this); });
  $('#clear').addEventListener('click', function () {
    input.value = ''; render(); input.focus();
  });

  boot();
})();
