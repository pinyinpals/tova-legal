/* Pinyin -> Thai script, following the Royal Institute rules for Mandarin as
 * published in ประกาศสำนักนายกรัฐมนตรี เรื่อง หลักเกณฑ์การทับศัพท์ภาษาจีนและภาษาฮินดี
 * (22 ธันวาคม 2549, ราชกิจจานุเบกษา เล่ม 124 ตอนพิเศษ 2 ง): 你好 หนี่เห่า,
 * 孔子 ขงจื่อ, 武汉 อู่ฮั่น, 国 กั๋ว, 月 เยฺว่, 云 ยฺหวิน.
 *
 * Used by the Thai pinyin converter only (loaded on /th/tools/pinyin-converter/)
 * and by ../build.js, which pre-renders the example. Plain ES5 so the same file
 * runs in the browser (window.TovaThai) and in Node (module.exports).
 *
 * How the rules work:
 *  - Tones map to Thai tones: 1 สามัญ, 2 จัตวา, 3 เอก, 4 โท, neutral = no mark.
 *  - Paired consonants (ผ/พ, ถ/ท, ข/ค, ห/ฮ, ฉ/ช, ส/ซ, ฝ/ฟ) and ห นำ are chosen so
 *    the Thai tone rules produce that tone.
 *  - Finals with two forms (–ัน/–าน, ไ–/–าย ...) use the first, short form: the
 *    rules allow either for tones 1–3 and require the short one for tone 4.
 *  - A glide ว/ย written after the initial gets พินทุ (ตฺวั้น, ซฺยง), except the
 *    native Thai clusters กว ขว คว; where ห นำ is needed it goes inside the
 *    cluster (นฺหวี่, ยฺหวิน).
 *  - y- syllables are ย + the written final (ยา, เยา, โยว, ยัง, หยิน), with the
 *    rules' own cases: yi = อี, ye = เย, yu/yue/yuan/yun use ü; yan is written
 *    as ian (เยียน), as in established spellings such as 严 เหยียน.
 *  - The third-tone sandhi is not applied to the spelling (ขงจื่อ keeps เอก).
 * Thai is shown next to the pinyin, never instead of it.
 */
