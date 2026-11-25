#!/usr/bin/env python3
"""Build /browser-extension/ (English): Tova for Chrome and Safari (Mac).

    python3 _build/browser_page.py
    python3 -c "import sys,os;sys.path.insert(0,'_build');import chrome;chrome.process(os.path.join(chrome.ROOT,'browser-extension','index.html'),'browser-extension')"

Store buttons follow _build/browser_stores.json: a store that isn't live yet shows "Coming soon" with no link.
Styles: _build/keyboard_page.css + EXTRA below. NEW PAGE — published by a queued routine (owner's pacing rule).
"""
import html, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://tovatranslate.app'
URL = f'{BASE}/browser-extension/'
ST = json.load(open(os.path.join(ROOT, '_build', 'browser_stores.json')))
CHROME = f"https://chromewebstore.google.com/detail/{ST['chrome_id']}" if ST.get('chrome_id') else None
MAC = 'https://apps.apple.com/us/app/tova-translate/id6764455741?platform=mac' if ST.get('mac_live') else None
IPHONE = 'https://apps.apple.com/us/app/tova-translate/id6764455741'
CSS = open(os.path.join(ROOT, '_build', 'keyboard_page.css'), encoding='utf-8').read()
EXTRA = '''
  .wide{display:block;width:100%;border-radius:14px;border:1px solid rgba(255,255,255,.35);background:#fff;box-shadow:0 22px 50px rgba(0,25,45,.42)}
  .hero.hx{grid-template-columns:minmax(0,1fr) minmax(0,1.15fr)}
  .cta.soon{background:rgba(0,0,0,.35);box-shadow:none;cursor:default}
  .cta.soon:hover{filter:none}
  .bshots{display:grid;gap:22px;margin-top:24px}
  .bshots figure{margin:0}
  .bshots img{display:block;width:100%;border-radius:14px;border:1px solid var(--line);box-shadow:0 10px 26px rgba(15,40,60,.12)}
  .bshots figcaption{font-size:14.5px;color:var(--muted);margin-top:10px}
  kbd{font:600 13px ui-monospace,Menlo,monospace;background:#EEF4F7;border:1px solid #D5E1E8;border-radius:6px;padding:1px 6px;color:#1d2a33}
  @media (min-width:860px){.bshots{grid-template-columns:1fr 1fr}}
  @media (max-width:900px){.hero.hx{grid-template-columns:minmax(0,1fr)}}
'''
CHROME_SVG = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M12 8h9M8.5 14l-4.6-7.8M15.5 14l-4.5 8"/></svg>'
SAFARI_SVG = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M16 8l-2.5 5.5L8 16l2.5-5.5z"/></svg>'

def cta(href, svg, small, big):
    if href:
        return f'<a class="cta" href="{href}" target="_blank" rel="noopener">{svg}<span><small>{small}</small>{big}</span></a>'
    return f'<span class="cta soon" aria-disabled="true">{svg}<span><small>Coming soon</small>{big}</span></span>'

def ctas():
    return ('<div class="ctas">\n        ' + cta(CHROME, CHROME_SVG, 'Add to Chrome', 'Chrome Web Store') +
            '\n        ' + cta(MAC, SAFARI_SVG, 'Safari on the Mac', 'Mac App Store') + '\n      </div>')

TITLE = 'Pinyin Browser Extension for Chrome and Safari — Tova'
DESC = ('Point at a Chinese word on any web page for its pinyin or Jyutping and meanings, looked up on your computer. '
        'Translate and reply in Chinese, Japanese or Korean.')
NOTE = ('Chrome on Windows and Mac · Safari on the Mac · word cards always free, 20 translations a day, unlimited with Tova Pro'
        if CHROME and MAC else
        'Coming soon for Chrome (Windows and Mac) and Safari on the Mac. Word cards always free, 20 translations a day, unlimited with Tova Pro.')

