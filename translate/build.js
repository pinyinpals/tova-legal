#!/usr/bin/env node
/*
 * Tova programmatic SEO/GEO page generator.
 *
 * Reads ./_guides.json and writes one static landing page per high-intent
 * query into ./<slug>/index.html, plus a hub index at ./index.html.
 *
 * Each page is built for BOTH Google and AI answer engines (GEO):
 *   - Visible question→answer blocks that mirror the FAQPage JSON-LD exactly
 *     (Google drops the rich result on mismatch; AI engines quote the text).
 *   - BreadcrumbList + FAQPage + a reference to the site's MobileApplication.
 *   - Internal cross-links (guide ↔ guide ↔ hub ↔ homepage) + a portfolio
 *     link to ZET Studios — our own free "backlink network".
 *
 * To add a page: append an object to _guides.json and run `node build.js`.
 * Then add the new URL to ../sitemap.xml (this script prints the block to paste).
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const SITE = 'https://tovatranslate.app';
const APP_STORE = 'https://apps.apple.com/us/app/tova-translate/id6764455741';
const guides = JSON.parse(fs.readFileSync(path.join(ROOT, '_guides.json'), 'utf8'));

const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

const HEAD_CSS = `
  :root{--bg:#22A8E0;--top:#46C0EE;--bot:#1090CC;--fg:#111418;--muted:#5f6c76;
    --accent:#0090D0;--card:#fff;--band:#FAFCFD;--border:rgba(0,144,208,.18)}
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
  .hero{padding:28px 0 8px}
  .hero h1{font-size:38px;line-height:1.12;font-weight:800;letter-spacing:-.025em;margin:10px 0 14px}
  .hero p.lede{font-size:19px;opacity:.94;margin:0 0 22px;max-width:620px}
  .cta{display:inline-flex;align-items:center;gap:11px;background:#0B2536;color:#fff;text-decoration:none;
    padding:13px 20px;border-radius:14px;font-weight:700;box-shadow:0 10px 30px rgba(8,30,48,.35)}
  .cta:hover{filter:brightness(1.12)}
  .cta small{display:block;font-size:10px;opacity:.7;font-weight:600;text-transform:uppercase;letter-spacing:.08em}
  .cta span{font-size:17px;line-height:1}
  .reassure{font-size:13.5px;opacity:.9;margin:14px 0 0}
  .reassure b{font-weight:700}
  .band{background:var(--band);color:var(--fg);border-radius:26px 26px 0 0;margin-top:34px;
    box-shadow:inset 0 1px 0 rgba(0,0,0,.04)}
  .band .wrap{padding:34px 22px}
  .eyebrow{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
  h2{font-size:26px;font-weight:800;letter-spacing:-.02em;margin:8px 0 18px;color:var(--fg)}
  .steps{counter-reset:s;padding:0;margin:0;list-style:none}
  .steps li{counter-increment:s;position:relative;padding:0 0 18px 46px;color:#26323b}
  .steps li::before{content:counter(s);position:absolute;left:0;top:-2px;width:30px;height:30px;border-radius:50%;
    background:var(--accent);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:15px}
  .faq{border-top:1px solid var(--border);padding:18px 0}
  .faq:last-child{border-bottom:1px solid var(--border)}
  .faq h3{margin:0 0 6px;font-size:18px;color:var(--fg)}
  .faq p{margin:0;color:#3a4751}
  .related{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}
  @media(max-width:560px){.related{grid-template-columns:1fr}.hero h1{font-size:30px}}
  .rcard{display:block;background:#fff;border:1px solid var(--border);border-radius:14px;padding:14px 16px;
    text-decoration:none;color:var(--fg);font-weight:600;transition:transform .12s}
  .rcard:hover{transform:translateY(-2px)}
  .rcard span{display:block;font-size:12px;color:var(--muted);font-weight:500;margin-top:3px}
  footer{color:#fff;padding:26px 22px 40px;text-align:center;font-size:13px;opacity:.92}
  footer a{text-decoration:none}
  footer .frow{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:10px}
  .portfolio{font-size:12.5px;opacity:.8;margin-top:8px}
`;

function pageHead({ title, desc, keywords, canonical, jsonld }) {
  return `<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="keywords" content="${esc(keywords)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0090D0">
<meta name="apple-itunes-app" content="app-id=6764455741">
<link rel="canonical" href="${canonical}">
<link rel="icon" type="image/png" href="/tova-icon.png">
<meta property="og:type" content="article"><meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${canonical}">
<meta property="og:image" content="${SITE}/og-image.png"><meta property="og:site_name" content="Tova Translate">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">${JSON.stringify(jsonld)}</script>
<style>${HEAD_CSS}</style></head><body>`;
}

const topbar = `<div class="topbar"><a href="/" style="display:flex;align-items:center;gap:10px">
<img src="/tova-icon.png" alt="Tova Translate icon"><b>Tova Translate</b></a></div>`;

const ctaBtn = `<a class="cta" href="${APP_STORE}" target="_blank" rel="noopener">
<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 12.5c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.7 3-.4 7.4 1.3 9.8.8 1.2 1.8 2.5 3.1 2.5 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9z"/></svg>
<span><small>Download on the</small>App Store</span></a>`;

function footer(related) {
  const rel = related.map(g => `<a class="rcard" href="/translate/${g.slug}/">${esc(g.breadcrumb)}<span>Guide →</span></a>`).join('');
  return `</div></section>
<section class="band" style="background:transparent;color:#fff;box-shadow:none;margin-top:4px"><div class="wrap">
<div class="eyebrow" style="color:rgba(255,255,255,.85)">More translation guides</div>
<div class="related">${rel}</div></div></section>
<footer><div class="frow">
<a href="/">Home</a><a href="/translate/">All guides</a><a href="/faq/">FAQ</a>
<a href="/learn/">Tova Learn</a><a href="/support">Support</a><a href="/privacy">Privacy</a>
<a href="${APP_STORE}" target="_blank" rel="noopener">App Store</a></div>
<div class="portfolio">A <a href="https://zetstudios.ca/apps/tova/">ZET Studios</a> app · Free download · No sign-up · Works in China, no VPN</div>
</footer></body></html>`;
}

function guidePage(g, all) {
  const url = `${SITE}/translate/${g.slug}/`;
  const related = all.filter(x => x.slug !== g.slug).slice(0, 4);
  const jsonld = {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "BreadcrumbList", "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + "/" },
        { "@type": "ListItem", "position": 2, "name": "Translation guides", "item": SITE + "/translate/" },
        { "@type": "ListItem", "position": 3, "name": g.breadcrumb, "item": url } ] },
      { "@type": "FAQPage", "mainEntity": g.faqs.map(f => (
        { "@type": "Question", "name": f.q, "acceptedAnswer": { "@type": "Answer", "text": f.a } })) },
      { "@type": "HowTo", "name": g.h1, "step": g.steps.map((s, i) => (
        { "@type": "HowToStep", "position": i + 1, "text": s })) },
      { "@type": "WebPage", "@id": url, "url": url, "name": g.title,
        "isPartOf": { "@id": SITE + "/#site" },
        "about": { "@id": SITE + "/#app" },
        "primaryImageOfPage": SITE + "/og-image.png" },
      { "@type": "MobileApplication", "@id": SITE + "/#app", "name": "Tova Translate",
        "operatingSystem": "iOS", "applicationCategory": "TravelApplication",
        "downloadUrl": APP_STORE, "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" } }
    ]
  };
  const steps = g.steps.map(s => `<li>${esc(s)}</li>`).join('');
  const faqs = g.faqs.map(f => `<div class="faq"><h3>${esc(f.q)}</h3><p>${esc(f.a)}</p></div>`).join('');
  return pageHead({ title: g.title, desc: g.metaDesc, keywords: g.keywords, canonical: url, jsonld })
    + topbar
    + `<div class="wrap"><div class="crumbs"><a href="/">Tova</a> › <a href="/translate/">Guides</a> › ${esc(g.breadcrumb)}</div>
<section class="hero"><h1>${esc(g.h1)}</h1><p class="lede">${esc(g.lede)}</p>
${ctaBtn}<p class="reassure"><b>Free</b> · No sign-up · Works offline in China — no VPN</p></section></div>
<section class="band"><div class="wrap">
<div class="eyebrow">How it works</div><h2>Read it in three steps</h2><ol class="steps">${steps}</ol>
<div class="eyebrow" style="margin-top:26px">Common questions</div><h2>About this guide</h2>${faqs}
<div style="margin-top:26px">${ctaBtn}</div>`
    + footer(related);
}

function hubPage(all) {
  const url = `${SITE}/translate/`;
  const jsonld = {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "CollectionPage", "@id": url, "url": url, "name": "Tova Translation Guides",
        "isPartOf": { "@id": SITE + "/#site" }, "about": { "@id": SITE + "/#app" } },
      { "@type": "BreadcrumbList", "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Tova Translate", "item": SITE + "/" },
        { "@type": "ListItem", "position": 2, "name": "Translation guides", "item": url } ] },
      { "@type": "ItemList", "itemListElement": all.map((g, i) => (
        { "@type": "ListItem", "position": i + 1, "url": `${SITE}/translate/${g.slug}/`, "name": g.breadcrumb })) }
    ]
  };
  const cards = all.map(g => `<a class="rcard" href="/translate/${g.slug}/">${esc(g.breadcrumb)}<span>${esc(g.lede.slice(0, 88))}…</span></a>`).join('');
  return pageHead({
    title: "Tova Translation Guides — Menus, Signs & Offline Travel",
    desc: "Step-by-step guides for translating Chinese, Cantonese, Japanese, and Korean menus and signs with your phone camera — offline, no VPN.",
    keywords: "translation guides, translate menu, translate signs, offline translator, China travel translator",
    canonical: url, jsonld
  })
    + topbar
    + `<div class="wrap"><div class="crumbs"><a href="/">Tova</a> › Guides</div>
<section class="hero"><h1>Translation guides</h1>
<p class="lede">Quick how-tos for reading menus and signs across Asia with your camera — each works offline in China with no VPN.</p>
${ctaBtn}</section></div>
<section class="band"><div class="wrap"><div class="eyebrow">Pick your situation</div><h2>All guides</h2>
<div class="related">${cards}</div></div></section>
<footer><div class="frow"><a href="/">Home</a><a href="/faq/">FAQ</a><a href="/learn/">Tova Learn</a>
<a href="/support">Support</a><a href="/privacy">Privacy</a><a href="${APP_STORE}" target="_blank" rel="noopener">App Store</a></div>
<div class="portfolio">A <a href="https://zetstudios.ca/apps/tova/">ZET Studios</a> app · Free download · Works in China, no VPN</div></footer></body></html>`;
}

// ---- write ----
let written = 0;
for (const g of guides) {
  const dir = path.join(ROOT, g.slug);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), guidePage(g, guides));
  written++;
}
fs.writeFileSync(path.join(ROOT, 'index.html'), hubPage(guides));
written++;

// ---- print sitemap block to paste into ../sitemap.xml ----
const today = new Date().toISOString().slice(0, 10);
const smHub = `  <url><loc>${SITE}/translate/</loc><lastmod>${today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>`;
const smGuides = guides.map(g =>
  `  <url><loc>${SITE}/translate/${g.slug}/</loc><lastmod>${today}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>`).join('\n');

console.log(`✓ wrote ${written} pages (${guides.length} guides + 1 hub)`);
console.log('\n--- paste into ../sitemap.xml before </urlset> ---\n');
console.log(smHub + '\n' + smGuides + '\n');
