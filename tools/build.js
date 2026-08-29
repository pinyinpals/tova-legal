#!/usr/bin/env node
/*
 * Tova free-tool page generator.
 *
 * Reads ./_tools.json and writes one static tool page per entry into
 * ./<slug>/index.html, plus a hub at ./index.html.
 *
 * These pages exist to rank for high-intent utility queries ("pinyin
 * converter", "jyutping converter") that a landing page cannot win, and to be
 * the kind of page other sites link to. The tool is the content, so it sits
 * above the fold with no preamble in front of it.
 *
 * Same conventions as ../translate/build.js: visible copy mirrors the FAQPage
 * JSON-LD exactly (Google drops the rich result on a mismatch, and AI answer
 * engines quote the visible text), plus BreadcrumbList and a reference to the
 * site's MobileApplication node.
 *
 * The conversion engine and dictionaries live in ./lib/ and are shared by both
 * pages. Regenerate the dictionaries with `node build-data.js`.
 *
 * To add a tool: append to _tools.json, add an engine branch in lib/tool.js,
 * run `node build.js`, and paste the printed sitemap block into ../sitemap.xml.
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const SITE = 'https://tovatranslate.app';
const APP_STORE = 'https://apps.apple.com/us/app/tova-translate/id6764455741';
const tools = JSON.parse(fs.readFileSync(path.join(ROOT, '_tools.json'), 'utf8'));

const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

/* Base design system is shared with ../translate/build.js. Keep the two in
   sync by eye — they are deliberately separate files so a tool-page tweak
   cannot break the guide pages. */
