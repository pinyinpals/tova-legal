# -*- coding: utf-8 -*-
"""Static SEO audit of the built site.

Reports, per URL: on-disk status, <html lang>, canonical, hreflang count,
x-default presence, title length, word count, and whether the page is in
sitemap.xml. Written 2026-09-26 while diagnosing 45 "Discovered - currently
not indexed" pages in Search Console.

    python3 _build/audit.py            # table
    python3 _build/audit.py --problems # only rows with findings
"""
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://tovatranslate.app'
SKIP_DIRS = {'.git', '_build', 'media', 'lexicon', 'node_modules'}


# CJK and Thai do not put spaces between words, so whitespace splitting
# undercounts them by roughly 2-4x and makes a perfectly normal Chinese page
# look thin. Count CJK ideographs, kana and Thai characters individually and
# add them to the whitespace-token count for everything else.
_CJK = re.compile(
    r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff'
    r'\uac00-\ud7af\u0e00-\u0e7f]')


def text_words(s):
    s = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', s)
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    t = html.unescape(s)
    cjk = len(_CJK.findall(t))
    latin = len(_CJK.sub(' ', t).split())
    return latin + cjk


def url_for(path):
    rel = os.path.relpath(path, ROOT)
    d = os.path.dirname(rel)
    return f'{BASE}/' if d in ('', '.') else f'{BASE}/{d}/'


def scan():
    pages = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if 'index.html' not in filenames:
            continue
        p = os.path.join(dirpath, 'index.html')
        s = open(p, encoding='utf-8', errors='replace').read()
        m = re.search(r'<html[^>]*\blang="([^"]+)"', s, re.I)
        canon = re.search(
            r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', s, re.I)
        alts = re.findall(
            r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
            s, re.I)
        # Attribute order varies; catch the reversed spelling too.
        alts += re.findall(
            r'<link[^>]+hreflang="([^"]+)"[^>]+rel="alternate"[^>]+href="([^"]+)"',
            s, re.I)
        title = re.search(r'<title[^>]*>(.*?)</title>', s, re.I | re.S)
        pages[url_for(p)] = dict(
            path=os.path.relpath(p, ROOT),
            lang=m.group(1) if m else '',
            canonical=canon.group(1) if canon else '',
            hreflang={k: v for k, v in alts},
            title=html.unescape(title.group(1)).strip() if title else '',
            words=text_words(s),
            noindex=bool(re.search(r'noindex', s, re.I)),
        )
    return pages


def sitemap_urls():
    f = os.path.join(ROOT, 'sitemap.xml')
    if not os.path.exists(f):
        return set()
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    return {e.text.strip() for e in ET.parse(f).getroot().iter(
        '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}


def main():
    only_problems = '--problems' in sys.argv
    pages = scan()
    sm = sitemap_urls()
    rows, issues = [], []

    for url in sorted(pages):
        p = pages[url]
        probs = []
        if url not in sm and not p['noindex']:
            probs.append('not-in-sitemap')
        if not p['canonical']:
            probs.append('no-canonical')
        elif p['canonical'].rstrip('/') != url.rstrip('/'):
            probs.append(f'canonical→{p["canonical"]}')
        if not p['lang']:
            probs.append('no-lang')
        if p['hreflang'] and 'x-default' not in p['hreflang']:
            probs.append('no-x-default')
        # Reciprocity: every alternate must point back here.
        for code, href in p['hreflang'].items():
            if code == 'x-default':
                continue
            tgt = pages.get(href if href.endswith('/') else href + '/')
            if tgt is None:
                probs.append(f'hreflang→missing({code})')
            elif url not in tgt['hreflang'].values():
                probs.append(f'no-reciprocal({code})')
        if p['words'] < 300 and not p['noindex']:
            probs.append(f'thin({p["words"]}w)')
        if len(p['title']) > 60:
            probs.append(f'title{len(p["title"])}c')
        rows.append((url, p, probs))
        if probs:
            issues.append((url, probs))

    hdr = f'{"URL":<58} {"lang":<7} {"canon":<6} {"hl":>3} {"xdef":<5} {"words":>6}  findings'
    print(hdr)
    print('-' * len(hdr))
    for url, p, probs in rows:
        if only_problems and not probs:
            continue
        short = url.replace(BASE, '') or '/'
        print(f'{short:<58} {p["lang"]:<7} '
              f'{"ok" if p["canonical"] else "MISS":<6} '
              f'{len(p["hreflang"]):>3} '
              f'{"yes" if "x-default" in p["hreflang"] else "no":<5} '
              f'{p["words"]:>6}  {", ".join(probs)}')

    orphan = sorted(u for u in sm if u not in pages)
    print(f'\n{len(pages)} pages on disk · {len(sm)} in sitemap · '
          f'{len(issues)} with findings')
    if orphan:
        print(f'\nIn sitemap but NOT on disk ({len(orphan)}):')
        for u in orphan:
            print('  ', u)


if __name__ == '__main__':
    main()
