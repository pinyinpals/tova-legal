# Publishing a dated translation (run by scheduled cloud routines)

The routine prompt gives: SLUG (guide slug), TITLE, LANG (one language folder code, e.g. `ko`) and DATE (YYYY-MM-DD).
The translation is already on main in `translate/i18n/LANG.json` with `"publishOn": DATE`; `translate/build.js` only
builds a translation once that date has arrived (UTC). Only build and publish. Do not edit wording or data.
One new page per release, on purpose (the owner paces new pages to avoid looking like scaled content).
If any check fails, do not push, and end your reply with "NOT PUBLISHED:" and the reason.

1. `git fetch origin` and `git checkout -B publish origin/main`.
   - `python3 -c "import json;print(json.load(open('translate/i18n/LANG.json'))['guides']['SLUG']['publishOn'])"` must print
     `DATE`, and `translate/SLUG/index.html` must exist.
2. Build: `node translate/build.js` (it regenerates ALL guide pages without the site header/footer).
   - Keep ONLY: new or changed `index.html` files under `LANG/translate/`, plus `translate/SLUG/index.html` and
     `translate/index.html`. (Other pages in that language folder change because their "related guides" cards now point
     to the new page.) Restore every other changed tracked file with `git checkout -- <file>` and delete any other new
     untracked file or folder the build created.
   - Fill the header/footer on the kept pages:
     `python3 -c "import sys,subprocess; sys.path.insert(0,'_build'); import chrome; ch=subprocess.run(['git','status','--porcelain','--untracked-files=all'],capture_output=True,text=True).stdout.split(chr(10)); P=sorted(l[3:] for l in ch if l[3:].endswith('index.html')); [chrome.process(p, p.rsplit('/index.html',1)[0]) for p in P]; print(P)"`
   - `python3 _build/sitemap.py`
   - `python3 _build/audit.py --problems`: the last line must say `0 with findings`.
3. Checks:
   - `LANG/translate/SLUG/index.html` exists, and `grep -o hreflang= LANG/translate/SLUG/index.html | wc -l` is at least 3.
   - `grep -c 'LANG/translate/SLUG/' sitemap.xml` is 1.
   - No other translation went live by accident: `ls -d */translate/SLUG/` lists only languages whose publishOn for SLUG
     is DATE or earlier.
   - `git status --short` lists only files under `LANG/translate/`, `translate/SLUG/`, `translate/index.html` and `sitemap.xml`.
4. Commit "TITLE: <language name> version live" and `git push origin HEAD:main`. If the push is rejected because main
   moved: `git fetch origin`, `git rebase origin/main`, rerun the audit, push once more.
5. Poll `curl -s -o /dev/null -w '%{http_code}' https://tovatranslate.app/LANG/translate/SLUG/` every 15 s, up to
   10 minutes, until 200.
6. `node indexnow.js https://tovatranslate.app/LANG/translate/SLUG/ https://tovatranslate.app/translate/SLUG/`
   (never run indexnow.js without arguments).
7. Report: commit hash on main, HTTP status and <title> of the new page, IndexNow result.