const HEAD_CSS = `
  :root{--bg:#22A8E0;--top:#46C0EE;--bot:#1090CC;--fg:#111418;--muted:#5f6c76;
    --accent:#0090D0;--card:#fff;--band:#FAFCFD;--border:rgba(0,144,208,.18);
    --mint:#00796B;--mintbg:#E0F2F1}
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Arial,sans-serif;
    line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}
  body{color:#fff;background:
    radial-gradient(ellipse 80% 60% at 50% 0%,rgba(255,255,255,.22),transparent 60%),
    radial-gradient(ellipse 60% 40% at 90% 100%,rgba(0,80,130,.32),transparent 55%),
    linear-gradient(180deg,var(--top) 0%,var(--bg) 50%,var(--bot) 100%);min-height:100vh}
  a{color:inherit}
  .wrap{max-width:760px;margin:0 auto;padding:0 22px}
  .topbar{display:flex;align-items:center;gap:10px;padding:16px 22px;max-width:760px;margin:0 auto}
  .topbar img{width:34px;height:34px;border-radius:8px}
  .topbar b{font-size:17px;font-weight:800;letter-spacing:-.01em}
  .topbar a{text-decoration:none}
  .crumbs{font-size:13px;opacity:.85;padding:6px 0 0}
  .crumbs a{text-decoration:none}
  .hero{padding:22px 0 6px}
  .hero h1,.toolwrap h1{font-size:38px;line-height:1.12;font-weight:800;letter-spacing:-.025em;margin:16px 0 12px}
  .hero p.lede,.toolwrap p.lede{font-size:18px;opacity:.94;margin:0 0 18px;max-width:640px}
  /* Flex only so the phone layout can put the tool above the lede. DOM order
     stays h1 -> lede -> tool for crawlers and screen readers. */
  .toolwrap{display:flex;flex-direction:column}
  .toolwrap .crumbs{order:1}.toolwrap h1{order:2}.toolwrap p.lede{order:3}
  .toolwrap .toolcard{order:4}.toolwrap .privacy{order:5}
  .cta{display:inline-flex;align-items:center;gap:11px;background:#0B2536;color:#fff;text-decoration:none;
    padding:13px 20px;border-radius:14px;font-weight:700;box-shadow:0 10px 30px rgba(8,30,48,.35)}
  .cta:hover{filter:brightness(1.12)}
  .cta small{display:block;font-size:10px;opacity:.7;font-weight:600;text-transform:uppercase;letter-spacing:.08em}
  .cta span{font-size:17px;line-height:1}
  .band{background:var(--band);color:var(--fg);border-radius:26px 26px 0 0;margin-top:30px;
    box-shadow:inset 0 1px 0 rgba(0,0,0,.04)}
  .band .wrap{padding:34px 22px}
  .eyebrow{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
  h2{font-size:26px;font-weight:800;letter-spacing:-.02em;margin:8px 0 16px;color:var(--fg)}
  .band p{color:#3a4751}
  .faq{border-top:1px solid var(--border);padding:18px 0}
  .faq:last-of-type{border-bottom:1px solid var(--border)}
  .faq h3{margin:0 0 6px;font-size:18px;color:var(--fg)}
  .faq p{margin:0}
  .related{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}
  .rcard{display:block;background:#fff;border:1px solid var(--border);border-radius:14px;padding:14px 16px;
    text-decoration:none;color:var(--fg);font-weight:600;transition:transform .12s}
  .rcard:hover{transform:translateY(-2px)}
  .rcard span{display:block;font-size:12px;color:var(--muted);font-weight:500;margin-top:3px}
  footer{color:#fff;padding:26px 22px 40px;text-align:center;font-size:13px;opacity:.92}
  footer a{text-decoration:none}
  footer .frow{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:10px}
  .portfolio{font-size:12.5px;opacity:.8;margin-top:8px}

  /* ---------- the tool itself ---------- */
  .toolcard{background:#fff;color:var(--fg);border-radius:20px;padding:18px;margin:4px 0 8px;
    box-shadow:0 18px 46px rgba(6,42,66,.28)}
  .tlabel{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:8px}
  .tlabel label{font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}
  .tlabel .count{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
  textarea#in{width:100%;min-height:104px;resize:vertical;border:1.5px solid var(--border);border-radius:13px;
    padding:13px 14px;font-size:18px;line-height:1.55;font-family:inherit;color:var(--fg);background:#fff}
  textarea#in:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,144,208,.14)}
  textarea#in:disabled{background:#f4f8fa;color:var(--muted)}
  .samples{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0 2px;align-items:center}
  .samples b{font-size:12px;color:var(--muted);font-weight:600;margin-right:2px}
  .sample{background:var(--mintbg);border:1px solid rgba(0,121,107,.22);color:var(--mint);border-radius:999px;
    padding:5px 11px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
  .sample:hover{background:#cdeae7}
  .opts{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:14px 0 4px;
    padding-top:13px;border-top:1px solid var(--border)}
  .opt{display:flex;align-items:center;gap:7px;font-size:14px;color:#33424c;font-weight:600}
  .opt em{font-style:normal;color:var(--muted);font-weight:600;font-size:13px}
  .opt label{display:inline-flex;align-items:center;gap:5px;cursor:pointer}
  .opt input{accent-color:var(--accent);width:16px;height:16px;cursor:pointer}
  .outhead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:16px 0 8px}
  .outhead .eyebrow{color:var(--accent)}
  .btns{display:flex;gap:7px;flex-wrap:wrap}
  .copy,#clear{background:#fff;border:1.5px solid var(--border);color:var(--fg);border-radius:10px;
    padding:7px 12px;font-size:13px;font-weight:700;cursor:pointer;font-family:inherit}
  .copy:hover:not(:disabled),#clear:hover{border-color:var(--accent);color:var(--accent)}
  .copy:disabled{opacity:.45;cursor:default}
  .copy.ok{background:var(--mintbg);border-color:var(--mint);color:var(--mint)}
  #stacked{border:1.5px solid var(--border);border-radius:13px;padding:14px;min-height:88px;background:#FBFDFE;
    display:flex;flex-wrap:wrap;align-items:flex-end;gap:2px 1px;overflow-x:auto}
  #stacked .empty{color:var(--muted);font-size:15px;margin:0;padding:6px 2px}
  .cell{display:inline-flex;flex-direction:column;align-items:center;padding:2px 3px;border-radius:7px}
  .cell.poly{background:rgba(0,121,107,.07)}
  .cell .rd{font-size:12.5px;line-height:1.35;color:var(--mint);font-weight:700;white-space:nowrap}
  .cell .ch{font-size:27px;line-height:1.25;color:var(--fg);font-weight:600}
  .cell .alt{font-size:10.5px;line-height:1.3;color:var(--muted);white-space:nowrap}
  .plainrun{font-size:20px;line-height:1.9;color:#44525c;align-self:flex-end;white-space:pre-wrap}
  textarea#plain{width:100%;min-height:62px;resize:vertical;margin-top:10px;border:1.5px solid var(--border);
    border-radius:13px;padding:11px 13px;font-size:16px;line-height:1.6;font-family:inherit;
    color:#33424c;background:#FBFDFE}
  #status{font-size:13.5px;margin:9px 0 0;min-height:19px;color:var(--muted)}
  #refining{font-size:12.5px;margin:5px 0 0;color:var(--muted);opacity:.85}
  #refining[hidden]{display:none}
  #status.loading::before{content:"";display:inline-block;width:11px;height:11px;margin-right:7px;
    border:2px solid rgba(0,144,208,.28);border-top-color:var(--accent);border-radius:50%;
    animation:spin .7s linear infinite;vertical-align:-1px}
  #status.err{color:#B3261E;font-weight:600}
  @keyframes spin{to{transform:rotate(360deg)}}
  .srcnote{font-size:13.5px;color:var(--muted);margin-top:14px}
  .srcnote a{color:var(--accent)}
  .privacy{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.14);
    border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:7px 14px;font-size:13.5px;margin-top:12px}
  /* On a phone the tool is the page. Tighten the hero so the result area is
     visible without scrolling on a 390x844 viewport. */
  @media(max-width:560px){
    .related{grid-template-columns:1fr}
    .hero{padding:12px 0 2px}
    .hero h1,.toolwrap h1{font-size:28px;margin:8px 0 10px}
    .hero p.lede,.toolwrap p.lede{font-size:15.5px;margin:16px 0 0}
    /* tool first, explanation after — the result must be reachable without scrolling */
    .toolwrap .toolcard{order:3}.toolwrap .privacy{order:4}.toolwrap p.lede{order:5}
    .toolcard{padding:14px;border-radius:16px}
    textarea#in{min-height:82px;font-size:17px}
    .samples{margin:8px 0 0}
    .sample,#clear{padding:5px 10px;font-size:12.5px}
    .opts{gap:6px 14px;margin:11px 0 2px;padding-top:10px}
    .opt{font-size:13.5px}
    .outhead{margin:12px 0 7px}
    .copy{padding:6px 10px;font-size:12.5px}
    #stacked{min-height:70px;padding:11px}
    .cell .ch{font-size:24px}
    textarea#plain{min-height:52px;font-size:15px}
  }
  @media (prefers-reduced-motion:reduce){#status.loading::before{animation:none}}
`;

