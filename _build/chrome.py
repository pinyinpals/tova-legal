# -*- coding: utf-8 -*-
"""Site-wide header + footer ("chrome") for every public page.

Runs LAST in the build (see _build/build_all.sh). Every generator and every
hand-written page carries two marker pairs:

    <!--tv:header--> ... <!--/tv:header-->
    <!--tv:footer--> ... <!--/tv:footer-->

and this script replaces whatever sits between them, plus one <style
id="tv-chrome"> and one <script id="tv-chrome-js"> in <head>/<body>. It is
idempotent: run it as often as you like.

Why one post-processor instead of a header in each generator: until
2026-09-30 the homepage, the guides, the tools and the six hand-written
pages each drew their own header, and they had drifted into four different
brand names, two logos and three nav sets. One source cannot drift.

The locale comes from the URL prefix (/de/..., /zh-tw/...). The language
picker lists the page's own hreflang alternates when it has them, so a
tool page's picker goes to the same tool in another language rather than
dumping the reader on a homepage; pages with no alternates list the
localized homepages.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_STORE = 'https://apps.apple.com/us/app/tova-translate/id6764455741'
PLAY = 'https://play.google.com/store/apps/details?id=com.tovatranslate.app'
PLAY_SVG = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M22.018 13.298l-3.919 2.218-3.515-3.493 3.543-3.521 3.891 2.202a1.49 1.49 0 0 1 0 2.594zM1.337.924a1.486 1.486 0 0 0-.112.568v21.017c0 .217.045.419.124.6l11.155-11.087L1.337.924zm12.207 10.065l3.258-3.238L3.45.195a1.466 1.466 0 0 0-.946-.179l11.04 10.973zm0 2.067l-11 10.933c.298.036.612-.016.906-.183l13.324-7.54-3.23-3.21z"/></svg>')
# "Get the app" points at the App Store; on an Android phone this swaps it (and
# its icon) to Google Play before anyone can tap it.
ANDROID_SWAP = ('<script>if(/Android/i.test(navigator.userAgent)){var g=document.querySelector(".tv-get");'
                'if(g){g.href=' + repr(PLAY).replace("'", '"') + ';var i=g.querySelector("svg");'
                'if(i)i.outerHTML=' + repr(PLAY_SVG).replace("'", '"').replace('"<', "'<").replace('>"', ">'") + ';}}</script>')
SKIP_DIRS = {'.git', '_build', 'media', 'node_modules', 'lexicon'}

LOCALES = [  # (url prefix, hreflang code, native name)
    ('', 'en', 'English'),
    ('zh-cn', 'zh-Hans', '简体中文'), ('zh-tw', 'zh-Hant', '繁體中文'),
    ('ja', 'ja', '日本語'), ('ko', 'ko', '한국어'),
    ('es', 'es', 'Español'), ('fr', 'fr', 'Français'), ('de', 'de', 'Deutsch'),
    ('pt', 'pt', 'Português'), ('it', 'it', 'Italiano'), ('th', 'th', 'ไทย'),
    ('vi', 'vi', 'Tiếng Việt'), ('id', 'id', 'Bahasa Indonesia'),
    ('tl', 'tl', 'Filipino'),
]
NATIVE = {code: name for _, code, name in LOCALES}
PREFIXES = {p for p, _, _ in LOCALES if p}

# The five guides the footer promotes, in order.
TOP_GUIDES = ['best-translator-app-for-china', 'china-no-vpn',
              'offline-translator-china', 'chinese-menu',
              'chinese-train-stations']

# key order: guides, tools, faq, get, menu, lang, travel, all, tova, support,
# privacy, terms, learn, press, languages, made, tagline, then TOP_GUIDES labels
L = {
 'en': dict(guides='Guides', tools='Free tools', faq='FAQ', get='Get the app',
   menu='Menu', lang='Language', travel='Travel guides', all='All guides',
   tova='Tova', support='Support', privacy='Privacy', terms='Terms',
   learn='Tova Learn', press='Press', languages='Languages',
   made='A ZET Studios app',
   tagline='Camera and voice translator with pinyin and Jyutping. Works in China without a VPN.',
   g=['Best translator app for China', 'Translate in China without a VPN',
      'Offline translator for China', 'Read a Chinese menu',
      'Chinese train stations']),
 'zh-cn': dict(guides='指南', tools='免费工具', faq='常见问题', get='下载应用',
   menu='菜单', lang='语言', travel='旅行指南', all='全部指南', tova='Tova',
   support='支持', privacy='隐私', terms='条款', learn='Tova Learn',
   press='媒体', languages='语言', made='ZET Studios 出品',
   tagline='带拼音和粤拼的相机与语音翻译。在中国无需 VPN 也能用。',
   g=['在中国最好用的翻译应用', '在中国不用 VPN 也能翻译', '中国离线翻译',
      '看懂中文菜单', '中国火车站站名']),
 'zh-tw': dict(guides='指南', tools='免費工具', faq='常見問題', get='下載 App',
   menu='選單', lang='語言', travel='旅遊指南', all='所有指南', tova='Tova',
   support='支援', privacy='隱私權', terms='條款', learn='Tova Learn',
   press='媒體', languages='語言', made='ZET Studios 出品',
   tagline='附拼音與粵拼的相機及語音翻譯。在中國不用 VPN 也能用。',
   g=['中國最好用的翻譯 App', '在中國不用 VPN 翻譯', '中國離線翻譯',
      '看懂簡體菜單', '中國火車站站名']),
 'ja': dict(guides='ガイド', tools='無料ツール', faq='よくある質問',
   get='アプリを入手', menu='メニュー', lang='言語', travel='旅行ガイド',
   all='すべてのガイド', tova='Tova', support='サポート', privacy='プライバシー',
   terms='利用規約', learn='Tova Learn', press='プレス', languages='言語',
   made='ZET Studios のアプリ',
   tagline='ピンインと粤拼つきのカメラ・音声翻訳。中国でもVPNなしで使えます。',
   g=['中国で使える翻訳アプリ比較', '中国でVPNなしで翻訳する',
      '中国のオフライン翻訳', '中国語メニューの読み方', '中国の駅名の読み方']),
 'ko': dict(guides='가이드', tools='무료 도구', faq='자주 묻는 질문',
   get='앱 받기', menu='메뉴', lang='언어', travel='여행 가이드',
   all='전체 가이드', tova='Tova', support='지원', privacy='개인정보',
   terms='약관', learn='Tova Learn', press='보도자료', languages='언어',
   made='ZET Studios 앱',
   tagline='병음과 월병 표기를 보여주는 카메라·음성 번역기. 중국에서 VPN 없이 작동합니다.',
   g=['중국 여행 번역 앱 비교', '중국에서 VPN 없이 번역하기', '중국 오프라인 번역',
      '중국어 메뉴 읽는 법', '중국 기차역 이름 읽기']),
 'es': dict(guides='Guías', tools='Herramientas gratis', faq='Preguntas',
   get='Descargar la app', menu='Menú', lang='Idioma', travel='Guías de viaje',
   all='Todas las guías', tova='Tova', support='Ayuda', privacy='Privacidad',
   terms='Términos', learn='Tova Learn', press='Prensa', languages='Idiomas',
   made='Una app de ZET Studios',
   tagline='Traductor de cámara y voz con pinyin y jyutping. Funciona en China sin VPN.',
   g=['El mejor traductor para China', 'Traducir en China sin VPN',
      'Traductor sin conexión para China', 'Leer un menú chino',
      'Estaciones de tren en China']),
 'fr': dict(guides='Guides', tools='Outils gratuits', faq='FAQ',
   get="Télécharger l'app", menu='Menu', lang='Langue', travel='Guides de voyage',
   all='Tous les guides', tova='Tova', support='Assistance',
   privacy='Confidentialité', terms='Conditions', learn='Tova Learn',
   press='Presse', languages='Langues', made='Une app ZET Studios',
   tagline='Traducteur photo et vocal avec pinyin et jyutping. Fonctionne en Chine sans VPN.',
   g=['Le meilleur traducteur pour la Chine', 'Traduire en Chine sans VPN',
      'Traducteur hors ligne pour la Chine', 'Lire un menu chinois',
      'Les gares chinoises']),
 'de': dict(guides='Ratgeber', tools='Kostenlose Tools', faq='FAQ',
   get='App laden', menu='Menü', lang='Sprache', travel='Reiseratgeber',
   all='Alle Ratgeber', tova='Tova', support='Support', privacy='Datenschutz',
   terms='AGB', learn='Tova Learn', press='Presse', languages='Sprachen',
   made='Eine App von ZET Studios',
   tagline='Kamera- und Sprachübersetzer mit Pinyin und Jyutping. Funktioniert in China ohne VPN.',
   g=['Die beste Übersetzer-App für China', 'In China ohne VPN übersetzen',
      'Offline-Übersetzer für China', 'Chinesische Speisekarte lesen',
      'Bahnhöfe in China']),
 'pt': dict(guides='Guias', tools='Ferramentas grátis', faq='Perguntas',
   get='Baixar o app', menu='Menu', lang='Idioma', travel='Guias de viagem',
   all='Todos os guias', tova='Tova', support='Suporte', privacy='Privacidade',
   terms='Termos', learn='Tova Learn', press='Imprensa', languages='Idiomas',
   made='Um app da ZET Studios',
   tagline='Tradutor de câmera e voz com pinyin e jyutping. Funciona na China sem VPN.',
   g=['Melhor app de tradução para a China', 'Traduzir na China sem VPN',
      'Tradutor offline para a China', 'Ler um cardápio chinês',
      'Estações de trem na China']),
 'it': dict(guides='Guide', tools='Strumenti gratuiti', faq='Domande',
   get="Scarica l'app", menu='Menu', lang='Lingua', travel='Guide di viaggio',
   all='Tutte le guide', tova='Tova', support='Assistenza', privacy='Privacy',
   terms='Termini', learn='Tova Learn', press='Stampa', languages='Lingue',
   made='Un’app di ZET Studios',
   tagline='Traduttore con fotocamera e voce, con pinyin e jyutping. Funziona in Cina senza VPN.',
   g=['Il miglior traduttore per la Cina', 'Tradurre in Cina senza VPN',
      'Traduttore offline per la Cina', 'Leggere un menu cinese',
      'Stazioni ferroviarie in Cina']),
 'th': dict(guides='คู่มือ', tools='เครื่องมือฟรี', faq='คำถามที่พบบ่อย',
   get='ดาวน์โหลดแอป', menu='เมนู', lang='ภาษา', travel='คู่มือท่องเที่ยว',
   all='คู่มือทั้งหมด', tova='Tova', support='ช่วยเหลือ', privacy='ความเป็นส่วนตัว',
   terms='ข้อกำหนด', learn='Tova Learn', press='ข่าวสาร', languages='ภาษา',
   made='แอปจาก ZET Studios',
   tagline='แอปแปลภาษาด้วยกล้องและเสียง พร้อมพินอินและยฺหวิดเพ็ง ใช้ในจีนได้โดยไม่ต้องใช้ VPN',
   g=['แอปแปลภาษาที่ดีที่สุดสำหรับจีน', 'แปลภาษาในจีนโดยไม่ใช้ VPN',
      'แอปแปลภาษาออฟไลน์สำหรับจีน', 'อ่านเมนูภาษาจีน', 'ชื่อสถานีรถไฟในจีน']),
 'vi': dict(guides='Hướng dẫn', tools='Công cụ miễn phí', faq='Hỏi đáp',
   get='Tải ứng dụng', menu='Menu', lang='Ngôn ngữ', travel='Cẩm nang du lịch',
   all='Tất cả hướng dẫn', tova='Tova', support='Hỗ trợ',
   privacy='Quyền riêng tư', terms='Điều khoản', learn='Tova Learn',
   press='Báo chí', languages='Ngôn ngữ', made='Ứng dụng của ZET Studios',
   tagline='Dịch bằng camera và giọng nói, có pinyin và Jyutping. Dùng được ở Trung Quốc không cần VPN.',
   g=['Ứng dụng dịch tốt nhất ở Trung Quốc', 'Dịch ở Trung Quốc không cần VPN',
      'Dịch ngoại tuyến ở Trung Quốc', 'Đọc thực đơn tiếng Trung',
      'Tên ga tàu ở Trung Quốc']),
 'id': dict(guides='Panduan', tools='Alat gratis', faq='Tanya jawab',
   get='Unduh aplikasi', menu='Menu', lang='Bahasa', travel='Panduan perjalanan',
   all='Semua panduan', tova='Tova', support='Bantuan', privacy='Privasi',
   terms='Ketentuan', learn='Tova Learn', press='Pers', languages='Bahasa',
   made='Aplikasi dari ZET Studios',
   tagline='Penerjemah kamera dan suara dengan pinyin dan Jyutping. Bisa dipakai di Tiongkok tanpa VPN.',
   g=['Aplikasi penerjemah terbaik untuk Tiongkok', 'Menerjemahkan di Tiongkok tanpa VPN',
      'Penerjemah offline untuk Tiongkok', 'Membaca menu Mandarin',
      'Stasiun kereta di Tiongkok']),
 'tl': dict(guides='Mga gabay', tools='Libreng tools', faq='FAQ',
   get='I-download ang app', menu='Menu', lang='Wika', travel='Mga gabay sa biyahe',
   all='Lahat ng gabay', tova='Tova', support='Suporta', privacy='Privacy',
   terms='Mga tuntunin', learn='Tova Learn', press='Press', languages='Mga wika',
   made='Isang app ng ZET Studios',
   tagline='Camera at voice translator na may pinyin at Jyutping. Gumagana sa China kahit walang VPN.',
   g=['Pinakamahusay na translator app para sa China', 'Mag-translate sa China nang walang VPN',
      'Offline translator para sa China', 'Pagbasa ng Chinese menu',
      'Mga istasyon ng tren sa China']),
}
PREFIX_TO_CODE = {p: c for p, c, _ in LOCALES}
LABEL_KEY = {'': 'en', 'zh-cn': 'zh-cn', 'zh-tw': 'zh-tw'}

APPLE_SVG = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
             '<path d="M17.5 12.5c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.7 3-.4 7.4 1.3 9.8.8 1.2 1.8 2.5 3.1 2.5 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9z"/></svg>')
GLOBE_SVG = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
             '<line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 '
             '15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>')

INSTAGRAM_URL = 'https://www.instagram.com/tova.translate/'
# Same outline style as GLOBE_SVG (white stroke, 2px, round caps); a touch
# larger because it stands alone with no label beside it on desktop.
INSTAGRAM_SVG = ('<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>'
                 '<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>'
                 '<line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>')

CSS = """
.tv-hdr{position:sticky;top:0;z-index:100;background:rgba(7,78,116,.94);
  -webkit-backdrop-filter:saturate(160%) blur(10px);backdrop-filter:saturate(160%) blur(10px);
  color:#fff;border-bottom:1px solid rgba(255,255,255,.12);
  font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Arial,sans-serif;
  line-height:1.3;text-align:left;margin:0;padding:0}