(function (root) {
  'use strict';

  var MID = 'mid', HIGH = 'high', LOW = 'low', SON = 'son';
  // Initial -> [class, letter, high-class partner for paired low letters]
  var INITIALS = {
    b: [MID, 'ป'], d: [MID, 'ต'], g: [MID, 'ก'], j: [MID, 'จ'], z: [MID, 'จ'], zh: [MID, 'จ'],
    p: [LOW, 'พ', 'ผ'], t: [LOW, 'ท', 'ถ'], k: [LOW, 'ค', 'ข'], h: [LOW, 'ฮ', 'ห'],
    q: [LOW, 'ช', 'ฉ'], ch: [LOW, 'ช', 'ฉ'], sh: [LOW, 'ช', 'ฉ'], c: [LOW, 'ช', 'ฉ'],
    x: [LOW, 'ซ', 'ส'], s: [LOW, 'ซ', 'ส'], f: [LOW, 'ฟ', 'ฝ'],
    m: [SON, 'ม'], n: [SON, 'น'], l: [SON, 'ล'], r: [SON, 'ร'], y: [SON, 'ย'], w: [SON, 'ว'],
    '': [MID, 'อ']
  };
  var INIT_RE = /^(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?(.*)$/;

  // Final -> { g: glide letter in the onset, lead: vowel written before the onset,
  //            above: vowel sign on the last onset letter, tail: rest, dead: short open }
  function F(g, lead, above, tail) { return { g: g, lead: lead, above: above, tail: tail }; }
  var FINALS = {
    a: F('', '', '', 'า'), ai: F('', 'ไ', '', ''), an: F('', '', 'ั', 'น'),
    ang: F('', '', 'ั', 'ง'), ao: F('', 'เ', '', 'า'),
    e: F('', 'เ', '', 'อ'), ei: F('', 'เ', '', 'ย์'), en: F('', 'เ', 'ิ', 'น'),
    eng: F('', 'เ', 'ิ', 'ง'), er: F('', 'เ', '', 'อร์'),
    i: F('', '', 'ี', ''), ia: F('', 'เ', 'ี', 'ย'), ie: F('', 'เ', 'ี', 'ย'),
    ian: F('', 'เ', 'ี', 'ยน'), iang: F('', 'เ', 'ี', 'ยง'), iao: F('', 'เ', 'ี', 'ยว'),
    'in': F('', '', 'ิ', 'น'), ing: F('', '', 'ิ', 'ง'), iong: F('ย', '', '', 'ง'),
    iu: F('', '', 'ิ', 'ว'), o: F('', 'โ', '', ''), ong: F('', '', '', 'ง'),
    ou: F('', 'โ', '', 'ว'), u: F('', '', 'ู', ''),
    ua: F('ว', '', '', 'า'), uai: F('ว', 'ไ', '', ''), uan: F('ว', '', 'ั', 'น'),
    uang: F('ว', '', 'ั', 'ง'), ueng: F('', 'เ', 'ิ', 'ง'),
    ui: F('', '', 'ุ', 'ย'), un: F('', '', 'ุ', 'น'), uo: F('', '', 'ั', 'ว'),
    'ü': F('ว', '', 'ี', ''), 'üe': F('ว', 'เ', '', ''), 'üan': F('ว', 'เ', 'ี', 'ยน'),
    'ün': F('ว', '', 'ิ', 'น')
  };
  var RETROFLEX = { z: 1, c: 1, s: 1, zh: 1, ch: 1, sh: 1, r: 1 };
  var NATIVE_CLUSTER = { 'ก': 1, 'ข': 1, 'ค': 1 };   // กว ขว คว need no พินทุ
  var MARKS = { 1: '', 2: '๋', 3: '่', 4: '้' };  // on a mid-class letter
  var EK = '่', PINTHU = 'ฺ';

  // "lǜ" -> { base: "lü", tone: 4 }; a trailing digit (ni3) is accepted too.
  function parse(s) {
    var tone = 0;
    var d = s.normalize('NFD').toLowerCase();
    var out = '';
    for (var i = 0; i < d.length; i++) {
      var c = d[i];
      if (c === '̄') tone = 1;
      else if (c === '́') tone = 2;
      else if (c === '̌') tone = 3;
      else if (c === '̀') tone = 4;
      else out += c;
    }
    out = out.normalize('NFC').replace(/v/g, 'ü');
    var m = out.match(/^([a-zü]+)([0-5])?$/);
    if (!m) return null;
    if (m[2]) tone = +m[2] % 5;
    return { base: m[1], tone: tone };
  }

  function split(base) {
    var m = base.match(INIT_RE);
    var ini = m[1] || '', fin = m[2];
    if (!fin && ini !== 'ng') return null;
    // Spelling conventions back to the underlying final.
    if (ini === 'y') {
      if (fin === 'i' || fin === 'in' || fin === 'ing') { if (fin === 'i') ini = ''; }
      else if (fin === 'u' || fin === 'ue' || fin === 'uan' || fin === 'un') fin = 'ü' + fin.slice(1);
      else if (fin === 'e') return { ini: 'y', fin: 'e', yE: true };
      else if (fin === 'an') fin = 'ian';
    } else if (ini === 'w') {
      if (fin === 'u') ini = '';
      else if (fin === 'o') fin = 'uo';
      else if (fin === 'ei') fin = 'ei';
      else if (fin === 'en') fin = 'en';
    } else if (/^[jqx]$/.test(ini) && fin[0] === 'u') {
      fin = 'ü' + fin.slice(1);
    } else if ((ini === 'b' || ini === 'p' || ini === 'm' || ini === 'f') && fin === 'o') {
      fin = 'uo';
    } else if (ini === 'n' || ini === 'l') {
      if (fin === 'üe' || fin === 'ue') fin = 'üe';
    }
    if (fin === 'iou') fin = 'iu';
    if (fin === 'uei') fin = 'ui';
    if (fin === 'uen') fin = 'un';
    return { ini: ini, fin: fin };
  }

  function syllable(reading) {
    var p = parse(reading || '');
    if (!p) return null;
    var sp = split(p.base);
    if (!sp) return null;
    var tone = p.tone, ini = sp.ini, fin = sp.fin;
    var f;
    if (sp.yE) f = F('', 'เ', '', '');                       // ye -> เย
    else if (fin === 'i' && RETROFLEX[ini]) f = tone ? F('', '', 'ื', 'อ') : F('', '', 'ึ', '');
    else if (fin === 'a' && !tone) f = F('', '', '', 'ะ');
    else f = FINALS[fin];
    if (!f) return null;
    var dead = (f.tail === 'ะ' || f.above === 'ึ');
    if (fin === 'er' && ini) return null;                     // er only stands alone

    var I = INITIALS[ini];
    if (!I) return null;
    var cls = I[0], letter = I[1], ho = false, mark = '';
    var t = tone || (dead ? 3 : 1);                           // neutral: light, short
    if (!tone && !dead) t = 1;
    if (cls === MID) {
      mark = tone ? MARKS[tone] : '';
    } else if (cls === LOW) {
      if (t === 1) { mark = ''; }
      else if (t === 2) { letter = I[2]; }
      else if (t === 3) { letter = I[2]; mark = EK; }
      else { mark = EK; }
      if (!tone) mark = '';
    } else {                                                 // sonorant: ห นำ when needed
      if (t === 2 || t === 3) ho = true;
      if (tone === 3 || tone === 4) mark = EK;
    }

    // Onset: initial [+ พินทุ] [+ ห นำ inside a cluster] [+ glide]
    var onset;
    if (f.g) {
      if (f.g === 'ว' && NATIVE_CLUSTER[letter]) onset = letter + f.g;   // กวา, ไคว่
      else onset = letter + PINTHU + (ho ? 'ห' : '') + f.g;            // ตฺวั้น, นฺหวี่
    } else {
      onset = (ho ? 'ห' : '') + letter;
    }
    return f.lead + onset + f.above + mark + f.tail;
  }

  // A whole run of tone-marked pinyin syllables separated by spaces.
  function line(readings) {
    return readings.map(function (r) { return syllable(r) || r; }).join('');
  }

  var api = { syllable: syllable, line: line };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TovaThai = api;
})(this);