function pageHead({ title, desc, keywords, canonical, jsonld, preload }) {
  return `<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="keywords" content="${esc(keywords)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0090D0">
<meta name="apple-itunes-app" content="app-id=6764455741">
<link rel="canonical" href="${canonical}">
${preload || ''}
<link rel="icon" type="image/png" href="/tova-icon.png">
<meta property="og:type" content="website"><meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SITE}/og-image.png"><meta property="og:site_name" content="Tova Translate">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">${JSON.stringify(jsonld)}</script>
<style>${HEAD_CSS}</style></head><body`;
}

const topbar = `<div class="topbar"><a href="/" style="display:flex;align-items:center;gap:10px">
<img src="/tova-icon.png" alt="Tova Translate icon" width="34" height="34"><b>Tova Translate</b></a></div>`;

const ctaBtn = `<a class="cta" href="${APP_STORE}" target="_blank" rel="noopener">
<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 12.5c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.7 3-.4 7.4 1.3 9.8.8 1.2 1.8 2.5 3.1 2.5 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9z"/></svg>
<span><small>Download on the</small>App Store</span></a>`;

function siteFooter(extraLinks) {
  return `<footer><div class="frow">
<a href="/">Home</a><a href="/tools/">Free tools</a><a href="/translate/">Guides</a><a href="/faq/">FAQ</a>
<a href="/learn/">Tova Learn</a><a href="/support">Support</a><a href="/privacy">Privacy</a>
<a href="${APP_STORE}" target="_blank" rel="noopener">App Store</a></div>
${extraLinks || ''}
<div class="portfolio">A <a href="https://zetstudios.ca/apps/tova/">ZET Studios</a> app · Free download · No sign-up · Works in China, no VPN</div>
</footer></body></html>`;
}

/* Option controls differ per engine. The ids and the .opt/.sample class names
   are the contract with lib/tool.js — change both together. */