.tv-hdr *{box-sizing:border-box}
.tv-hdr-in{max-width:1180px;margin:0 auto;padding:0 18px;height:60px;display:flex;align-items:center;gap:14px}
.tv-logo{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;
  font-size:17px;letter-spacing:-.01em;min-height:44px;margin-right:auto;white-space:nowrap}
.tv-logo img{width:34px;height:34px;border-radius:9px;display:block}
.tv-nav{display:flex;align-items:center;gap:4px}
.tv-nav>a,.tv-lang>summary{color:#fff;text-decoration:none;font-size:15px;font-weight:600;
  padding:0 12px;min-height:44px;display:inline-flex;align-items:center;gap:7px;border-radius:10px;cursor:pointer}
.tv-nav>a:hover,.tv-lang>summary:hover{background:rgba(255,255,255,.12)}
.tv-nav>a[aria-current=page]{background:rgba(255,255,255,.16)}
.tv-nav>a.tv-get{background:#fff;color:#073f5e;margin-left:8px;padding:0 16px;font-weight:700}
.tv-nav>a.tv-ig{min-width:44px;justify-content:center;padding:0 10px}
.tv-ig-label{display:none}
.tv-nav>a.tv-get:hover{background:#e6f5fc}
.tv-lang{position:relative}
.tv-lang>summary{list-style:none}
.tv-lang>summary::-webkit-details-marker{display:none}
.tv-lang-menu{position:absolute;right:0;top:calc(100% + 6px);background:#fff;border-radius:12px;min-width:210px;
  max-height:70vh;overflow:auto;padding:6px 0;box-shadow:0 14px 34px rgba(0,30,60,.25);z-index:110}
.tv-lang-menu a{display:flex;align-items:center;min-height:44px;padding:0 16px;color:#16202a;
  text-decoration:none;font-size:15px}
.tv-lang-menu a:hover{background:#e7f5fb}
.tv-lang-menu a[aria-current=true]{font-weight:700;color:#075e8c}
.tv-burger{display:none;background:transparent;border:0;color:#fff;width:44px;height:44px;
  border-radius:10px;cursor:pointer;align-items:center;justify-content:center;padding:0}
.tv-burger:hover{background:rgba(255,255,255,.12)}
@media (max-width:767px){
  .tv-burger{display:inline-flex}
  .tv-hdr-in{height:56px}
  .tv-nav{display:none;position:absolute;left:0;right:0;top:56px;flex-direction:column;align-items:stretch;
    background:#073f5e;padding:8px 14px 16px;gap:2px;box-shadow:0 18px 30px rgba(0,20,40,.3)}
  .tv-hdr.tv-open .tv-nav{display:flex}
  .tv-nav>a,.tv-lang>summary{font-size:17px;padding:0 12px;min-height:48px}
  .tv-nav>a.tv-get{margin:8px 0 0;justify-content:center}
  .tv-nav>a.tv-ig{justify-content:flex-start;padding:0 12px}
  .tv-ig-label{display:inline}
  .tv-lang-menu{position:static;box-shadow:none;margin:4px 0;max-height:none}
}
@media (max-width:360px){.tv-logo{font-size:16px}}
.tv-ftr{background:#062f47;color:#dcebf3;margin:0;padding:0;text-align:left;opacity:1;
  font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Arial,sans-serif;line-height:1.5}
.tv-ftr *{box-sizing:border-box}
.tv-ftr a{color:#fff;text-decoration:none}
.tv-ftr a:hover{text-decoration:underline}
.tv-ftr-in{max-width:1180px;margin:0 auto;padding:44px 22px 22px;display:grid;gap:30px;
  grid-template-columns:1.3fr 1.2fr 1fr 1.2fr}
.tv-ftr-brand p{font-size:14px;margin:12px 0 16px;max-width:300px;color:#c9dfea}
.tv-ftr-logo{gap:10px;font-weight:800}
.tv-ftr-logo img{width:36px;height:36px;border-radius:9px}
.tv-ftr-app{display:inline-flex;align-items:center;gap:8px;background:#fff;color:#062f47 !important;
  font-weight:700;font-size:15px;padding:0 16px;min-height:44px;border-radius:12px}
.tv-ftr-app:hover{text-decoration:none !important;background:#e6f5fc}
.tv-ftr-h{font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#9cc6dc;margin:0 0 8px}
.tv-ftr ul{list-style:none;margin:0;padding:0}
.tv-ftr li a,.tv-ftr-langs a,.tv-ftr-base a,.tv-ftr-logo{display:inline-flex;align-items:center;min-height:44px;min-width:44px;font-size:14.5px}
.tv-ftr-logo{font-size:18px}
.tv-ftr-langs{display:flex;flex-wrap:wrap;gap:0 14px}
.tv-ftr-base{max-width:1180px;margin:0 auto;padding:18px 22px 30px;border-top:1px solid rgba(255,255,255,.12);
  font-size:13px;color:#b5d0de}
@media (max-width:900px){.tv-ftr-in{grid-template-columns:1fr 1fr}}
@media (max-width:520px){.tv-ftr-in{grid-template-columns:1fr}}
"""

JS = """(function(){var h=document.querySelector('.tv-hdr');if(!h)return;var b=h.querySelector('.tv-burger');
b.addEventListener('click',function(){var o=h.classList.toggle('tv-open');b.setAttribute('aria-expanded',o?'true':'false');});
document.addEventListener('click',function(e){var d=h.querySelector('.tv-lang');if(d&&d.open&&!d.contains(e.target))d.open=false;});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){h.classList.remove('tv-open');b.setAttribute('aria-expanded','false');var d=h.querySelector('.tv-lang');if(d)d.open=false;}});})();"""

esc = lambda s: html.escape(s, quote=True)


def page_locale(rel_dir):
    first = rel_dir.split('/')[0] if rel_dir not in ('', '.') else ''
    return first if first in PREFIXES else ''


def alternates(src):
    alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', src)
    return [(c, h.replace('https://tovatranslate.app', '')) for c, h in alts if c != 'x-default']


def lang_items(src, cur_code):
    alts = alternates(src)
    if len(alts) < 2:
        alts = [(c, f'/{p}/' if p else '/') for p, c, _ in LOCALES]
    order = [c for _, c, _ in LOCALES]
    alts.sort(key=lambda a: order.index(a[0]) if a[0] in order else 99)
    return [(c, h, NATIVE.get(c, c)) for c, h in alts]


def guide_href(prefix, slug):
    if prefix and os.path.exists(os.path.join(ROOT, prefix, 'translate', slug, 'index.html')):
        return f'/{prefix}/translate/{slug}/'
    return f'/translate/{slug}/'


def header(prefix, rel_dir, src):
    t = L[prefix or 'en']
    code = PREFIX_TO_CODE[prefix]
    home = f'/{prefix}/' if prefix else '/'
    brand = 'Tova通话' if prefix in ('zh-cn', 'zh-tw') else 'Tova Translate'
    here = '/' + (rel_dir + '/' if rel_dir not in ('', '.') else '')
    tools = f'/{prefix}/tools/' if prefix else '/tools/'

    def nav(href, label, section):
        cur = ' aria-current="page"' if here.startswith(section) else ''
        return f'<a href="{href}"{cur}>{esc(label)}</a>'
    items = ''.join(
        f'<a href="{h}" hreflang="{c}" lang="{c}"'
        + (' aria-current="true"' if c == code else '') + f'>{esc(n)}</a>'
        for c, h, n in lang_items(src, code))
    return (
        '<header class="tv-hdr"><div class="tv-hdr-in">'
        f'<a class="tv-logo" href="{home}"><img src="/media/tova-icon-72.png" width="34" height="34" alt="">'
        f'<span>{brand}</span></a>'
        f'<button class="tv-burger" type="button" aria-expanded="false" aria-controls="tv-nav" aria-label="{esc(t["menu"])}">'
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" aria-hidden="true"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" '
        'x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>'
        f'<nav class="tv-nav" id="tv-nav" aria-label="{esc(t["menu"])}">'
        + nav('/translate/', t['guides'], '/translate/')
        + nav(tools, t['tools'], tools)
        + nav('/faq/', t['faq'], '/faq/')
        + f'<details class="tv-lang"><summary aria-label="{esc(t["lang"])}: {esc(NATIVE[code])}">'
          f'{GLOBE_SVG}<span>{esc(NATIVE[code])}</span></summary>'
          f'<div class="tv-lang-menu">{items}</div></details>'
        + f'<a class="tv-ig" href="{INSTAGRAM_URL}" target="_blank" rel="noopener me" '
          f'aria-label="Tova on Instagram" title="Instagram">{INSTAGRAM_SVG}'
          f'<span class="tv-ig-label">Instagram</span></a>'
        + f'<a class="tv-get" href="{APP_STORE}" target="_blank" rel="noopener">{APPLE_SVG}{esc(t["get"])}</a>'
        '</nav></div></header>' + ANDROID_SWAP)


def footer(prefix, src):
    t = L[prefix or 'en']
    code = PREFIX_TO_CODE[prefix]
    home = f'/{prefix}/' if prefix else '/'
    tools = f'/{prefix}/tools/' if prefix else '/tools/'
    guides = ''.join(f'<li><a href="{guide_href(prefix, s)}">{esc(lbl)}</a></li>'
                     for s, lbl in zip(TOP_GUIDES, t['g']))
    langs = ''.join(f'<a href="{h}" hreflang="{c}" lang="{c}">{esc(n)}</a>'
                    for c, h, n in lang_items(src, code))
    return (
        '<footer class="tv-ftr"><div class="tv-ftr-in">'
        f'<div class="tv-ftr-brand"><a class="tv-ftr-logo" href="{home}"><img src="/media/tova-icon-72.png" width="36" '
        f'height="36" alt="" loading="lazy">Tova Translate</a><p>{esc(t["tagline"])}</p>'
        f'<a class="tv-ftr-app" href="{APP_STORE}" target="_blank" rel="noopener">{APPLE_SVG}App Store</a> '
        f'<a class="tv-ftr-app" href="{PLAY}" target="_blank" rel="noopener">{PLAY_SVG}Google Play</a></div>'
        f'<div><p class="tv-ftr-h">{esc(t["travel"])}</p><ul>{guides}'
        f'<li><a href="/translate/">{esc(t["all"])} →</a></li></ul></div>'
        f'<div><p class="tv-ftr-h">{esc(t["tova"])}</p><ul>'
        f'<li><a href="{tools}">{esc(t["tools"])}</a></li><li><a href="/faq/">{esc(t["faq"])}</a></li>'
        f'<li><a href="/learn/">{esc(t["learn"])}</a></li><li><a href="/support/">{esc(t["support"])}</a></li>'
        f'<li><a href="/press/">{esc(t["press"])}</a></li><li><a href="/privacy/">{esc(t["privacy"])}</a></li>'
        f'<li><a href="/terms/">{esc(t["terms"])}</a></li></ul></div>'
        f'<div><p class="tv-ftr-h">{esc(t["languages"])}</p><div class="tv-ftr-langs">{langs}</div></div>'
        '</div><div class="tv-ftr-base">© 2026 Tova Translate · '
        f'<a href="https://zetstudios.ca/apps/tova/">{esc(t["made"])}</a></div></footer>')


def process(path, rel_dir):
    src = open(path, encoding='utf-8').read()
    if '<!--tv:header-->' not in src or '<!--tv:footer-->' not in src:
        return False
    prefix = page_locale(rel_dir)
    src = re.sub(r'<!--tv:header-->.*?<!--/tv:header-->',
                 lambda m: '<!--tv:header-->' + header(prefix, rel_dir, src) + '<!--/tv:header-->',
                 src, count=1, flags=re.S)
    src = re.sub(r'<!--tv:footer-->.*?<!--/tv:footer-->',
                 lambda m: '<!--tv:footer-->' + footer(prefix, src) + '<!--/tv:footer-->',
                 src, count=1, flags=re.S)
    src = re.sub(r'\s*<style id="tv-chrome">.*?</style>', '', src, flags=re.S)
    src = re.sub(r'\s*<script id="tv-chrome-js">.*?</script>', '', src, flags=re.S)
    # Favicons: the 1024px /tova-icon.png (507 KB) was being fetched as a tab icon.
    src = re.sub(r'<link rel="icon"[^>]*>', '<link rel="icon" type="image/png" sizes="48x48" href="/media/favicon-48.png">', src, count=1)
    src = re.sub(r'<link rel="apple-touch-icon"[^>]*>', '', src)
    src = src.replace('<link rel="icon" type="image/png" sizes="48x48" href="/media/favicon-48.png">',
                      '<link rel="icon" type="image/png" sizes="48x48" href="/media/favicon-48.png">'
                      '<link rel="apple-touch-icon" href="/media/apple-touch-icon.png">', 1)
    src = src.replace('</head>', f'<style id="tv-chrome">{CSS}</style>\n</head>', 1)
    src = src.replace('</body>', f'<script id="tv-chrome-js">{JS}</script>\n</body>', 1)
    open(path, 'w', encoding='utf-8').write(src)
    return True


def main():
    done, skipped = 0, []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        if 'index.html' not in files:
            continue
        rel = os.path.relpath(d, ROOT)
        if process(os.path.join(d, 'index.html'), rel):
            done += 1
        else:
            skipped.append(rel)
    print(f'chrome: {done} pages')
    if skipped:
        print('  no markers (left untouched):', ', '.join(skipped))
        if '--strict' in sys.argv:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