CARDS = [
 ("Word cards", "Rest the pointer on a Chinese word: pinyin in tone colours, its meanings, measure words and other readings, from the CC-CEDICT dictionary inside the extension. Simplified and traditional."),
 ("Cantonese", "Choose Jyutping and the card shows the Cantonese reading first, with pinyin underneath."),
 ("Translate with readings", "Highlight text and click the Tova button: the translation, with pinyin, Jyutping, Japanese romaji or Korean romanization above every character."),
 ("Readings on the page", "Put readings right above the words on the page, like a textbook. One click puts the page back."),
 ("Reply in 中文", "In a text box or email, write in your own language and press “Reply in 中文”. Tova translates it and shows a “Means:” line in your language before you replace your text. A Polite switch for formal Japanese and Korean."),
 ("Listen", "Hear a word or sentence with a voice on your computer."),
]
SHOTS = [
 ("browser-word", "A word card: 躺平 tǎng píng in tone colours, with both of its meanings.", "A Chinese article with a Tova word card for 躺平, showing tǎng píng and two meanings"),
 ("browser-translate", "Highlight and translate: the readings sit above every character.", "A highlighted Chinese paragraph translated by Tova, with pinyin above each character"),
 ("browser-readings", "Readings on the page, added above the original text.", "A Chinese web page with pinyin shown above the words"),
 ("browser-reply", "Reply in 中文: an English message becomes Chinese, with a “Means:” line to check it.", "Tova's reply card turning an English message into Chinese with pinyin and a Means line"),
 ("browser-japanese", "Japanese too: translations with romaji.", "A Japanese passage translated by Tova with romaji readings"),
]
FAQ = [
 ("Is the Tova browser extension free?",
  "Yes. Word cards and readings on the page are always free and have no limit. Translations and replies are free up to 20 a day. Tova Pro removes that limit."),
 ("Does looking up a word send it anywhere?",
  "No. Word cards come from a dictionary inside the extension and are looked up on your computer. Text is sent to Tova's server only when you ask for a translation or a reply."),
 ("I already pay for Tova Pro on my phone. Do I pay again?",
  "No. On Chrome, open the Tova app on your iPhone, go to Settings → Tova Pro on your computer, get a code and type it into the extension; up to three computers. On a Mac, Safari uses the Pro you bought on your iPhone with the same Apple Account. Linking from Android phones is coming."),
 ("Does pointing at a word work for Japanese and Korean?",
  "Word cards are for Chinese. For Japanese and Korean, highlight the text and translate it: you get romaji or Korean romanization above every character."),
 ("Is there a version for Safari on the iPhone?",
  "Not yet. It is planned inside the Tova app for iPhone."),
]

def build():
    e = lambda s: html.escape(s, quote=False)
    a = lambda s: html.escape(s, quote=True)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Tova Translate", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Browser extension", "item": URL}]},
        {"@type": "WebPage", "@id": URL + "#page", "url": URL, "name": TITLE, "description": DESC, "inLanguage": "en",
         "about": {"@id": f"{BASE}/#app"}, "primaryImageOfPage": f"{BASE}/media/app/browser-word-card.webp"},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in FAQ]},
    ]}
    cards = '\n'.join(f'        <div class="card"><h3>{e(t)}</h3><p>{e(b)}</p></div>' for t, b in CARDS)
    shots = '\n'.join(f'        <figure><img src="/media/app/{s}.webp" width="960" height="600" loading="lazy" decoding="async" alt="{a(alt)}"><figcaption>{e(c)}</figcaption></figure>' for s, c, alt in SHOTS)
    qa = '\n'.join(f'      <div class="qa">\n        <h3>{e(q)}</h3>\n        <p>{e(ans)}</p>\n      </div>' for q, ans in FAQ)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(TITLE)}</title>
<meta name="description" content="{a(DESC)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0B5F8A">
<link rel="canonical" href="{URL}">
<link rel="icon" type="image/png" sizes="48x48" href="/media/favicon-48.png"><link rel="apple-touch-icon" href="/media/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tova Translate">
<meta property="og:title" content="{a(TITLE)}">
<meta property="og:description" content="{a(DESC)}">
<meta property="og:url" content="{URL}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}{EXTRA}</style>
</head>
<body>
<!--tv:header--><!--/tv:header-->

