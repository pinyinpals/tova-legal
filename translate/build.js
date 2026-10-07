#!/usr/bin/env node
// Pageview beacon. GitHub Pages runs no server code, so unlike the Cloudflare
// sites there is no middleware to inject this at the edge — it has to be in the
// emitted HTML, or a rebuild silently strips it back out of every generated page.
// Kept identical to what marketing/add-beacon.py writes in gtm-platform; if one
// changes, change both. No country here: that needs a Cloudflare edge.
/*
 * Tova guide generator.
 *
 * Reads ./_guides.json (English source of truth), ./_plates.json (app screen
 * alt text + captions) and ./i18n/<locale>.json (translated guides), and writes
 *   translate/<slug>/index.html            one page per English guide
 *   translate/index.html                   the hub
 *   <locale>/translate/<slug>/index.html   one page per translated guide
 *
 * Header and footer are NOT drawn here: every page carries the
 * <!--tv:header--> / <!--tv:footer--> markers and ../_build/chrome.py fills
 * them, so all pages on the site share one nav. Run the whole site build with
 * ../_build/build_all.sh.
 *
 * Structured data rules (unchanged since the first version): the visible FAQ
 * text mirrors the FAQPage JSON-LD exactly, because Google drops the rich
 * result on a mismatch and AI answer engines quote the visible text.
 * HowTo steps and HowTo JSON-LD are emitted ONLY for guides with
 * "type": "howto" — a comparison page with a "three steps" block stapled on
 * reads as boilerplate and the steps described nothing real.
 *
 * Guide fields beyond the basics:
 *   type       "howto" | "editorial"
 *   updated    YYYY-MM-DD   tested  YYYY-MM   (the byline)
 *   sections   body blocks: h2, h3, p[], callout, ul[], ol[], table{head,rows,hanCols,romCols}
 *   images     [{plate, after}]  — app screens from /media/app/, placed after section index `after`
 *   related    [slug, ...]  — 4-6 curated "Related guides"
 *   toolCta    {href, title, text}
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const SITE = 'https://tovatranslate.app';
const APP_STORE = 'https://apps.apple.com/us/app/tova-translate/id6764455741';
const guides = JSON.parse(fs.readFileSync(path.join(ROOT, '_guides.json'), 'utf8'));
const PLATES = JSON.parse(fs.readFileSync(path.join(ROOT, '_plates.json'), 'utf8'));
const BY_SLUG = Object.fromEntries(guides.map(g => [g.slug, g]));
const IMG_W = 280, IMG_H = 607; // media/app/*.webp are 560x1215 (2x)

// Locales with translated guides. `intl` is the BCP-47 tag used to format
// dates in the byline; `hreflang` matches the homepage + tools clusters.
const LOCALES = [
  { code: 'it', lang: 'it', hreflang: 'it', intl: 'it-IT' },
  { code: 'es', lang: 'es', hreflang: 'es', intl: 'es-ES' },
  { code: 'de', lang: 'de', hreflang: 'de', intl: 'de-DE' },
  { code: 'fr', lang: 'fr', hreflang: 'fr', intl: 'fr-FR' },
  { code: 'ja', lang: 'ja', hreflang: 'ja', intl: 'ja-JP' },
  { code: 'ko', lang: 'ko', hreflang: 'ko', intl: 'ko-KR' },
  { code: 'zh-tw', lang: 'zh-Hant', hreflang: 'zh-Hant', intl: 'zh-TW' },
  { code: 'th', lang: 'th', hreflang: 'th', intl: 'th-TH' },
];
const I18N = {};
for (const l of LOCALES) {
  const f = path.join(ROOT, 'i18n', l.code + '.json');
  if (fs.existsSync(f)) I18N[l.code] = JSON.parse(fs.readFileSync(f, 'utf8'));
}
const ACTIVE = LOCALES.filter(l => I18N[l.code]);

const EN_UI = {
  guides: 'Guides',
  byline: 'By ZET Studios · Tested {tested} · Updated {updated}',
  toc: 'On this page', related: 'Related guides',
  faqEyebrow: 'Common questions', faqH2: 'About this guide',
  howEyebrow: 'How it works', howH2: 'Read it in three steps',
  reassure: '**Free** · No sign-up · Works offline in China — no VPN',
  ctaSmall: 'Download on the', ctaBig: 'App Store',
  midCtaTitle: 'Try it on the next menu or sign',
  midCtaText: 'Free on the App Store. Works offline in China, no VPN.',
  tableHint: 'Swipe to see the whole table →', guideArrow: 'Guide →', englishOnly: '',
};

const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');
const slugify = (s) => String(s).toLowerCase().normalize('NFKD')
  .replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '').slice(0, 60) || 's';

const HEAD_CSS = `
  :root{--bg:#0F6FA5;--top:#1579B0;--bot:#0B6498;--fg:#111418;--muted:#56626b;
    --accent:#006FA6;--card:#fff;--band:#FAFCFD;--border:rgba(0,111,166,.20)}
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Arial,sans-serif;
    line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:clip}
  body{color:#fff;background:
    radial-gradient(ellipse 60% 40% at 90% 100%,rgba(0,50,90,.30),transparent 55%),
    linear-gradient(180deg,var(--top) 0%,var(--bg) 50%,var(--bot) 100%);min-height:100vh}
  a{color:inherit}
  img{max-width:100%;height:auto}
  .wrap{max-width:760px;margin:0 auto;padding:0 20px}
  .crumbs{font-size:14px;padding:18px 0 0}
  .crumbs a{text-decoration:underline;text-underline-offset:2px}
  .hero{padding:18px 0 34px}
  .hero h1{font-size:40px;line-height:1.12;font-weight:800;letter-spacing:-.025em;margin:8px 0 12px;
    text-wrap:balance}
  .byline{font-size:14px;margin:0 0 16px;opacity:.95}
  .hero p.lede{font-size:19px;margin:0 0 22px;max-width:640px}
  .cta{display:inline-flex;align-items:center;gap:11px;background:#0B2536;color:#fff;text-decoration:none;
    padding:12px 20px;border-radius:14px;font-weight:700;box-shadow:0 10px 30px rgba(8,30,48,.35);min-height:52px}
  .cta:hover{filter:brightness(1.15)}
  .cta small{display:block;font-size:11px;opacity:.85;font-weight:600;letter-spacing:.02em}
  .cta span{font-size:18px;line-height:1.05}
  .reassure{font-size:14px;margin:14px 0 0}
  .band{background:var(--band);color:var(--fg);border-radius:26px 26px 0 0}
  .gwrap{max-width:760px;margin:0 auto;padding:34px 20px 40px}
  .eyebrow{font-size:12.5px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
  h2{font-size:26px;font-weight:800;letter-spacing:-.02em;margin:8px 0 18px;color:var(--fg);line-height:1.25}
  .prose h2{font-size:25px;margin:34px 0 10px;scroll-margin-top:80px}
  .prose h3{font-size:18.5px;margin:24px 0 6px}
  .prose p{margin:0 0 14px}
  .prose ul,.prose ol{margin:0 0 16px;padding-left:22px}
  .prose li{margin:0 0 8px}
  .prose a,.faq a{color:var(--accent);text-underline-offset:2px}
  .tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 18px}
  .prose table{border-collapse:collapse;width:100%;font-size:15.5px}
  .prose th,.prose td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--border);vertical-align:top}
  .prose th{font-weight:700}
  .prose td.han{font-size:19px;white-space:nowrap}
  .prose td.rom{color:var(--accent);white-space:nowrap}
  .prose tbody tr:nth-child(odd){background:rgba(0,111,166,.04)}
  .tablehint{display:none;font-size:13px;color:var(--muted);margin:-8px 0 16px}
  /* Wide tables (4+ columns) become one card per row under 640px: a 5-column
     comparison table cannot be read by scrolling it sideways on a phone. */
  @media (max-width:640px){
    .prose table.stack thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
    .prose table.stack,.prose table.stack tbody,.prose table.stack tr,.prose table.stack td{display:block;width:100%}
    .prose table.stack tr{background:#fff !important;border:1px solid var(--border);border-radius:12px;
      padding:6px 12px;margin:0 0 12px}
    .prose table.stack td{border:0;padding:5px 0;white-space:normal}
    .prose table.stack td:first-child{font-weight:750;font-size:17px}
    .prose table.stack td:first-child::before{display:none}
    .prose table.stack td::before{content:attr(data-label);display:block;font-size:12px;font-weight:700;
      letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
    .tablewrap.scroll + .tablehint{display:block}
    .prose td.rom,.prose td.han{white-space:normal}
    .prose th,.prose td{padding:8px 8px}
  }
  .prose .callout{background:rgba(0,111,166,.07);border-left:3px solid var(--accent);
    border-radius:0 10px 10px 0;padding:12px 15px;margin:0 0 16px}
  .prose .callout p:last-child{margin-bottom:0}
  .shots{display:flex;flex-wrap:wrap;justify-content:center;gap:22px;margin:22px 0 26px}
  .shots figure{margin:0;flex:0 1 240px;text-align:center}
  .shots img{display:block;width:100%;max-width:240px;margin:0 auto;border-radius:26px;
    border:6px solid #0B2536;box-shadow:0 14px 34px rgba(0,40,70,.22);background:#fff}
  .shots figcaption{font-size:14px;color:var(--muted);margin-top:10px;line-height:1.45}
  .midcta{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
    background:#EAF5FB;border:1px solid var(--border);border-radius:16px;padding:16px 18px;margin:28px 0}
  .midcta b{display:block;font-size:17px}
  .midcta span.t{display:block;font-size:14.5px;color:var(--muted)}
  .midcta .cta,.prose a.cta,.endcta a.cta{box-shadow:none;color:#fff}
  .toolcta{display:block;text-decoration:none;color:inherit;background:#fff;
    border:1px solid var(--border);border-left:4px solid var(--accent);
    border-radius:0 14px 14px 0;padding:15px 18px;margin:26px 0}
  .toolcta:hover{box-shadow:0 6px 20px rgba(0,80,130,.10)}
  .toolcta b{display:block;font-size:16.5px;color:var(--accent);margin:0 0 4px}
  .toolcta span{display:block;font-size:14.5px;color:var(--muted);line-height:1.5}
  .toolcta em{font-style:normal;font-weight:700;color:var(--accent)}
  .steps{counter-reset:s;padding:0;margin:0 0 10px;list-style:none}
  .steps li{counter-increment:s;position:relative;padding:0 0 18px 46px;color:#26323b}
  .steps li::before{content:counter(s);position:absolute;left:0;top:-2px;width:30px;height:30px;border-radius:50%;
    background:var(--accent);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:15px}
  .faq{border-top:1px solid var(--border);padding:18px 0}
  .faq:last-of-type{border-bottom:1px solid var(--border)}
  .faq h3{margin:0 0 6px;font-size:18px;color:var(--fg)}
  .faq p{margin:0;color:#34414b}
  .endcta{text-align:center;background:#0B4F76;color:#fff;border-radius:20px;padding:26px 20px;margin:34px 0 8px}
  .endcta h2{color:#fff;margin:0 0 6px;font-size:23px}
  .endcta p{margin:0 0 16px}
  .related{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}
  .rcard{display:block;background:#fff;border:1px solid var(--border);border-radius:14px;padding:14px 16px;
    text-decoration:none;color:var(--fg);font-weight:650;transition:transform .12s;min-height:44px}
  .rcard:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,60,100,.08)}
  .rcard span{display:block;font-size:13.5px;color:var(--muted);font-weight:500;margin-top:3px}
  .toc{font-size:15px}
  .toc summary{cursor:pointer;font-weight:800;min-height:44px;display:flex;align-items:center;
    color:var(--fg);list-style-position:inside}
  .toc ol{margin:4px 0 0;padding-left:20px}
  .toc li{margin:0 0 6px}
  .toc a{color:var(--accent);text-decoration:none;padding:3px 0;line-height:1.7}
  .toc a:hover{text-decoration:underline}
  .gwrap.has-toc .toc{background:#fff;border:1px solid var(--border);border-radius:14px;padding:4px 16px 8px;margin:0 0 22px}
  @media (min-width:1100px){
    .gwrap.has-toc{max-width:1080px;display:grid;grid-template-columns:230px minmax(0,760px);gap:44px;
      justify-content:center}
    .gwrap.has-toc .toc{position:sticky;top:84px;align-self:start;max-height:calc(100vh - 110px);overflow:auto;margin:0}
  }
  .cat{margin:0 0 34px}
  .cat h2{margin:0 0 8px}
  .cat p{margin:0 0 14px;color:#2c3842}
  .langlist{display:flex;flex-wrap:wrap;gap:8px 18px;margin:6px 0 0}
  .langlist a{color:var(--accent)}
  @media(max-width:560px){.related{grid-template-columns:1fr}.hero h1{font-size:31px}.hero p.lede{font-size:17.5px}
    .gwrap{padding:26px 18px 32px}}
`;

const TOC_JS = `<script>(function(){var t=document.querySelector('details.toc');
if(t&&window.matchMedia('(min-width:1100px)').matches)t.open=true;})();</script>`;

function pageHead({ lang, title, desc, keywords, canonical, jsonld, alternates, ogType }) {
  const alt = (alternates || []).map(a =>
    `<link rel="alternate" hreflang="${a.hreflang}" href="${a.href}">`).join('\n');
  return `<!DOCTYPE html><html lang="${lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
${keywords ? `<meta name="keywords" content="${esc(keywords)}">` : ''}
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0B5F8A">
<meta name="apple-itunes-app" content="app-id=6764455741">
<link rel="canonical" href="${canonical}">
${alt}
<link rel="icon" type="image/png" href="/tova-icon.png">
<meta property="og:type" content="${ogType || 'article'}"><meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SITE}/og-image.png"><meta property="og:site_name" content="Tova Translate">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">${JSON.stringify(jsonld)}</script>
<style>${HEAD_CSS}</style></head><body>
<!--tv:header--><!--/tv:header-->`;
}
const PAGE_END = `<!--tv:footer--><!--/tv:footer--><!--zet-beacon--><script>(function(){try{var u="https://zet-scan.fly.dev/api/hit",d=JSON.stringify({p:"tovatranslate.app"+location.pathname,r:document.referrer||"",s:new URLSearchParams(location.search).get("src")||""});if(!(navigator.sendBeacon&&navigator.sendBeacon(u,new Blob([d],{type:"text/plain"}))))fetch(u,{method:"POST",body:d,keepalive:true,mode:"no-cors",headers:{"content-type":"text/plain"}});}catch(e){}})();</script></body></html>`;

const APPLE = `<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 12.5c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.7 3-.4 7.4 1.3 9.8.8 1.2 1.8 2.5 3.1 2.5 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9z"/></svg>`;
const ctaBtn = (ui) => `<a class="cta" href="${APP_STORE}" target="_blank" rel="noopener">${APPLE}` +
  `<span><small>${esc(ui.ctaSmall)}</small>${esc(ui.ctaBig)}</span></a>`;

/* Link context for a render: where guide and tool links should point. */
function linker(loc) {
  return (href) => {
    if (!loc) return { href, en: false };
    const g = href.match(/^\/translate\/([a-z0-9-]+)\/$/);
    if (g) {
      const has = I18N[loc.code].guides[g[1]];
      return has ? { href: `/${loc.code}/translate/${g[1]}/`, en: false } : { href, en: true };
    }
    if (/^\/tools\//.test(href)) return { href: `/${loc.code}${href}`, en: false };
    return { href, en: false };
  };
}

/* Minimal inline markup so the JSON stays readable: **bold** and [text](url).
 * Everything is escaped first, so this cannot inject markup from the data. */
function inlineWith(link, ui) {
  return (s) => esc(s)
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, text, href) => {
      const r = link(href);
      const mark = r.en && ui.englishOnly ? ` ${esc(ui.englishOnly)}` : '';
      return `<a href="${r.href}"${r.en ? ' hreflang="en"' : ''}>${text}${mark}</a>`;
    });
}

function renderTable(t, inline, ui) {
  const han = new Set(t.hanCols || []);
  const rom = new Set(t.romCols || []);
  const stack = t.head.length >= 4;
  const body = t.rows.map(r => '<tr>' + r.map((c, i) => {
    const cls = han.has(i) ? ' class="han"' : rom.has(i) ? ' class="rom"' : '';
    const lbl = stack ? ` data-label="${esc(t.head[i] || '')}"` : '';
    return `<td${cls}${lbl}>${inline(c)}</td>`;
  }).join('') + '</tr>').join('');
  return `<div class="tablewrap${stack ? '' : ' scroll'}"><table${stack ? ' class="stack"' : ''}><thead><tr>`
    + t.head.map(h => `<th scope="col">${esc(h)}</th>`).join('') + `</tr></thead><tbody>${body}</tbody></table></div>`
    + (stack ? '' : `<p class="tablehint">${esc(ui.tableHint)}</p>`);
}

function renderShots(items, plates) {
  return '<div class="shots">' + items.map(it => {
    const p = plates[it.plate] || PLATES[it.plate];
    const file = it.plate.replace(/_/g, '-');
    return `<figure><img src="/media/app/${file}.webp" width="${IMG_W}" height="${IMG_H}" loading="lazy" decoding="async" alt="${esc(p.alt)}">`
      + `<figcaption>${esc(it.caption || p.caption)}</figcaption></figure>`;
  }).join('') + '</div>';
}

/* Where the mid-page App Store CTA goes: after the first key section, i.e.
 * immediately before the second h2. */
function midCtaIndex(sections) {
  let n = 0;
  for (let i = 0; i < sections.length; i++) if (sections[i].h2 && ++n === 2) return i - 1;
  return sections.length - 1;
}

function renderBody(g, src, ctx) {
  const { inline, ui, plates } = ctx;
  const sections = src.sections || [];
  const imgsAfter = {};
  for (const im of g.images || []) (imgsAfter[im.after] = imgsAfter[im.after] || []).push(im);
  const mid = sections.length ? midCtaIndex(sections) : -1;
  const midHtml = `<div class="midcta"><div><b>${esc(ui.midCtaTitle)}</b><span class="t">${esc(ui.midCtaText)}</span></div>${ctaBtn(ui)}</div>`;
  const ids = new Set();
  let out = '';
  sections.forEach((sec, i) => {
    if (sec.h2) {
      let id = slugify(sec.h2); while (ids.has(id)) id += '-2'; ids.add(id);
      sec._id = id;
      out += `<h2 id="${id}">${esc(sec.h2)}</h2>`;
    }
    if (sec.h3) out += `<h3>${esc(sec.h3)}</h3>`;
    for (const para of sec.p || []) out += `<p>${inline(para)}</p>`;
    if (sec.callout) out += `<div class="callout"><p>${inline(sec.callout)}</p></div>`;
    if (sec.ul) out += '<ul>' + sec.ul.map(li => `<li>${inline(li)}</li>`).join('') + '</ul>';
    if (sec.ol) out += '<ol>' + sec.ol.map(li => `<li>${inline(li)}</li>`).join('') + '</ol>';
    if (sec.table) out += renderTable(sec.table, inline, ui);
    if (imgsAfter[i]) out += renderShots(imgsAfter[i], plates);
    if (i === mid) out += midHtml;
  });
  if (!sections.length) out += midHtml;
  return `<div class="prose">${out}</div>`;
}

function toc(src, ui) {
  const h2s = (src.sections || []).filter(s => s.h2);
  if (h2s.length < 5) return '';
  return `<details class="toc"><summary>${esc(ui.toc)}</summary><ol>`
    + h2s.map(s => `<li><a href="#${s._id}">${esc(s.h2)}</a></li>`).join('') + '</ol></details>';
}

function fmtDates(g, intl) {
  const d = (s, o) => new Date(s + 'T00:00:00Z').toLocaleDateString(intl, { timeZone: 'UTC', ...o });
  return {
    tested: d((g.tested || (g.updated || '').slice(0, 7)) + '-01', { month: 'long', year: 'numeric' }),
    updated: d(g.updated, { day: 'numeric', month: 'long', year: 'numeric' }),
  };
}

/* 4-6 related guides. Curated in _guides.json; padded from the same
 * region so a guide never ends on an empty block. */
function relatedFor(g) {
  const list = (g.related || []).filter(s => BY_SLUG[s] && s !== g.slug);
  for (const x of guides) {
    if (list.length >= 4) break;
    if (x.slug !== g.slug && !list.includes(x.slug)) list.push(x.slug);
  }
  return list.slice(0, 6);
}

function guideUrl(slug, loc) { return loc ? `${SITE}/${loc.code}/translate/${slug}/` : `${SITE}/translate/${slug}/`; }

function alternatesFor(slug) {
  const locs = ACTIVE.filter(l => I18N[l.code].guides[slug]);
  if (!locs.length) return [];
  return [
    { hreflang: 'x-default', href: guideUrl(slug) },
    { hreflang: 'en', href: guideUrl(slug) },
    ...locs.map(l => ({ hreflang: l.hreflang, href: guideUrl(slug, l) })),
  ];
}

function guidePage(g, loc) {
  const t = loc ? I18N[loc.code] : null;
  const src = t ? { ...g, ...t.guides[g.slug] } : g;
  const ui = t ? { ...EN_UI, ...t.ui } : EN_UI;
  const plates = t && t.plates ? { ...PLATES, ...t.plates } : PLATES;
  const link = linker(loc);
  const inline = inlineWith(link, ui);
  const url = guideUrl(g.slug, loc);
  const howto = (g.type || 'howto') === 'howto' && (src.steps || []).length;
  const hubUrl = SITE + '/translate/';
  const dates = fmtDates(g, loc ? loc.intl : 'en-GB');
  const body = renderBody(g, src, { inline, ui, plates });   // assigns section ids before toc()
  const tocHtml = toc(src, ui);

  const graph = [
    { "@type": "BreadcrumbList", "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + (loc ? `/${loc.code}/` : '/') },
      { "@type": "ListItem", "position": 2, "name": ui.guides, "item": hubUrl },
      { "@type": "ListItem", "position": 3, "name": src.breadcrumb, "item": url } ] },
    { "@type": "FAQPage", "mainEntity": src.faqs.map(f => (
      { "@type": "Question", "name": f.q, "acceptedAnswer": { "@type": "Answer", "text": f.a } })) },
    ...(howto ? [{ "@type": "HowTo", "name": src.h1, "step": src.steps.map((s, i) => (
      { "@type": "HowToStep", "position": i + 1, "text": s })) }] : []),
    { "@type": "Article", "@id": url + "#article", "headline": src.h1, "inLanguage": loc ? loc.lang : 'en',
      "dateModified": g.updated,
      "author": { "@type": "Organization", "name": "ZET Studios", "url": "https://zetstudios.ca/" },
      "publisher": { "@type": "Organization", "name": "ZET Studios", "url": "https://zetstudios.ca/" },
      "image": (g.images || []).map(im => `${SITE}/media/app/${im.plate.replace(/_/g, '-')}.webp`).concat([SITE + '/og-image.png']),
      "mainEntityOfPage": url },
    { "@type": "WebPage", "@id": url, "url": url, "name": src.title, "dateModified": g.updated,
      "isPartOf": { "@id": SITE + "/#site" }, "about": { "@id": SITE + "/#app" },
      "primaryImageOfPage": SITE + "/og-image.png" },
    { "@type": "MobileApplication", "@id": SITE + "/#app", "name": "Tova Translate",
      "operatingSystem": "iOS", "applicationCategory": "TravelApplication",
      "downloadUrl": APP_STORE, "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" } },
  ];

  const steps = howto ? `<div class="eyebrow">${esc(ui.howEyebrow)}</div><h2>${esc(ui.howH2)}</h2>`
    + `<ol class="steps">${src.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>` : '';
  const faqs = src.faqs.map(f => `<div class="faq"><h3>${esc(f.q)}</h3><p>${esc(f.a)}</p></div>`).join('');
  const tool = src.toolCta || g.toolCta;
  const toolHtml = tool ? `<a class="toolcta" href="${esc(link(g.toolCta.href).href)}"><b>${esc(tool.title)}</b>`
    + `<span>${inline(tool.text)} <em>→</em></span></a>` : '';
  const rel = relatedFor(g).map(s => {
    const lg = loc && I18N[loc.code].guides[s];
    const r = link(`/translate/${s}/`);
    const name = lg ? lg.breadcrumb : BY_SLUG[s].breadcrumb;
    const mark = r.en && ui.englishOnly ? ` ${ui.englishOnly}` : '';
    return `<a class="rcard" href="${r.href}"${r.en ? ' hreflang="en"' : ''}>${esc(name)}<span>${esc(ui.guideArrow)}${esc(mark)}</span></a>`;
  }).join('');
  const reassure = esc(ui.reassure).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  const home = loc ? `/${loc.code}/` : '/';

  return pageHead({ lang: loc ? loc.lang : 'en', title: src.title, desc: src.metaDesc, keywords: src.keywords,
      canonical: url, jsonld: { "@context": "https://schema.org", "@graph": graph }, alternates: alternatesFor(g.slug) })
    + `<div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="${home}">Tova</a> › <a href="/translate/">${esc(ui.guides)}</a> › ${esc(src.breadcrumb)}</nav>
<section class="hero"><h1>${esc(src.h1)}</h1>
<p class="byline">${esc(ui.byline.replace('{tested}', dates.tested).replace('{updated}', dates.updated))}</p>
<p class="lede">${esc(src.lede)}</p>
${ctaBtn(ui)}<p class="reassure">${reassure}</p></section></div>
<main class="band"><div class="gwrap${tocHtml ? ' has-toc' : ''}">${tocHtml}<article>
${steps}
${body}
${toolHtml}
<div class="eyebrow" style="margin-top:30px">${esc(ui.faqEyebrow)}</div><h2>${esc(ui.faqH2)}</h2>${faqs}
<div class="endcta"><h2>${esc(ui.midCtaTitle)}</h2><p>${esc(ui.midCtaText)}</p>${ctaBtn(ui)}</div>
<div class="eyebrow" style="margin-top:30px">${esc(ui.related)}</div>
<div class="related">${rel}</div>
</article></div></main>
${tocHtml ? TOC_JS : ''}`
    + PAGE_END;
}

/* ---------------------------------------------------------------- hub -- */
const HUB = [
  { h2: 'China: menus, signs, stations and getting online',
    p: 'Mainland China is where most translation apps quietly stop working, because Google’s services are filtered and the obvious app cannot reach its servers. Start with the tested comparison of which apps still work, then the offline setup that keeps you covered with no signal at all. The menu, sign and station guides teach you the forty-odd characters that do most of the work, with the pinyin to say them out loud.',
    slugs: ['best-translator-app-for-china', 'china-no-vpn', 'offline-translator-china', 'chinese-menu', 'chinese-signs', 'chinese-train-stations', 'read-chinese-characters', 'pinyin-camera-app'] },
  { h2: 'Cantonese: Hong Kong, Macau and Guangzhou',
    p: 'Cantonese uses mostly the same characters as Mandarin but reads them completely differently, so Mandarin pinyin on a Hong Kong menu is worse than no reading at all. The Jyutping guide explains the six tones, the Cantonese-only characters you will meet on signs, and how to read a menu board with the right romanisation.',
    slugs: ['cantonese-jyutping'] },
  { h2: 'Japan: menus, signs and romaji',
    p: 'Japanese mixes three scripts in a single sentence, and the same kanji can be read several ways depending on the word. These guides cover the menu words behind ticket machines and izakaya tables, the station and street signs you will actually meet, and how romaji works so you can say a place name to a taxi driver.',
    slugs: ['japanese-menu', 'japanese-signs', 'read-japanese-romaji'] },
  { h2: 'Korea: menus and signs',
    p: 'Hangul is an alphabet, so it is learnable in an afternoon, but a Hangul-only menu with no pictures is still a wall on your first night. The Korean guides cover the dish and cooking words that repeat across every menu, and the transit and street signs that get you to the right exit.',
    slugs: ['korean-menu', 'korean-signs'] },
  { h2: 'Conversations and handwriting',
    p: 'Some situations are not a sign on a wall. A meeting with people who speak three different languages, or a note written by hand, needs a different approach from pointing a camera at print. These two guides explain what works, and where it still fails.',
    slugs: ['three-way-conversation', 'translate-handwriting'] },
];

function hubPage() {
  const url = `${SITE}/translate/`;
  const all = HUB.flatMap(c => c.slugs);
  const missing = guides.filter(g => !all.includes(g.slug));
  if (missing.length) throw new Error('hub is missing guides: ' + missing.map(g => g.slug).join(', '));
  const jsonld = { "@context": "https://schema.org", "@graph": [
    { "@type": "CollectionPage", "@id": url, "url": url, "name": "Tova Translation Guides",
      "isPartOf": { "@id": SITE + "/#site" }, "about": { "@id": SITE + "/#app" } },
    { "@type": "BreadcrumbList", "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + "/" },
      { "@type": "ListItem", "position": 2, "name": "Translation guides", "item": url } ] },
    { "@type": "ItemList", "itemListElement": all.map((s, i) => (
      { "@type": "ListItem", "position": i + 1, "url": `${SITE}/translate/${s}/`, "name": BY_SLUG[s].breadcrumb })) } ] };
  const cats = HUB.map(c => `<section class="cat"><h2>${esc(c.h2)}</h2><p>${esc(c.p)}</p><div class="related">`
    + c.slugs.map(s => { const g = BY_SLUG[s];
      return `<a class="rcard" href="/translate/${s}/">${esc(g.breadcrumb)}<span>${esc(g.lede.length > 110 ? g.lede.slice(0, g.lede.lastIndexOf(' ', 107)) + '…' : g.lede)}</span></a>`; }).join('')
    + '</div></section>').join('');
  const tools = `<section class="cat"><h2>Free tools</h2><p>For text you can already copy, the browser tools do the same job as the camera: paste Chinese and get Hanyu Pinyin or Cantonese Jyutping above every character, with the right reading for characters that change pronunciation from word to word. They run in your browser and nothing you paste is uploaded.</p>
<div class="related"><a class="rcard" href="/tools/pinyin-converter/">Pinyin converter<span>Chinese characters to Hanyu Pinyin with tone marks.</span></a>
<a class="rcard" href="/tools/jyutping-converter/">Jyutping converter<span>Cantonese characters to Jyutping with tone numbers.</span></a></div></section>`;
  const byLoc = ACTIVE.map(l => {
    const gs = Object.keys(I18N[l.code].guides);
    return `<p><b lang="${l.lang}">${esc(nativeName(l.code))}</b>: ` + gs.map(s =>
      `<a href="/${l.code}/translate/${s}/" hreflang="${l.hreflang}" lang="${l.lang}">${esc(I18N[l.code].guides[s].breadcrumb)}</a>`).join(' · ') + '</p>';
  }).join('');
  const other = byLoc ? `<section class="cat"><h2>Guides in other languages</h2><p>Our four most-read China guides are also written in these languages.</p><div class="langblock">${byLoc}</div></section>` : '';
  return pageHead({
    lang: 'en', title: 'Travel Translation Guides: China, Japan & Korea | Tova',
    desc: 'Practical guides to reading menus, signs and stations in China, Hong Kong, Japan and Korea with your phone camera, offline and without a VPN in China.',
    keywords: 'translation guides, translate menu, translate signs, offline translator, China travel translator',
    canonical: url, jsonld, ogType: 'website' })
    + `<div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Tova</a> › Guides</nav>
<section class="hero"><h1>Translation guides for travel in Asia</h1>
<p class="lede">How to read the menu, the station sign and the note on the door when you cannot read the script. Every guide is written from testing on a real phone, and each one says where the app you are using, ours included, falls short.</p>
${ctaBtn(EN_UI)}</section></div>
<main class="band"><div class="gwrap">
<p>These guides are grouped by where you are going. If you are heading to mainland China, read the first two before you pack: they explain why the translator you already have may not work there, and what to download on home Wi-Fi so it does. Everywhere else, the menu and sign guides are the ones you will open at a table or on a platform.</p>
${cats}${tools}${other}
</div></main>`
    + PAGE_END;
}

const NATIVES = { it: 'Italiano', es: 'Español', de: 'Deutsch', fr: 'Français', ja: '日本語', ko: '한국어', 'zh-tw': '繁體中文', th: 'ไทย' };
function nativeName(c) { return NATIVES[c] || c; }

// ---- write ----
let written = 0;
for (const g of guides) {
  const dir = path.join(ROOT, g.slug);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), guidePage(g));
  written++;
}
fs.writeFileSync(path.join(ROOT, 'index.html'), hubPage());
written++;
for (const l of ACTIVE) {
  for (const slug of Object.keys(I18N[l.code].guides)) {
    if (!BY_SLUG[slug]) throw new Error(`${l.code}: unknown guide ${slug}`);
    const dir = path.join(ROOT, '..', l.code, 'translate', slug);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'index.html'), guidePage(BY_SLUG[slug], l));
    written++;
  }
}
console.log(`✓ translate: wrote ${written} pages (${guides.length} guides + hub + ${written - guides.length - 1} localized)`);
