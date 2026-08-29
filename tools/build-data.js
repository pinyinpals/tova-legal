#!/usr/bin/env node
/*
 * Regenerates the tool dictionaries in lib/ from two upstream sources.
 *
 *   node build-data.js          # uses cached _data/, downloads if absent
 *   node build-data.js --fresh  # force re-download
 *
 * SOURCES (both redistributable, both attributed on the tool page):
 *   1. Unicode Unihan `kCantonese` — one authoritative preferred reading per
 *      character, ~30k characters. Unicode License (attribution).
 *   2. CanCLID rime-cantonese — full reading sets per character AND a
 *      word-level lexicon. CC-BY 4.0.
 *
 * WHY BOTH: Unihan gives one reading and never says which alternates exist.
 * rime gives every reading but its weights are coarse (0%/3%/5%) and do not
 * rank reliably — 行 has four readings all tagged 5%. So Unihan picks the
 * primary, rime supplies the alternates, and rime's word list fixes the
 * cases where reading a word character-by-character gives the wrong answer
 * (銀行 is ngan4 hong4, not ngan4 hang4).
 *
 * OUTPUT — split into two tiers so the page is usable before the whole
 * dictionary has arrived. The full set is ~465KB gzipped, which is eleven
 * seconds on a 3G connection before the user can type a single character.
 *
 *   jyutping-core.json  {p:{char:reading}, a:{char:[alts]}}  ~38KB gz
 *       The ~5,600 characters that actually occur in the modern Cantonese
 *       word lexicon. Blocking: the input box unlocks when this lands.
 *   jyutping-full.json  {p:{...}, a:{...}, w:{word:"r1 r2"}} ~427KB gz
 *       Rare characters plus the whole word list. Loaded in the background
 *       and merged in; the page re-renders once it arrives, upgrading
 *       character-level readings to word-level ones.
 *
 *   The word list holds ONLY words where
 *                          character-by-character lookup is wrong. Words the
 *                          naive path already gets right are dropped; storing
 *                          them would just be dead weight.
 *   t2s.json               {traditional: simplified}   — used by the PINYIN
 *                          tool. pinyin-pro's phrase dictionary is
 *                          simplified-only, so traditional input silently
 *                          loses polyphone disambiguation (音樂 comes back
 *                          "yin le" instead of "yin yue"). We look the phrase
 *                          up in simplified and paint the readings back over
 *                          the original traditional characters. The mapping is
 *                          1 char -> 1 char, so alignment is preserved.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DATA = path.join(__dirname, '_data');
const OUT = path.join(__dirname, 'lib');
const FRESH = process.argv.includes('--fresh');

const SRC = {
  unihan: 'https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip',
  chars: 'https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.chars.dict.yaml',
  words: 'https://raw.githubusercontent.com/rime/rime-cantonese/main/jyut6ping3.words.dict.yaml',
};

fs.mkdirSync(DATA, { recursive: true });

function fetchTo(url, file) {
  const dest = path.join(DATA, file);
  if (fs.existsSync(dest) && !FRESH) { console.log(`· cached ${file}`); return dest; }
  console.log(`↓ ${url}`);
  execFileSync('curl', ['-sSL', '--max-time', '180', '-o', dest, url], { stdio: 'inherit' });
  return dest;
}

// ---------------------------------------------------------------- sources
const zip = fetchTo(SRC.unihan, 'Unihan.zip');
const readingsTxt = path.join(DATA, 'Unihan_Readings.txt');
const variantsTxt = path.join(DATA, 'Unihan_Variants.txt');
for (const f of [readingsTxt, variantsTxt]) {
  if (!fs.existsSync(f) || FRESH) {
    execFileSync('unzip', ['-o', '-q', zip, path.basename(f), '-d', DATA]);
  }
}
const charsYaml = fetchTo(SRC.chars, 'jyut6ping3.chars.dict.yaml');
const wordsYaml = fetchTo(SRC.words, 'jyut6ping3.words.dict.yaml');

// ------------------------------------------- 1. Unihan authoritative primary
const unihan = Object.create(null);
for (const line of fs.readFileSync(readingsTxt, 'utf8').split('\n')) {
  if (!line || line[0] === '#') continue;
  const [cp, field, val] = line.split('\t');
  if (field !== 'kCantonese') continue;
  unihan[String.fromCodePoint(parseInt(cp.slice(2), 16))] = val.trim().split(/\s+/)[0];
}

// ------------------------------------------------- 2. rime full reading sets
const readings = Object.create(null); // char -> [{r, w, hasW}]
for (const line of fs.readFileSync(charsYaml, 'utf8').split('\n')) {
  if (!line || line[0] === '#' || !line.includes('\t')) continue;
  const [ch, r, w] = line.split('\t');
  if (!ch || !r || [...ch].length !== 1) continue;
  (readings[ch] ||= []).push({ r: r.trim(), w: w ? parseInt(w) || 0 : -1, hasW: !!w });
}

// ------------------------------------------------------------ 3. merge
const primary = Object.create(null);
const alts = Object.create(null);
const stat = { unihan: 0, unihanOnly: 0, unweighted: 0, weight: 0 };

for (const ch of new Set([...Object.keys(readings), ...Object.keys(unihan)])) {
  const rs = readings[ch] || [];
  const set = rs.map(x => x.r);
  let p;
  // Unihan always wins when it has a reading. rime is a traditional-character
  // lexicon and files some simplified forms under their archaic radical
  // reading — its base entry for 广 is am1 (the "shelter" radical), not the
  // gwong2 that anyone typing 广东话 means. Unihan carries the modern reading
  // for both script variants, so it is the primary and rime supplies alternates.
  if (unihan[ch]) {
    p = unihan[ch];
    set.length ? stat.unihan++ : stat.unihanOnly++;
  } else {
    // rime marks the base reading by omitting the weight column
    const bare = rs.filter(x => !x.hasW);
    if (bare.length === 1) { p = bare[0].r; stat.unweighted++; }
    else { p = rs.slice().sort((a, b) => b.w - a.w)[0]?.r; stat.weight++; }
  }
  if (!p) continue;
  primary[ch] = p;
  const others = [...new Set(set)].filter(r => r !== p);
  if (others.length) alts[ch] = others;
}

// ------------------------------- 4. traditional -> simplified character map
const t2s = Object.create(null);
for (const line of fs.readFileSync(variantsTxt, 'utf8').split('\n')) {
  if (!line || line[0] === '#') continue;
  const [cp, field, val] = line.split('\t');
  if (field !== 'kSimplifiedVariant') continue;
  const trad = String.fromCodePoint(parseInt(cp.slice(2), 16));
  // 64 entries list several targets; the first is the standard one
  const simp = String.fromCodePoint(parseInt(val.trim().split(/\s+/)[0].slice(2), 16));
  if (trad !== simp) t2s[trad] = simp;
}

// ------------------------------- 5. words, keeping ONLY the informative ones
const words = Object.create(null);
let scanned = 0, kept = 0, alias = 0, collide = 0;
for (const line of fs.readFileSync(wordsYaml, 'utf8').split('\n')) {
  if (!line || line[0] === '#' || !line.includes('\t')) continue;
  const [w, r] = line.split('\t');
  if (!w || !r) continue;
  const chars = [...w];
  if (chars.length < 2 || chars.length > 6) continue;
  scanned++;
  const actual = r.trim();
  if (chars.some(c => !primary[c])) continue;
  if (actual.split(' ').length !== chars.length) continue;
  if (chars.map(c => primary[c]).join(' ') === actual) continue; // naive is right
  if (!(w in words)) { words[w] = actual; kept++; }

  // rime is written in traditional characters, so 銀行 is listed but 银行 is
  // not — simplified input would get no word-level disambiguation at all.
  // Traditional -> simplified is 1 char -> 1 char, so the simplified form can
  // be registered at build time and the runtime stays a plain lookup.
  const simp = chars.map(c => t2s[c] || c).join('');
  if (simp !== w) {
    if (!(simp in words)) { words[simp] = actual; alias++; }
    else if (words[simp] !== actual) collide++;
  }
}

// ------------------------------------------------------------------- write
fs.mkdirSync(OUT, { recursive: true });
// A character earns a place in the core tier by appearing in the modern word
// lexicon and living in the base CJK block. Everything else — historic forms,
// rare surnames, the Unicode extension planes — can arrive late.
const inWords = new Set();
for (const w of Object.keys(words)) for (const c of w) inWords.add(c);
const isCore = (c) => {
  const cp = c.codePointAt(0);
  return cp >= 0x4E00 && cp <= 0x9FFF && inWords.has(c);
};

const core = { p: {}, a: {} };
const full = { p: {}, a: {}, w: words };
for (const [c, r] of Object.entries(primary)) (isCore(c) ? core.p : full.p)[c] = r;
for (const [c, r] of Object.entries(alts)) (isCore(c) ? core.a : full.a)[c] = r;

const files = {
  'jyutping-core.json': core,
  'jyutping-full.json': full,
  't2s.json': t2s,
};
for (const [name, obj] of Object.entries(files)) {
  fs.writeFileSync(path.join(OUT, name), JSON.stringify(obj));
}

console.log(`\ncharacters : ${Object.keys(primary).length} ` +
  `(unihan ${stat.unihan}, unihan-only ${stat.unihanOnly}, rime-base ${stat.unweighted}, by-weight ${stat.weight})`);
console.log(`polyphones : ${Object.keys(alts).length}`);
console.log(`words      : ${kept} informative of ${scanned} scanned, +${alias} simplified aliases (${collide} collisions skipped)`);
console.log(`trad->simp : ${Object.keys(t2s).length}`);
console.log(`core tier  : ${Object.keys(core.p).length} characters (unlocks the input)`);
const zlib = require('zlib');
for (const name of Object.keys(files)) {
  const buf = fs.readFileSync(path.join(OUT, name));
  console.log(`  lib/${name} — ${(buf.length / 1024).toFixed(0)}KB raw, ` +
    `${(zlib.gzipSync(buf).length / 1024).toFixed(0)}KB gzipped`);
}
