#!/usr/bin/env node
/*
 * Submits every URL in ../sitemap.xml to IndexNow.
 *
 *   node indexnow.js            # submit all sitemap URLs
 *   node indexnow.js <url>...   # submit specific URLs
 *
 * IndexNow is a push protocol accepted by Bing, Yandex, Seznam and Naver —
 * one POST tells them what changed instead of waiting to be crawled. Google
 * does not participate, so this is additive to Search Console, not a
 * replacement. It matters here because Bing's index is what several AI answer
 * engines read from, and these tool pages are written to be cited.
 *
 * Ownership is proved by hosting <key>.txt at the site root containing the
 * key. Keep that file deployed or submissions start failing.
 */
const fs = require('fs');
const path = require('path');

const HOST = 'tovatranslate.app';
const KEY = fs.readdirSync(__dirname).find(f => /^[0-9a-f]{32}\.txt$/.test(f))?.replace('.txt', '');
if (!KEY) { console.error('No <key>.txt at the repo root — cannot prove ownership.'); process.exit(1); }

let urls = process.argv.slice(2);
if (!urls.length) {
  const xml = fs.readFileSync(path.join(__dirname, 'sitemap.xml'), 'utf8');
  urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].trim());
}
if (!urls.length) { console.error('nothing to submit'); process.exit(1); }

const body = JSON.stringify({
  host: HOST,
  key: KEY,
  keyLocation: `https://${HOST}/${KEY}.txt`,
  urlList: urls,
});

fetch('https://api.indexnow.org/indexnow', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body,
}).then(async r => {
  // 200 accepted, 202 accepted but key still being validated
  console.log(`IndexNow -> ${r.status} ${r.statusText}  (${urls.length} urls)`);
  const t = await r.text();
  if (t.trim()) console.log(t.slice(0, 300));
  if (r.status === 403) console.error('403 = key file not reachable at ' + `https://${HOST}/${KEY}.txt`);
  process.exit(r.status === 200 || r.status === 202 ? 0 : 1);
}).catch(e => { console.error(e.message); process.exit(1); });