<main>
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Tova Translate</a> › Browser extension</nav>
  <header class="hero hx">
    <div>
      <h1>Tova for Chrome and Safari</h1>
      <p class="lede">Read Chinese on any web page: point at a word for its pinyin in tone colours and its meanings. Translate what you highlight, and write replies in Chinese, Japanese or Korean.</p>
      {ctas()}
      <p class="note">{e(NOTE)}</p>
    </div>
    <img class="wide" src="/media/app/browser-word-card.webp" width="918" height="558" fetchpriority="high" decoding="async" alt="A Chinese web page with a Tova word card for 躺平 showing tǎng píng in tone colours and its meanings">
  </header>
</div>

<div class="band">
  <div class="wrap">

    <section class="sec">
      <span class="kicker">What it does</span>
      <h2>Chinese, Japanese and Korean on every page you read.</h2>
      <div class="grid g3">
{cards}
      </div>
    </section>

    <section class="sec">
      <span class="kicker">See it</span>
      <h2>What it looks like on a page.</h2>
      <div class="bshots">
{shots}
      </div>
    </section>

    <section class="sec" id="setup">
      <span class="kicker">Set up</span>
      <h2>Install it in a minute.</h2>
      <div class="grid">
        <div class="card"><h3>Chrome (Windows and Mac)</h3>
          <ol>
            <li>Add Tova Translate from the Chrome Web Store.</li>
            <li>Pin it from the puzzle-piece menu so the Tova icon stays in the toolbar.</li>
            <li>Open any Chinese page and rest the pointer on a word. Click the Tova icon for settings: tone colours, Jyutping, the language you translate into.</li>
          </ol>
        </div>
        <div class="card"><h3>Safari (Mac)</h3>
          <ol>
            <li>Install Tova Translate from the Mac App Store and open it once.</li>
            <li>Click “Open Safari Settings”, tick Tova Translate under Extensions and allow it on all websites.</li>
            <li>Open any Chinese page and rest the pointer on a word.</li>
          </ol>
        </div>
      </div>
      <p style="margin-top:18px">Keyboard shortcuts: <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>T</kbd> translates the highlighted text, <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>Y</kbd> translates what you are typing, <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> adds readings, <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>W</kbd> turns word cards on or off. On a Mac, Alt is Option.</p>
    </section>

    <section class="sec">
      <span class="kicker">Free and Pro</span>
      <h2>Most of it is free.</h2>
      <div class="price">
        <div class="card"><p class="big">Free</p><p>Word cards and readings on the page, as much as you like. 20 translations or replies a day.</p></div>
        <div class="card dark"><p class="big">Tova Pro</p><p>No daily limit. Already have Pro on your iPhone? Use it here: link Chrome with a code from the Tova app, or use the same Apple Account on your Mac. <a href="/#plans" style="color:#fff">See the plans</a>.</p></div>
      </div>
    </section>

    <section class="sec">
      <span class="kicker">Privacy</span>
      <h2>What stays on your computer.</h2>
      <ul class="list">
        <li>Word cards are looked up on your computer. Pointing at a word sends nothing.</li>
        <li>Text goes to Tova's server only when you translate or reply, and only that text.</li>
        <li>No account and no sign-in. Details in the <a href="/privacy/#chrome-extension">privacy policy</a>.</li>
      </ul>
    </section>

    <section class="sec">
      <span class="kicker">Questions</span>
      <h2>Questions people ask.</h2>
{qa}
    </section>

  </div>
</div>

<div class="end">
  <div class="wrap">
    <h2>On your phone too.</h2>
    <p>The Tova app reads signs and menus with the camera, translates conversations and works offline in China.</p>
    <div class="ctas"><a class="cta" href="{IPHONE}" target="_blank" rel="noopener"><span><small>Download on the</small>App Store</span></a> <a class="cta" href="https://play.google.com/store/apps/details?id=com.tovatranslate.app" target="_blank" rel="noopener"><span><small>Get it on</small>Google Play</span></a></div>
  </div>
</div>
</main>

<!--tv:footer--><!--/tv:footer-->
</body>
</html>
'''

os.makedirs(os.path.join(ROOT, 'browser-extension'), exist_ok=True)
open(os.path.join(ROOT, 'browser-extension', 'index.html'), 'w', encoding='utf-8').write(build())
print('wrote browser-extension/index.html', 'chrome:', bool(CHROME), 'mac:', bool(MAC))