function optionsFor(t) {
  if (t.tool === 'pinyin') {
    return `<div class="opts"><div class="opt"><em>Tones</em>
<label><input type="radio" name="tone" value="symbol" checked> Marks <span style="color:var(--muted)">nǐ hǎo</span></label>
<label><input type="radio" name="tone" value="num"> Numbers <span style="color:var(--muted)">ni3 hao3</span></label>
<label><input type="radio" name="tone" value="none"> None <span style="color:var(--muted)">ni hao</span></label>
</div></div>`;
  }
  return `<div class="opts">
<div class="opt"><label><input type="checkbox" id="tones" checked> Tone numbers <span style="color:var(--muted)">hou2</span></label></div>
<div class="opt"><label><input type="checkbox" id="alts"> Show alternate readings</label></div>
</div>`;
}

function toolBlock(t) {
  const samples = t.samples.map(s =>
    `<button type="button" class="sample" data-text="${esc(s.text)}">${esc(s.label)}</button>`).join('');
  return `<div class="toolcard">
<div class="tlabel"><label for="in">${esc(t.inputLabel)}</label><span class="count" id="count">0 / 5000</span></div>
<textarea id="in" disabled placeholder="${esc(t.placeholder)}" spellcheck="false" autocapitalize="off"
  autocomplete="off" lang="zh" aria-describedby="status"></textarea>
<p id="status" class="loading" role="status" aria-live="polite">Loading dictionary…</p>
<p id="refining" hidden>Loading the full dictionary — readings sharpen in a moment.</p>
<div class="samples"><b>Try:</b>${samples}<button type="button" id="clear">Clear</button></div>
${optionsFor(t)}
<div class="outhead"><div class="eyebrow">Result</div>
<div class="btns">
<button type="button" class="copy" id="copy-rom" disabled>Copy romanization</button>
<button type="button" class="copy" id="copy-both" disabled>Copy side by side</button>
</div></div>
<div id="stacked"><p class="empty">Your romanization appears here as you type.</p></div>
<label for="plain" style="position:absolute;left:-9999px">Romanization only</label>
<textarea id="plain" readonly placeholder="Romanization only"></textarea>
</div>`;
}

function toolPage(t, all) {
  const url = `${SITE}/tools/${t.slug}/`;
  const jsonld = {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "BreadcrumbList", "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + "/" },
        { "@type": "ListItem", "position": 2, "name": "Free tools", "item": SITE + "/tools/" },
        { "@type": "ListItem", "position": 3, "name": t.breadcrumb, "item": url } ] },
      { "@type": "FAQPage", "mainEntity": t.faqs.map(f => (
        { "@type": "Question", "name": f.q, "acceptedAnswer": { "@type": "Answer", "text": f.a } })) },
      { "@type": "WebApplication", "@id": url + "#tool", "name": t.h1, "url": url,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
        "description": t.metaDesc, "isAccessibleForFree": true, "inLanguage": "en",
        "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
        "publisher": { "@id": SITE + "/#site" } },
      { "@type": "WebPage", "@id": url, "url": url, "name": t.title,
        "isPartOf": { "@id": SITE + "/#site" }, "about": { "@id": SITE + "/#app" },
        "primaryImageOfPage": SITE + "/og-image.png" },
      { "@type": "MobileApplication", "@id": SITE + "/#app", "name": "Tova Translate",
        "operatingSystem": "iOS", "applicationCategory": "TravelApplication",
        "downloadUrl": APP_STORE, "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" } }
    ]
  };
  const accuracy = t.accuracy.map(p => `<p>${esc(p)}</p>`).join('');
  const sources = t.sources.map(s =>
    `<li><a href="${s.url}" target="_blank" rel="noopener">${esc(s.name)}</a> — ${esc(s.detail)} (${esc(s.license)})</li>`).join('');
  const faqs = t.faqs.map(f => `<div class="faq"><h3>${esc(f.q)}</h3><p>${esc(f.a)}</p></div>`).join('');
  const related = t.related.map(r =>
    `<a class="rcard" href="${r.href}">${esc(r.name)}<span>${esc(r.sub)}</span></a>`).join('');

  const preload = t.tool === 'pinyin'
    ? '<link rel="preload" as="script" href="/tools/lib/pinyin-pro.js">'
    : '<link rel="preload" as="fetch" type="application/json" crossorigin href="/tools/lib/jyutping-core.json">';
  return pageHead({ title: t.title, desc: t.metaDesc, keywords: t.keywords, canonical: url, jsonld, preload })
    + ` data-tool="${t.tool}">`
    + topbar
    + `<div class="wrap toolwrap"><div class="crumbs"><a href="/">Tova</a> › <a href="/tools/">Free tools</a> › ${esc(t.breadcrumb)}</div>
<h1>${esc(t.h1)}</h1>
<p class="lede">${esc(t.lede)}</p>
${toolBlock(t)}
<p class="privacy">Runs in your browser · Your text is never uploaded · No sign-up</p>
</div>
<section class="band"><div class="wrap">
<div class="eyebrow">Accuracy</div><h2>${esc(t.accuracyHeading)}</h2>
${accuracy}
<div class="srcnote">Built from open data:
<ul style="margin:6px 0 0;padding-left:20px">${sources}</ul></div>

<div class="eyebrow" style="margin-top:30px">From the makers</div><h2>${esc(t.pitchHeading)}</h2>
<p>${esc(t.pitch)}</p>
<div style="margin-top:16px">${ctaBtn}</div>

<div class="eyebrow" style="margin-top:32px">Common questions</div><h2>About this tool</h2>
${faqs}

<div class="eyebrow" style="margin-top:30px">Keep going</div><h2>Related</h2>
<div class="related">${related}</div>
</div></section>
<script src="/tools/lib/tool.js" defer></script>`
    + siteFooter();
}

