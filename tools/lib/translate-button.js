/* Tova pinyin converter — optional "Translate" button (2026-11-19).
 *
 * The pinyin itself still runs only in the browser (lib/tool.js). This script
 * adds a button that, ONLY when pressed, sends the text in the box to Tova's
 * server (POST https://api.tovatranslate.app/api/web/translate) and shows the
 * translation. The page's privacy line and FAQ say exactly that — keep them in
 * step if this changes. Server-side limits (Chinese only, 300 characters,
 * per-network and daily caps) live in backend/routes/webTranslate.js; the
 * codes it returns are mapped to messages below.
 *
 * Self-contained: its own strings for the 14 site languages (picked from
 * <html lang>) and its own styles, so it does not touch tool.js.
 */
(function () {
  'use strict';
  var input = document.getElementById('in');
  var card = document.querySelector('.toolcard');
  if (!input || !card) return;

  var API = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
    ? 'http://localhost:3011/api/web/translate'
    : 'https://api.tovatranslate.app/api/web/translate';
  var MAX = 300;
  var HAN = /[⺀-⿟㐀-䶿一-鿿豈-﫿]|[\uD840-\uD87E][\uDC00-\uDFFF]/;

  // Target languages offered (server accepts exactly these), each in its own name.
  var TARGETS = [
    ['en', 'English'], ['zh-TW', '繁體中文'], ['zh-CN', '简体中文'], ['ja', '日本語'], ['ko', '한국어'],
    ['es', 'Español'], ['fr', 'Français'], ['de', 'Deutsch'], ['pt', 'Português'], ['it', 'Italiano'],
    ['th', 'ไทย'], ['vi', 'Tiếng Việt'], ['id', 'Bahasa Indonesia'], ['tl', 'Filipino']
  ];

  var S = {
    en: { into: 'Translate into', go: 'Translate', going: 'Translating…', head: 'Translation', copy: 'Copy', copied: 'Copied',
      note: 'Translate sends the text in the box to Tova’s server. The pinyin stays in your browser.',
      needZh: 'Type some Chinese characters first.', long: 'Translate works on up to 300 characters at a time.',
      rate: 'Too many translations — wait a minute and try again.', daily: 'You’ve reached today’s limit. Try again tomorrow, or use the free Tova app.',
      busy: 'Translation is busy right now. Try again later, or use the Tova app.', fail: 'Couldn’t translate right now. Please try again.' },
    'zh-cn': { into: '翻译成', go: '翻译', going: '正在翻译…', head: '翻译', copy: '复制', copied: '已复制',
      note: '点“翻译”会把框里的文字发送到 Tova 服务器。拼音仍只在你的浏览器里生成。',
      needZh: '请先输入中文。', long: '每次最多翻译 300 个字。',
      rate: '翻译次数太多了，请等一分钟再试。', daily: '今天的次数已用完。明天再试，或使用免费的 Tova App。',
      busy: '翻译服务正忙，请稍后再试，或使用 Tova App。', fail: '暂时无法翻译，请重试。' },
    'zh-tw': { into: '翻譯成', go: '翻譯', going: '正在翻譯…', head: '翻譯', copy: '複製', copied: '已複製',
      note: '點「翻譯」會把框內的文字傳送到 Tova 伺服器。拼音仍只在你的瀏覽器中產生。',
      needZh: '請先輸入中文。', long: '每次最多翻譯 300 個字。',
      rate: '翻譯次數太多了，請等一分鐘再試。', daily: '今天的次數已用完。明天再試，或使用免費的 Tova App。',
      busy: '翻譯服務正忙，請稍後再試，或使用 Tova App。', fail: '暫時無法翻譯，請重試。' },
    ja: { into: '翻訳先', go: '翻訳', going: '翻訳中…', head: '翻訳', copy: 'コピー', copied: 'コピーしました',
      note: '「翻訳」を押すと、入力欄の文字が Tova のサーバーに送信されます。ピンインはブラウザ内だけで作られます。',
      needZh: 'まず中国語を入力してください。', long: '一度に翻訳できるのは 300 文字までです。',
      rate: '翻訳の回数が多すぎます。1 分ほど待ってからお試しください。', daily: '本日の上限に達しました。明日もう一度お試しいただくか、無料の Tova アプリをご利用ください。',
      busy: '現在、翻訳が混み合っています。しばらくしてからお試しいただくか、Tova アプリをご利用ください。', fail: '翻訳できませんでした。もう一度お試しください。' },
    ko: { into: '번역할 언어', go: '번역', going: '번역 중…', head: '번역', copy: '복사', copied: '복사됨',
      note: '‘번역’을 누르면 입력란의 글이 Tova 서버로 전송됩니다. 병음은 브라우저 안에서만 만들어집니다.',
      needZh: '먼저 중국어를 입력하세요.', long: '한 번에 300자까지 번역할 수 있습니다.',
      rate: '번역 요청이 너무 많습니다. 1분 뒤에 다시 시도하세요.', daily: '오늘 사용 한도에 도달했습니다. 내일 다시 시도하거나 무료 Tova 앱을 사용하세요.',
      busy: '지금은 번역이 혼잡합니다. 잠시 후 다시 시도하거나 Tova 앱을 사용하세요.', fail: '지금은 번역할 수 없습니다. 다시 시도하세요.' },
    es: { into: 'Traducir al', go: 'Traducir', going: 'Traduciendo…', head: 'Traducción', copy: 'Copiar', copied: 'Copiado',
      note: 'Traducir envía el texto del cuadro al servidor de Tova. El pinyin se queda en tu navegador.',
      needZh: 'Escribe primero algunos caracteres chinos.', long: 'Se pueden traducir hasta 300 caracteres a la vez.',
      rate: 'Demasiadas traducciones: espera un minuto y vuelve a intentarlo.', daily: 'Has llegado al límite de hoy. Vuelve mañana o usa la app gratuita de Tova.',
      busy: 'La traducción está saturada ahora mismo. Inténtalo más tarde o usa la app de Tova.', fail: 'No se ha podido traducir. Inténtalo de nuevo.' },
    fr: { into: 'Traduire en', go: 'Traduire', going: 'Traduction…', head: 'Traduction', copy: 'Copier', copied: 'Copié',
      note: 'Traduire envoie le texte de la zone au serveur de Tova. Le pinyin reste dans votre navigateur.',
      needZh: 'Saisissez d’abord des caractères chinois.', long: 'La traduction porte sur 300 caractères au maximum à la fois.',
      rate: 'Trop de traductions : attendez une minute puis réessayez.', daily: 'Vous avez atteint la limite du jour. Réessayez demain ou utilisez l’app gratuite Tova.',
      busy: 'La traduction est très sollicitée en ce moment. Réessayez plus tard ou utilisez l’app Tova.', fail: 'Traduction impossible pour le moment. Réessayez.' },
    de: { into: 'Übersetzen in', go: 'Übersetzen', going: 'Wird übersetzt …', head: 'Übersetzung', copy: 'Kopieren', copied: 'Kopiert',
      note: '„Übersetzen“ sendet den Text im Feld an den Server von Tova. Das Pinyin bleibt in Ihrem Browser.',
      needZh: 'Geben Sie zuerst chinesische Schriftzeichen ein.', long: 'Es lassen sich bis zu 300 Zeichen auf einmal übersetzen.',
      rate: 'Zu viele Übersetzungen – warten Sie eine Minute und versuchen Sie es erneut.', daily: 'Das Tageslimit ist erreicht. Versuchen Sie es morgen wieder oder nutzen Sie die kostenlose Tova-App.',
      busy: 'Die Übersetzung ist gerade ausgelastet. Versuchen Sie es später oder nutzen Sie die Tova-App.', fail: 'Übersetzung gerade nicht möglich. Bitte versuchen Sie es erneut.' },
    pt: { into: 'Traduzir para', go: 'Traduzir', going: 'A traduzir…', head: 'Tradução', copy: 'Copiar', copied: 'Copiado',
      note: 'Traduzir envia o texto da caixa para o servidor do Tova. O pinyin fica no seu navegador.',
      needZh: 'Escreva primeiro alguns caracteres chineses.', long: 'É possível traduzir até 300 caracteres de cada vez.',
      rate: 'Demasiadas traduções — aguarde um minuto e tente novamente.', daily: 'Atingiu o limite de hoje. Tente amanhã ou use a app gratuita Tova.',
      busy: 'A tradução está sobrecarregada neste momento. Tente mais tarde ou use a app Tova.', fail: 'Não foi possível traduzir agora. Tente novamente.' },
    it: { into: 'Traduci in', go: 'Traduci', going: 'Traduzione…', head: 'Traduzione', copy: 'Copia', copied: 'Copiato',
      note: 'Traduci invia il testo della casella al server di Tova. Il pinyin resta nel tuo browser.',
      needZh: 'Scrivi prima dei caratteri cinesi.', long: 'Si possono tradurre fino a 300 caratteri alla volta.',
      rate: 'Troppe traduzioni: attendi un minuto e riprova.', daily: 'Hai raggiunto il limite di oggi. Riprova domani o usa l’app gratuita Tova.',
      busy: 'La traduzione è molto richiesta in questo momento. Riprova più tardi o usa l’app Tova.', fail: 'Impossibile tradurre ora. Riprova.' },
    th: { into: 'แปลเป็น', go: 'แปล', going: 'กำลังแปล…', head: 'คำแปล', copy: 'คัดลอก', copied: 'คัดลอกแล้ว',
      note: 'เมื่อกด แปล ข้อความในช่องจะถูกส่งไปยังเซิร์ฟเวอร์ของ Tova ส่วนพินอินสร้างในเบราว์เซอร์ของคุณเท่านั้น',
      needZh: 'พิมพ์ตัวอักษรจีนก่อน', long: 'แปลได้ครั้งละไม่เกิน 300 ตัวอักษร',
      rate: 'แปลบ่อยเกินไป รอสักหนึ่งนาทีแล้วลองอีกครั้ง', daily: 'ครบจำนวนของวันนี้แล้ว ลองใหม่พรุ่งนี้ หรือใช้แอป Tova ฟรี',
      busy: 'ขณะนี้มีผู้ใช้การแปลจำนวนมาก ลองใหม่ภายหลัง หรือใช้แอป Tova', fail: 'แปลไม่ได้ในขณะนี้ โปรดลองอีกครั้ง' },
    vi: { into: 'Dịch sang', go: 'Dịch', going: 'Đang dịch…', head: 'Bản dịch', copy: 'Sao chép', copied: 'Đã sao chép',
      note: 'Nút Dịch sẽ gửi chữ trong ô đến máy chủ của Tova. Pinyin vẫn được tạo ngay trong trình duyệt của bạn.',
      needZh: 'Hãy nhập chữ Hán trước.', long: 'Mỗi lần dịch được tối đa 300 ký tự.',
      rate: 'Bạn dịch quá nhiều lần — hãy đợi một phút rồi thử lại.', daily: 'Bạn đã dùng hết lượt hôm nay. Hãy thử lại vào ngày mai hoặc dùng ứng dụng Tova miễn phí.',
      busy: 'Dịch vụ đang quá tải. Hãy thử lại sau hoặc dùng ứng dụng Tova.', fail: 'Hiện chưa dịch được. Vui lòng thử lại.' },
    id: { into: 'Terjemahkan ke', go: 'Terjemahkan', going: 'Menerjemahkan…', head: 'Terjemahan', copy: 'Salin', copied: 'Disalin',
      note: 'Tombol Terjemahkan mengirim teks di kotak ke server Tova. Pinyin tetap dibuat di browser Anda.',
      needZh: 'Ketik beberapa karakter Mandarin terlebih dahulu.', long: 'Terjemahan maksimal 300 karakter sekali jalan.',
      rate: 'Terlalu banyak terjemahan — tunggu satu menit lalu coba lagi.', daily: 'Batas hari ini sudah tercapai. Coba lagi besok, atau gunakan aplikasi Tova gratis.',
      busy: 'Layanan terjemahan sedang sibuk. Coba lagi nanti, atau gunakan aplikasi Tova.', fail: 'Tidak dapat menerjemahkan sekarang. Silakan coba lagi.' },
    tl: { into: 'Isalin sa', go: 'Isalin', going: 'Isinasalin…', head: 'Salin', copy: 'Kopyahin', copied: 'Nakopya',
      note: 'Ang Isalin ay nagpapadala ng text sa kahon sa server ng Tova. Sa browser mo lang ginagawa ang pinyin.',
      needZh: 'Mag-type muna ng Chinese characters.', long: 'Hanggang 300 characters lang ang maisasalin bawat beses.',
      rate: 'Sobrang dami ng pagsalin — maghintay ng isang minuto at subukan ulit.', daily: 'Naabot mo na ang limit ngayong araw. Subukan ulit bukas, o gamitin ang libreng Tova app.',
      busy: 'Abala ang pagsasalin ngayon. Subukan ulit mamaya, o gamitin ang Tova app.', fail: 'Hindi maisalin ngayon. Pakisubukan ulit.' }
  };

  var langAttr = (document.documentElement.lang || 'en').toLowerCase();
  var code = /^zh-(hant|tw|hk)/.test(langAttr) ? 'zh-tw' : /^zh/.test(langAttr) ? 'zh-cn' : langAttr.split('-')[0];
  var t = S[code] || S.en;
  var defTarget = { 'zh-cn': 'en', 'zh-tw': 'en', ja: 'ja', ko: 'ko', es: 'es', fr: 'fr', de: 'de', pt: 'pt',
    it: 'it', th: 'th', vi: 'vi', id: 'id', tl: 'tl' }[code] || 'en';
  var storedTarget = null;
  try { storedTarget = localStorage.getItem('tova.trTarget'); } catch (_) {}
  var target = TARGETS.some(function (x) { return x[0] === storedTarget; }) ? storedTarget : defTarget;

  var css = document.createElement('style');
  css.textContent =
    '.tvtr{margin-top:14px;padding-top:13px;border-top:1px solid var(--border)}' +
    '.tvtr-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}' +
    '.tvtr-row label{font-size:14px;font-weight:600;color:#33424c}' +
    '.tvtr select{min-height:44px;border:1.5px solid var(--border);border-radius:10px;padding:0 10px;font:inherit;font-size:14px;color:var(--fg);background:#fff;max-width:100%}' +
    '.tvtr-go{min-height:44px;border:0;border-radius:10px;padding:0 18px;font:inherit;font-size:15px;font-weight:700;color:#fff;background:var(--accent);cursor:pointer}' +
    '.tvtr-go:disabled{opacity:.5;cursor:default}' +
    '.tvtr-note{font-size:12.5px;color:var(--muted);margin:8px 0 0}' +
    '.tvtr-msg{font-size:13.5px;color:#9a3412;margin:8px 0 0;min-height:0}' +
    '.tvtr-out{margin-top:10px;border:1.5px solid var(--border);border-radius:13px;padding:12px 14px;background:#FBFDFE}' +
    '.tvtr-out[hidden]{display:none}' +
    '.tvtr-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}' +
    '.tvtr-head .eyebrow{color:var(--accent)}' +
    '.tvtr-text{font-size:17px;line-height:1.55;color:var(--fg);white-space:pre-wrap;overflow-wrap:anywhere;margin:0}' +
    // Korean breaks inside words by default ("브라우/저"); keep words whole.
    'html[lang^="ko"] .tvtr-note,html[lang^="ko"] .tvtr-msg{word-break:keep-all}';
  document.head.appendChild(css);

  var box = document.createElement('div');
  box.className = 'tvtr';
  var opts = TARGETS.map(function (x) {
    return '<option value="' + x[0] + '"' + (x[0] === target ? ' selected' : '') + ' lang="' + x[0] + '">' + x[1] + '</option>';
  }).join('');
  box.innerHTML =
    '<div class="tvtr-row"><label for="tvtr-target"></label><select id="tvtr-target">' + opts + '</select>' +
    '<button type="button" class="tvtr-go"></button></div>' +
    '<p class="tvtr-note"></p><p class="tvtr-msg" role="status" aria-live="polite"></p>' +
    '<div class="tvtr-out" hidden><div class="tvtr-head"><div class="eyebrow"></div>' +
    '<button type="button" class="copy tvtr-copy"></button></div><p class="tvtr-text"></p></div>';
  card.appendChild(box);

  var sel = box.querySelector('select'), go = box.querySelector('.tvtr-go'), msg = box.querySelector('.tvtr-msg');
  var out = box.querySelector('.tvtr-out'), outText = box.querySelector('.tvtr-text'), copyBtn = box.querySelector('.tvtr-copy');
  box.querySelector('label').textContent = t.into;
  box.querySelector('.tvtr-note').textContent = t.note;
  box.querySelector('.tvtr-head .eyebrow').textContent = t.head;
  go.textContent = t.go;
  copyBtn.textContent = t.copy;

  var lastText = null, busy = false;

  function reset() {
    if (input.value.trim() !== lastText) { out.hidden = true; outText.textContent = ''; lastText = null; }
    msg.textContent = '';
    go.disabled = busy || !HAN.test(input.value);
  }
  input.addEventListener('input', reset);
  // Sample chips and Clear set the box from tool.js without an input event.
  card.addEventListener('click', function (e) {
    if (e.target.closest('.sample, #clear')) setTimeout(reset, 0);
  });
  sel.addEventListener('change', function () {
    target = sel.value;
    try { localStorage.setItem('tova.trTarget', target); } catch (_) {}
    out.hidden = true; lastText = null;
  });

  go.addEventListener('click', function () {
    var text = input.value.trim();
    msg.textContent = '';
    if (!HAN.test(text)) { msg.textContent = t.needZh; return; }
    if (Array.from(text).length > MAX) { msg.textContent = t.long; return; }
    busy = true; go.disabled = true; go.textContent = t.going;
    fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, target: target })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      if (res.ok && res.j.translation) {
        outText.textContent = res.j.translation;
        outText.lang = target;
        out.hidden = false;
        lastText = text;
        try { if (window.gtag) window.gtag('event', 'tool_translate', { target: target }); } catch (_) {}
        return;
      }
      var c = res.j.code;
      msg.textContent = c === 'rate' ? t.rate : c === 'daily' ? t.daily : c === 'budget' ? t.busy
        : c === 'not_chinese' ? t.needZh : c === 'length' ? t.long : t.fail;
    }).catch(function () {
      msg.textContent = t.fail;
    }).then(function () {
      busy = false; go.textContent = t.go; go.disabled = !HAN.test(input.value);
    });
  });

  copyBtn.addEventListener('click', function () {
    var s = outText.textContent;
    var done = function () {
      copyBtn.textContent = t.copied; copyBtn.classList.add('ok');
      setTimeout(function () { copyBtn.textContent = t.copy; copyBtn.classList.remove('ok'); }, 1400);
    };
    if (navigator.clipboard) navigator.clipboard.writeText(s).then(done, function () {});
  });

  reset();
})();
