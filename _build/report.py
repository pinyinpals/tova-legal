# -*- coding: utf-8 -*-
"""Per-URL content report for every URL in sitemap.xml.

Columns: status (200 if the file exists on disk, which is what GitHub Pages
serves), title length, meta-description length, words (characters for
zh / ja / th, which do not space-separate words), inbound internal links
(distinct OTHER pages that link to the URL), and <img>/<svg role=img> count.

    python3 _build/report.py [site_root] > report.json

Written 2026-09-30 for the site-structure pass, so a before/after table can
be produced from two checkouts with the same code.
"""
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://tovatranslate.app'
SKIP = {'.git', '_build', 'media', 'node_modules'}
CHAR_LANGS = ('zh', 'ja', 'th')
_CJK = re.compile(r'[぀-ヿ㐀-䶿一-鿿豈-﫿'
                  r'가-힯฀-๿]')


def visible(s):
    # Page content only: site chrome (header, footer, old topbar) is excluded
    # so a new site-wide footer does not inflate every page's count.
    s = re.sub(r'(?is)<(script|style|noscript|svg|header|footer)\b[^>]*>.*?</\1>', ' ', s)
    s = re.sub(r'(?is)<div class="topbar">.*?</div>', ' ', s)
    s = re.sub(r'(?is)<div class="brand-row">.*?<span class="eyebrow">', ' ', s)
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    return html.unescape(s)


def measure(t, lang):
    if lang.startswith(CHAR_LANGS):
        # Character count, whitespace excluded — the convention for CJK/Thai.
        return len(re.sub(r'\s+', '', t)), 'chars'
    return len(_CJK.sub(' ', t).split()) + len(_CJK.findall(t)), 'words'


def url_for(rel_dir):
    return f'{BASE}/' if rel_dir in ('', '.') else f'{BASE}/{rel_dir}/'


def norm(href, here):
    href = href.split('#')[0].split('?')[0]
    if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
        return None
    if href.startswith(BASE):
        href = href[len(BASE):]
    if href.startswith('//') or re.match(r'^[a-z]+:', href):
        return None
    if not href.startswith('/'):
        href = here.replace(BASE, '').rsplit('/', 1)[0] + '/' + href
    if not href.endswith('/') and '.' not in href.rsplit('/', 1)[-1]:
        href += '/'
    return BASE + href


def main():
    pages = {}
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP]
        if 'index.html' in files:
            rel = os.path.relpath(d, ROOT)
            pages[url_for(rel)] = open(os.path.join(d, 'index.html'),
                                       encoding='utf-8').read()
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    sm = [e.text.strip() for e in
          ET.parse(os.path.join(ROOT, 'sitemap.xml')).getroot().iter(ns + 'loc')]

    inbound = {u: set() for u in pages}
    for u, s in pages.items():
        for href in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', s, re.I):
            t = norm(html.unescape(href), u)
            if t and t != u and t in inbound:
                inbound[t].add(u)

    out = []
    for u in sm:
        s = pages.get(u)
        if s is None:
            out.append(dict(url=u, status=404))
            continue
        lang = (re.search(r'<html[^>]*\blang="([^"]+)"', s) or [None, ''])[1]
        title = re.search(r'<title[^>]*>(.*?)</title>', s, re.S)
        desc = re.search(r'<meta name="description" content="([^"]*)"', s)
        n, unit = measure(visible(s), lang)
        imgs = len([i for i in re.findall(r'<img\b[^>]*>', s, re.I) if 'tova-icon' not in i]) + len(
            re.findall(r'<svg\b[^>]*(?:role="img"|aria-label=)', s, re.I))
        out.append(dict(
            url=u, status=200, lang=lang,
            title=len(html.unescape(title.group(1)).strip()) if title else 0,
            desc=len(html.unescape(desc.group(1))) if desc else 0,
            size=n, unit=unit, inbound=len(inbound[u]), images=imgs))
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