function hubPage(all) {
  const url = `${SITE}/tools/`;
  const jsonld = {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "CollectionPage", "@id": url, "url": url, "name": "Free Chinese Romanization Tools",
        "isPartOf": { "@id": SITE + "/#site" }, "about": { "@id": SITE + "/#app" } },
      { "@type": "BreadcrumbList", "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + "/" },
        { "@type": "ListItem", "position": 2, "name": "Free tools", "item": url } ] },
      { "@type": "ItemList", "itemListElement": all.map((t, i) => (
        { "@type": "ListItem", "position": i + 1, "url": `${SITE}/tools/${t.slug}/`, "name": t.breadcrumb })) }
    ]
  };
  const cards = all.map(t =>
    `<a class="rcard" href="/tools/${t.slug}/">${esc(t.breadcrumb)}<span>${esc(t.lede.slice(0, 96))}…</span></a>`).join('');
  return pageHead({
    title: "Free Chinese Romanization Tools — Pinyin & Jyutping Converters",
    desc: "Free browser tools from Tova Translate: convert Chinese characters to Hanyu Pinyin, or Cantonese to Jyutping. Word-level accuracy, no sign-up, nothing uploaded.",
    keywords: "pinyin converter, jyutping converter, chinese romanization tool, cantonese romanization, free chinese tools",
    canonical: url, jsonld
  })
    + '>'
    + topbar
    + `<div class="wrap"><div class="crumbs"><a href="/">Tova</a> › Free tools</div>
<section class="hero"><h1>Free tools</h1>
<p class="lede">Small browser tools built from the same romanization engine that runs inside Tova Translate. Free, no sign-up, and nothing you paste leaves your device.</p>
</section></div>
<section class="band"><div class="wrap"><div class="eyebrow">Pick a tool</div><h2>Romanization</h2>
<div class="related">${cards}</div>
<div class="eyebrow" style="margin-top:30px">The app</div><h2>When the text isn't on a screen</h2>
<p>These tools work on text you can paste. Tova Translate does the same thing through your camera — per-character readings over a live menu or street sign, plus the translation, and it keeps working offline in mainland China with no VPN.</p>
<div style="margin-top:16px">${ctaBtn}</div>
</div></section>`
    + siteFooter();
}

// ---- write ----
let written = 0;
for (const t of tools) {
  const dir = path.join(ROOT, t.slug);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), toolPage(t, tools));
  written++;
}
fs.writeFileSync(path.join(ROOT, 'index.html'), hubPage(tools));
written++;

// ---- sitemap block to paste into ../sitemap.xml ----
const today = new Date().toISOString().slice(0, 10);
console.log(`✓ wrote ${written} pages (${tools.length} tools + 1 hub)`);
console.log('\n--- paste into ../sitemap.xml before </urlset> ---\n');
console.log(`  <!-- ===== Free browser tools ===== -->`);
console.log(`  <url><loc>${SITE}/tools/</loc><lastmod>${today}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>`);
console.log(tools.map(t =>
  `  <url><loc>${SITE}/tools/${t.slug}/</loc><lastmod>${today}</lastmod><changefreq>monthly</changefreq><priority>0.9</priority></url>`).join('\n') + '\n');
