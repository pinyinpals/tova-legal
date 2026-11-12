#!/usr/bin/env python3
"""Build the Tova Keyboard page in every language listed in keyboard/_strings.json.

    python3 _build/keyboard_page.py            # writes keyboard/ (en) and <lang>/keyboard/
    python3 _build/chrome.py ...               # NOT over the whole site — see below

Text lives in keyboard/_strings.json (one object per language, same keys as "en").
The page's styles are kept in this file (CSS below). Each page carries empty
<!--tv:header--> / <!--tv:footer--> markers; fill them for the pages written here only:

    python3 -c "import sys,os;sys.path.insert(0,'_build');import chrome;\
[chrome.process(os.path.join(chrome.ROOT,p,'index.html'),p) for p in ['keyboard','zh-cn/keyboard','ko/keyboard']]"

(Running chrome.py over the whole site rewrites whitespace in other pages.)
A new language means a NEW PAGE: add one or two per deploy (owner's pacing rule).
"""
import html, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://tovatranslate.app'
APP_STORE = 'https://apps.apple.com/us/app/tova-translate/id6764455741'
PLAY = 'https://play.google.com/store/apps/details?id=com.tovatranslate.app'
HREFLANG = {'en': 'en', 'zh-cn': 'zh-Hans', 'ko': 'ko'}
OG_LOCALE = {'en': 'en_US', 'zh-cn': 'zh_CN', 'ko': 'ko_KR'}
# iPhone capture per page (real captures; zh-cn/ko have localized keyboards).
IPHONE = {'en': 'keyboard', 'zh-cn': 'keyboard-zh-cn', 'ko': 'keyboard-ko'}
ANDROID = {'en': 'keyboard-android', 'zh-cn': 'keyboard-android-zh-cn', 'ko': 'keyboard-android-ko'}

APPLE = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 12.5c0-2.5 2-3.7 2.1-3.8-1.1-1.7-2.9-1.9-3.5-1.9-1.5-.2-2.9.9-3.7.9-.8 0-1.9-.9-3.2-.9-1.7 0-3.2 1-4.1 2.5-1.7 3-.4 7.4 1.3 9.8.8 1.2 1.8 2.5 3.1 2.5 1.2-.1 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8-.1 0-2.6-1-2.7-3.9zM15 4.5c.7-.8 1.1-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>')
GPLAY = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M22.018 13.298l-3.919 2.218-3.515-3.493 3.543-3.521 3.891 2.202a1.49 1.49 0 0 1 0 2.594zM1.337.924a1.486 1.486 0 0 0-.112.568v21.017c0 .217.045.419.124.6l11.155-11.087L1.337.924zm12.207 10.065l3.258-3.238L3.45.195a1.466 1.466 0 0 0-.946-.179l11.04 10.973zm0 2.067l-11 10.933c.298.036.612-.016.906-.183l13.324-7.54-3.23-3.21z"/></svg>')

CSS = open(os.path.join(ROOT, '_build', 'keyboard_page.css'), encoding='utf-8').read()


def url(lang):
    return f'{BASE}/keyboard/' if lang == 'en' else f'{BASE}/{lang}/keyboard/'


