/* Pinyin -> Hangul, following the National Institute of Korean Language's
 * 외래어 표기법 for Chinese (the 주음 부호와 한글 대조표). This is the spelling
 * Korean newspapers and maps use: 北京 베이징, 四川 쓰촨, 习近平 시진핑.
 *
 * Used by the Korean pinyin converter only (loaded on /ko/tools/pinyin-converter/)
 * and by ../build.js, which pre-renders the example. Plain ES5 so the same file
 * runs in the browser (window.TovaHangul) and in Node (module.exports).
 *
 * Hangul cannot carry tones and merges some sounds (zh/j both ㅈ), so the page
 * always shows it next to the pinyin, never instead of it.
 */
(function (root) {
  'use strict';

  // Compatibility jamo -> index in the Unicode syllable formula.
  var CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
  var JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ';
  var JONG = { '': 0, 'ㄴ': 4, 'ㄹ': 8, 'ㅇ': 21 };

  function syl(cho, jung, jong) {
    return String.fromCharCode(0xAC00 +
      (CHO.indexOf(cho) * 21 + JUNG.indexOf(jung)) * 28 + JONG[jong || '']);
  }

  var INITIALS = {
    b: 'ㅂ', p: 'ㅍ', m: 'ㅁ', f: 'ㅍ', d: 'ㄷ', t: 'ㅌ', n: 'ㄴ', l: 'ㄹ',
    g: 'ㄱ', k: 'ㅋ', h: 'ㅎ', j: 'ㅈ', q: 'ㅊ', x: 'ㅅ',
    zh: 'ㅈ', ch: 'ㅊ', sh: 'ㅅ', r: 'ㄹ', z: 'ㅉ', c: 'ㅊ', s: 'ㅆ'
  };

  // Each final is a list of [vowel, coda] pairs. The first pair takes the
  // initial consonant; any further pairs are written as their own syllable
  // with a silent ㅇ (ai -> 아이, ao -> 아오, ou -> 어우).
  var FINALS = {
    a: [['ㅏ']], o: [['ㅗ']], e: [['ㅓ']], ai: [['ㅏ'], ['ㅣ']], ei: [['ㅔ'], ['ㅣ']],
    ao: [['ㅏ'], ['ㅗ']], ou: [['ㅓ'], ['ㅜ']], an: [['ㅏ', 'ㄴ']], en: [['ㅓ', 'ㄴ']],
    ang: [['ㅏ', 'ㅇ']], eng: [['ㅓ', 'ㅇ']], ong: [['ㅜ', 'ㅇ']], er: [['ㅓ', 'ㄹ']],
    i: [['ㅣ']], ia: [['ㅑ']], ie: [['ㅖ']], iao: [['ㅑ'], ['ㅗ']], iu: [['ㅠ']],
    ian: [['ㅖ', 'ㄴ']], 'in': [['ㅣ', 'ㄴ']], iang: [['ㅑ', 'ㅇ']], ing: [['ㅣ', 'ㅇ']],
    iong: [['ㅠ', 'ㅇ']],
    u: [['ㅜ']], ua: [['ㅘ']], uo: [['ㅝ']], uai: [['ㅘ'], ['ㅣ']], ui: [['ㅜ'], ['ㅣ']],
    uan: [['ㅘ', 'ㄴ']], un: [['ㅜ', 'ㄴ']], uang: [['ㅘ', 'ㅇ']], ueng: [['ㅝ', 'ㅇ']],
    v: [['ㅟ']], ve: [['ㅟ'], ['ㅔ']], van: [['ㅟ'], ['ㅏ', 'ㄴ']], vn: [['ㅟ', 'ㄴ']]
  };

  // Syllables with no initial are spelled with y/w in pinyin, and a few of
  // them do not follow the consonant pattern (wei 웨이 but gui 구이).
  var ZERO = {
    yi: 'i', ya: 'ia', ye: 'ie', yao: 'iao', you: 'iu', yan: 'ian', yin: 'in',
    yang: 'iang', ying: 'ing', yong: 'iong', yu: 'v', yue: 've', yuan: 'van', yun: 'vn',
    wu: 'u', wa: 'ua', wo: 'uo', wai: 'uai', wan: 'uan', wang: 'uang', weng: 'ueng'
  };
  var ZERO_SPECIAL = { wei: '웨이', wen: '원', yue: '웨' };

  // ㅈ ㅉ ㅊ swallow the y-glide (jia 자, jiu 주, qian 첸); ㅅ keeps it (xia 샤).
  var DEGLIDE = { 'ㅑ': 'ㅏ', 'ㅕ': 'ㅓ', 'ㅖ': 'ㅔ', 'ㅛ': 'ㅗ', 'ㅠ': 'ㅜ' };

  function build(cho, parts) {
    var out = '';
    for (var i = 0; i < parts.length; i++) {
      out += syl(i === 0 ? cho : 'ㅇ', parts[i][0], parts[i][1]);
    }
    return out;
  }

  /* One pinyin syllable (any tone style: nǐ, ni3, ni; ü, v or u:) -> Hangul,
     or null when it is not a syllable we know (interjections like ng, hm). */
  function syllable(py) {
    var s = String(py).toLowerCase().normalize('NFD')
      .replace(/u\u0308/g, 'v').replace(/u:/g, 'v')
      .replace(/[\u0300-\u036f]/g, '').replace(/[0-5]/g, '')
      .replace(/ü/g, 'v');
    if (!/^[a-z]+$/.test(s)) return null;

    if (ZERO_SPECIAL[s]) return ZERO_SPECIAL[s];
    if (ZERO[s]) return build('ㅇ', FINALS[ZERO[s]]);
    if (FINALS[s] && /^[aoe]/.test(s)) return build('ㅇ', FINALS[s]);

    var ini = /^[zcs]h/.test(s) ? s.slice(0, 2) : s.charAt(0);
    var cho = INITIALS[ini];
    if (!cho) return null;
    var fin = s.slice(ini.length);

    // After j q x, written u is really ü.
    if (/^[jqx]$/.test(ini) && fin.charAt(0) === 'u') fin = 'v' + fin.slice(1);

    // zhi chi shi ri zi ci si: the "i" is a buzzed vowel, written ㅡ.
    if (fin === 'i' && /^(zh|ch|sh|r|z|c|s)$/.test(ini)) return syl(cho, 'ㅡ');

    var parts = FINALS[fin];
    if (!parts) return null;
    parts = parts.map(function (p) { return [p[0], p[1]]; });

    // üe after j q x is one syllable (jue 줴, xue 쉐); after n l it is two (뉘에).
    if (fin === 've' && /^[jqx]$/.test(ini)) parts = [['ㅞ']];
    if ((cho === 'ㅈ' || cho === 'ㅉ' || cho === 'ㅊ') && DEGLIDE[parts[0][0]]) {
      parts[0][0] = DEGLIDE[parts[0][0]];
    }
    return build(cho, parts);
  }

  var api = { syllable: syllable };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TovaHangul = api;
})(this);