def build(lang, T, langs):
    e = lambda k: html.escape(T[k], quote=False)      # plain text
    a = lambda k: html.escape(T[k], quote=True)       # attribute
    h = lambda k: T[k]                                # may hold <strong>/<a>
    home = '/' if lang == 'en' else f'/{lang}/'

    def ctas():
        return (f'<div class="ctas">\n'
                f'        <a class="cta" href="{APP_STORE}" target="_blank" rel="noopener" aria-label="{a("aria_apple")}">{APPLE}<span><small>{e("badge_apple_small")}</small>App Store</span></a>\n'
                f'        <a class="cta" href="{PLAY}" target="_blank" rel="noopener" aria-label="{a("aria_play")}">{GPLAY}<span><small>{e("badge_play_small")}</small>Google Play</span></a>\n'
                f'      </div>')

    def shot(src, label, alt_key):
        return (f'<figure><img src="/media/app/{src}.webp" width="280" height="608" loading="lazy" decoding="async" '
                f'alt="{a(alt_key)}"><figcaption>{label}</figcaption></figure>')

    faq = [(T[f'q{i}'], T[f'a{i}']) for i in range(1, 6)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Tova Translate", "item": BASE + home},
            {"@type": "ListItem", "position": 2, "name": T['crumb_here'], "item": url(lang)}]},
        {"@type": "WebPage", "@id": url(lang) + "#page", "url": url(lang), "name": T['title'],
         "description": T['desc'], "inLanguage": HREFLANG[lang],
         "about": {"@id": f"{BASE}/#app"},
         "primaryImageOfPage": f"{BASE}/media/app/{IPHONE[lang]}.webp"},
        {"@type": "HowTo", "name": T['howto_name'], "step": [
            {"@type": "HowToStep", "position": 1, "name": T['s1_t'], "text": T['howto_1']},
            {"@type": "HowToStep", "position": 2, "name": T['s2_t'], "text": T['howto_2']},
            {"@type": "HowToStep", "position": 3, "name": T['s3_t'], "text": T['howto_3']}]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in faq]},
    ]}
    alts = '\n'.join(f'<link rel="alternate" hreflang="{HREFLANG[l]}" href="{url(l)}">' for l in langs)
    alts += f'\n<link rel="alternate" hreflang="x-default" href="{url("en")}">'
    qa = '\n'.join(f'''      <div class="qa">
        <h3>{html.escape(q, quote=False)}</h3>
        <p>{html.escape(ans, quote=False)}</p>
      </div>''' for q, ans in faq)
    cards = '\n'.join(f'        <div class="card"><h3>{e(f"c{i}_t")}</h3><p>{e(f"c{i}_b")}</p></div>' for i in range(1, 7))

    return f'''<!DOCTYPE html>
<html lang="{HREFLANG[lang]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e("title")}</title>
<meta name="description" content="{a("desc")}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0B5F8A">
<meta name="apple-itunes-app" content="app-id=6764455741">
<link rel="canonical" href="{url(lang)}">
{alts}
<link rel="icon" type="image/png" sizes="48x48" href="/media/favicon-48.png"><link rel="apple-touch-icon" href="/media/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tova Translate">
<meta property="og:title" content="{a("title")}">
<meta property="og:description" content="{a("desc")}">
<meta property="og:url" content="{url(lang)}">
<meta property="og:locale" content="{OG_LOCALE[lang]}">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{a("title")}">
<meta name="twitter:description" content="{a("desc")}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<!--tv:header--><!--/tv:header-->

<main>
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">{e("crumb_home")}</a> › {e("crumb_here")}</nav>
  <header class="hero">
    <div>
      <h1>{e("h1")}</h1>
      <p class="lede">{e("lede")}</p>
      {ctas()}
      <p class="note">{e("note")}</p>
    </div>
    <div class="devs">
      <figure class="dev"><img src="/media/app/{IPHONE[lang]}.webp" width="280" height="608" fetchpriority="high" decoding="async" alt="{a("alt_iphone")}"><figcaption>{e("cap_iphone")}</figcaption></figure>
      <figure class="dev"><img src="/media/app/{ANDROID[lang]}.webp" width="280" height="622" decoding="async" alt="{a("alt_android")}"><figcaption>{e("cap_android")}</figcaption></figure>
    </div>
  </header>
</div>

<div class="band">
  <div class="wrap">

    <section class="sec">
      <span class="kicker">{e("how_k")}</span>
      <h2>{e("how_h")}</h2>
      <p>{e("how_p")}</p>
      <ol class="steps">
        <li><b>{e("s1_t")}</b><span>{e("s1_b")}</span></li>
        <li><b>{e("s2_t")}</b><span>{e("s2_b")}</span></li>
        <li><b>{e("s3_t")}</b><span>{e("s3_b")}</span></li>
      </ol>
    </section>

    <section class="sec">
      <span class="kicker">{e("does_k")}</span>
      <h2>{e("does_h")}</h2>
      <div class="grid g3">
{cards}
      </div>
    </section>

    <section class="sec">
      <span class="kicker">{e("lang_k")}</span>
      <h2>{e("lang_h")}</h2>
      <p>{e("lang_p")}</p>
      <div class="shots">
        {shot("keyboard-ja", "日本語", "g_alt_ja")}
        {shot("keyboard-ko", "한국어", "g_alt_ko")}
        {shot("keyboard-de", "Deutsch", "g_alt_de")}
        {shot("keyboard-es", "Español", "g_alt_es")}
        {shot("keyboard-fr", "Français", "g_alt_fr")}
      </div>
    </section>

    <section class="sec" id="setup">
      <span class="kicker">{e("setup_k")}</span>
      <h2>{e("setup_h")}</h2>
      <p>{h("setup_p")}</p>
      <div class="grid">
        <div class="card"><h3>{e("ios_t")}</h3>
          <ol>
            <li>{h("ios_1")}</li>
            <li>{h("ios_2")}</li>
            <li>{h("ios_3")}</li>
            <li>{h("ios_4")}</li>
          </ol>
        </div>
        <div class="card"><h3>{e("and_t")}</h3>
          <ol>
            <li>{h("and_1")}</li>
            <li>{h("and_2")}</li>
            <li>{h("and_3")}</li>
          </ol>
        </div>
      </div>
    </section>

    <section class="sec">
      <span class="kicker">{e("cost_k")}</span>
      <h2>{e("cost_h")}</h2>
      <div class="price">
        <div class="card"><p class="big">{e("free_big")}</p><p>{e("free_p")}</p></div>
        <div class="card dark"><p class="big">{e("pro_big")}</p><p>{e("pro_p")} <a href="{home}#plans" style="color:#fff">{e("pro_link")}</a>.</p></div>
      </div>
    </section>

    <section class="sec">
      <span class="kicker">{e("priv_k")}</span>
      <h2>{e("priv_h")}</h2>
      <p>{e("priv_p")}</p>
      <ul class="list">
        <li>{h("priv_1")}</li>
        <li>{h("priv_2")}</li>
        <li>{h("priv_3")}</li>
      </ul>
    </section>

    <section class="sec">
      <span class="kicker">{e("gtk_k")}</span>
      <h2>{e("gtk_h")}</h2>
      <ul class="list">
        <li>{h("gtk_1")}</li>
        <li>{h("gtk_2")}</li>
        <li>{h("gtk_3")}</li>
      </ul>
    </section>

    <section class="sec">
      <span class="kicker">{e("q_k")}</span>
      <h2>{e("q_h")}</h2>
{qa}
      <p style="margin-top:22px">{h("faq_more")}</p>
    </section>

  </div>
</div>

<div class="end">
  <div class="wrap">
    <h2>{e("end_h")}</h2>
    <p>{e("end_p")}</p>
    {ctas()}
  </div>
</div>
</main>

<!--tv:footer--><!--/tv:footer-->
<!--zet-beacon--><script>(function(){{try{{var u="https://zet-scan.fly.dev/api/hit",d=JSON.stringify({{p:"tovatranslate.app"+location.pathname,r:document.referrer||"",s:new URLSearchParams(location.search).get("src")||""}});if(!(navigator.sendBeacon&&navigator.sendBeacon(u,new Blob([d],{{type:"text/plain"}}))))fetch(u,{{method:"POST",body:d,keepalive:true,mode:"no-cors",headers:{{"content-type":"text/plain"}}}});}}catch(e){{}}}})();</script>
</body>
</html>
'''


def main():
    S = json.load(open(os.path.join(ROOT, 'keyboard', '_strings.json'), encoding='utf-8'))
    langs = [l for l in ('en', 'zh-cn', 'ko') if l in S]
    for lang in langs:
        missing = set(S['en']) - set(S[lang])
        assert not missing, (lang, missing)
        out = os.path.join(ROOT, 'keyboard' if lang == 'en' else f'{lang}/keyboard')
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(build(lang, S[lang], langs))
        print('wrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
