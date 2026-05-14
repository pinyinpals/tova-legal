#!/usr/bin/env python3
"""Generate localized versions of index.html for 13 locales.

Strategy: marker-based string replacement against the English source so the
canonical English page stays the single source of truth. Each locale gets its
own subpath (/zh-cn/, /ja/, ...) so Google indexes them as distinct pages
with proper hreflang signalling.

To re-run after copy changes:
    python3 _build/build_locales.py
"""
import json, pathlib, re, html as html_lib

ROOT = pathlib.Path(__file__).resolve().parent.parent
_RAW = (ROOT / "index.html").read_text(encoding="utf-8")

# Idempotency: strip any previously-injected hreflang block + switcher CSS +
# switcher band so re-running the build doesn't double-insert.
_RAW = re.sub(r'\n?<link rel="alternate" hreflang="[^"]+" href="[^"]+">', '', _RAW)
_RAW = re.sub(r'\n?\s*/\* ===== Language switcher band =====.*?\n}\n', '', _RAW, flags=re.DOTALL)
_RAW = re.sub(r'<section class="lang-switcher-band">.*?</section>\n?', '', _RAW, flags=re.DOTALL)

TEMPLATE = _RAW

# ─── Locale registry ──────────────────────────────────────────────
# slug = URL subpath, lang = BCP-47 for <html lang>, hreflang = BCP-47 for
# <link rel="alternate" hreflang>. native = native name shown in the
# language switcher.
LOCALES = [
    {"slug": "zh-cn",  "lang": "zh-Hans", "hreflang": "zh-Hans", "native": "简体中文"},
    {"slug": "zh-tw",  "lang": "zh-Hant", "hreflang": "zh-Hant", "native": "繁體中文"},
    {"slug": "ja",     "lang": "ja",      "hreflang": "ja",      "native": "日本語"},
    {"slug": "ko",     "lang": "ko",      "hreflang": "ko",      "native": "한국어"},
    {"slug": "es",     "lang": "es",      "hreflang": "es",      "native": "Español"},
    {"slug": "fr",     "lang": "fr",      "hreflang": "fr",      "native": "Français"},
    {"slug": "de",     "lang": "de",      "hreflang": "de",      "native": "Deutsch"},
    {"slug": "pt",     "lang": "pt",      "hreflang": "pt",      "native": "Português"},
    {"slug": "it",     "lang": "it",      "hreflang": "it",      "native": "Italiano"},
    {"slug": "th",     "lang": "th",      "hreflang": "th",      "native": "ไทย"},
    {"slug": "vi",     "lang": "vi",      "hreflang": "vi",      "native": "Tiếng Việt"},
    {"slug": "id",     "lang": "id",      "hreflang": "id",      "native": "Bahasa Indonesia"},
    {"slug": "tl",     "lang": "tl",      "hreflang": "tl",      "native": "Filipino"},
]

# ─── English source-of-truth keys ─────────────────────────────────
# Each value here MUST match the exact text in index.html so we can find +
# replace it. If the English page is edited, sync the keys here too.
EN_STRINGS = {
    # head
    "title":         "Tova Translate — Camera & Voice Translator That Works Offline in China (No VPN)",
    "meta_desc":     "Camera + voice translator for travel in China and Asia. Hanyu Pinyin for Mandarin, Jyutping for Cantonese, 118 languages, Pro Plus 3-way Boardroom. Offline in China — no VPN.",
    "og_title":      "Tova Translate — Mandarin, Cantonese & 118 Languages, Offline in China",
    "og_desc":       "Scan menus and signs. Speak with anyone. Real Hanyu Pinyin for Mandarin, real Jyutping for Cantonese, Pro Plus three-way Boardroom mode. Works offline in China — no VPN.",
    "tw_title":      "Tova — Mandarin, Cantonese & 118 languages, offline in China",
    "tw_desc":       "Camera + voice + text translator. Hanyu Pinyin for Mandarin, Jyutping for Cantonese, Pro Plus three-way Boardroom. Works in China — no VPN.",
    # hero
    "eyebrow":       "Built for travellers · Asia · MENA · Europe",
    "h1_a":          "Read any sign. Speak with anyone.",
    "h1_b":          "Even in China — no VPN.",
    "store_dl_on":   "Download on the",
    "store_get_on":  "Get it on",
    "reassure_free": "Free to download",
    "reassure_nosignup": "No sign-up required",
    "reassure_china":   "Works in China — no VPN",
    "usecases_label":  "Use it to",
    "uc_food":        "Order food",
    "uc_taxi":        "Hail a taxi",
    "uc_contracts":   "Read contracts",
    "uc_friends":     "Make friends",
    "uc_hotels":      "Check in at hotels",
    "uc_signs":       "Read museum signs",
    # shot captions (3 phones)
    "shot1_strong":  "Live camera OCR",
    "shot1_body":    "Detected text + per-character pinyin in a single dark panel at the bottom of the camera screen — speak / show / save / copy actions and a STABLE READ pill on the high-confidence line.",
    "shot2_strong":  "Three speakers, one conversation",
    "shot2_body":    "Pro Plus Boardroom mode hears all three languages and translates between them — perfect for cross-border meetings.",
    "shot3_strong":  "Two-way voice translation",
    "shot3_body":    "Speak naturally — see the pinyin reading and translation in seconds, then tap Listen to hear it spoken back.",
    # dialects band
    "dial_eyebrow":  "Mandarin or Cantonese?",
    "dial_h2":       "Tova does both — with the right romanization for each.",
    "dial_p1_a":     "Other apps treat Chinese as one language and slap pinyin on every character.",
    "dial_p1_b":     "Tova doesn't. Pick 简体中文 and you get real",
    "dial_p1_c":     "above every character. Pick 廣東話 and you get real",
    "dial_p1_d":     "the romanization Hong Kong Cantonese speakers actually use.",
    "dial_p2":       "Same English question, two dialects, two correct readings — built in, no settings to tweak.",
    # features band
    "feat_eyebrow":  "What's inside",
    "feat_h2":       "A travel translator that doesn't quit at the border.",
    "feat_lead":     "A signage-first OCR engine, an offline-first translation pipeline, and a conversational mode that respects how people really talk.",
    "feat1_title":   "Live camera OCR — 11 scripts",
    "feat1_body":    "Point. See. Read. CJK, Thai, Arabic, Hebrew, Devanagari, Tibetan and more, with per-character pinyin, romaji, and hangeul rendered above each glyph in real time.",
    "feat2_title":   "Two-way voice translation",
    "feat2_body":    "On-device speech recognition, natural voice playback, and a Pro Plus 3-way Boardroom mode for meetings with speakers across three languages.",
    "feat3_title":   "Works in China — no VPN",
    "feat3_body":    "When the backend is unreachable, on-device neural translation kicks in automatically. Apple Translation on iOS, ML Kit on Android. No setup, no detours.",
    "feat4_title":   "29 offline phrase packs",
    "feat4_body":    "Curated travel phrases plus the full CC-CEDICT Chinese dictionary. Download once, use forever — no cell signal required to find the bathroom.",
    # cta band
    "cta_h2_a":      "Pack lighter. Travel further.",
    "cta_h2_b":      "Talk to anyone.",
    "cta_lead":      "Free to download. No accounts, no sign-up. Take Tova on your next trip and never get lost in translation again.",
    "cta_reassure_free": "Free download",
    # language switcher
    "lang_switcher_label": "Read this page in",
    "view_english":  "Read in English",
}

# ─── Translations ─────────────────────────────────────────────────
# LLM-quality translations awaiting native-speaker review.
# Branded terms kept English/native script: "Tova", "Pro Plus", "Boardroom",
# "Hanyu Pinyin", "Jyutping", "Apple Translation", "ML Kit", "CC-CEDICT".
# Native-script tags (简体中文, 廣東話) kept as-is across all locales.
T = {}

T["zh-cn"] = {
    "title": "Tova Translate — 让你在中国离线翻译的相机+语音翻译应用(无需 VPN)",
    "meta_desc": "面向亚洲旅行的相机+语音翻译应用。普通话配真正的汉语拼音,粤语配真正的粤拼,118 种语言,Pro Plus 三方会议室模式。在中国离线可用——无需 VPN。",
    "og_title": "Tova Translate — 普通话、粤语和 118 种语言,中国离线可用",
    "og_desc": "扫描菜单和路牌。和任何人交谈。普通话配真正的汉语拼音,粤语配真正的粤拼,Pro Plus 三方会议室模式。在中国离线可用——无需 VPN。",
    "tw_title": "Tova — 普通话、粤语和 118 种语言,中国离线可用",
    "tw_desc": "相机+语音+文本翻译。普通话配汉语拼音,粤语配粤拼,Pro Plus 三方会议室模式。在中国可用——无需 VPN。",
    "eyebrow": "为旅行者打造 · 亚洲 · 中东北非 · 欧洲",
    "h1_a": "看懂每一块标牌。和任何人交谈。",
    "h1_b": "在中国也行——无需 VPN。",
    "store_dl_on": "在以下平台下载",
    "store_get_on": "在以下平台获取",
    "reassure_free": "免费下载",
    "reassure_nosignup": "无需注册",
    "reassure_china": "在中国可用——无需 VPN",
    "usecases_label": "用它来",
    "uc_food": "点餐",
    "uc_taxi": "叫出租车",
    "uc_contracts": "阅读合同",
    "uc_friends": "结交朋友",
    "uc_hotels": "酒店办理入住",
    "uc_signs": "看博物馆说明",
    "shot1_strong": "实时相机识别",
    "shot1_body": "识别出的文字和逐字拼音显示在相机界面底部的深色面板中——支持朗读 / 显示 / 保存 / 复制操作,稳定识别行旁还会显示 STABLE READ 徽章。",
    "shot2_strong": "三个人,一场对话",
    "shot2_body": "Pro Plus 会议室模式同时识别三种语言并在它们之间翻译——非常适合跨境会议。",
    "shot3_strong": "双向语音翻译",
    "shot3_body": "自然地说——几秒内就能看到拼音读音和译文,点击 Listen 即可听到译文朗读。",
    "dial_eyebrow": "普通话还是粤语?",
    "dial_h2": "Tova 两者都支持——每种语言都配有正确的罗马化方式。",
    "dial_p1_a": "其他应用把中文当作一种语言,在每个字上都标拼音。",
    "dial_p1_b": "Tova 不一样。选择简体中文,你会看到真正的",
    "dial_p1_c": "在每个字上方。选择廣東話,你会看到真正的",
    "dial_p1_d": "这才是香港粤语使用者真正使用的罗马拼音。",
    "dial_p2": "同样的英文问题,两种方言,两种正确读法——内置支持,无需设置。",
    "feat_eyebrow": "应用内置",
    "feat_h2": "不会在国界停下的旅行翻译应用。",
    "feat_lead": "以标牌识别为核心的 OCR 引擎,以离线为优先的翻译流程,以及尊重真实对话方式的对话模式。",
    "feat1_title": "实时相机 OCR —— 11 种文字",
    "feat1_body": "对准。看见。读懂。中日韩、泰文、阿拉伯文、希伯来文、天城体、藏文等,实时在每个字符上方显示拼音、罗马音和谚文读音。",
    "feat2_title": "双向语音翻译",
    "feat2_body": "设备端语音识别,自然语音回放,加上 Pro Plus 三方 Boardroom 会议室模式,可用于三种语言之间的会议。",
    "feat3_title": "在中国可用 —— 无需 VPN",
    "feat3_body": "当后端无法连接时,自动启用设备端神经翻译。iOS 用 Apple Translation,Android 用 ML Kit。无需设置,无需绕路。",
    "feat4_title": "29 个离线短语包",
    "feat4_body": "精心整理的旅行短语,加上完整的 CC-CEDICT 中英词典。下载一次,永久使用——找洗手间不再需要手机信号。",
    "cta_h2_a": "行李轻一些。走得远一些。",
    "cta_h2_b": "和任何人交谈。",
    "cta_lead": "免费下载。无需账户,无需注册。带上 Tova 出发下一段旅程,再也不会在翻译中迷路。",
    "cta_reassure_free": "免费下载",
    "lang_switcher_label": "用其他语言阅读",
    "view_english": "Read in English",
}

T["zh-tw"] = {
    "title": "Tova Translate — 在中國離線可用的相機與語音翻譯應用程式(無需 VPN)",
    "meta_desc": "為亞洲旅行打造的相機+語音翻譯應用程式。普通話配真正的漢語拼音,廣東話配真正的粵拼,118 種語言,Pro Plus 三方會議室模式。在中國離線可用——無需 VPN。",
    "og_title": "Tova Translate — 國語、廣東話及 118 種語言,中國離線可用",
    "og_desc": "掃描菜單和路牌。與任何人交談。普通話配真正的漢語拼音,廣東話配真正的粵拼,Pro Plus 三方會議室模式。在中國離線可用——無需 VPN。",
    "tw_title": "Tova — 國語、廣東話及 118 種語言,中國離線可用",
    "tw_desc": "相機+語音+文字翻譯。普通話配漢語拼音,廣東話配粵拼,Pro Plus 三方會議室模式。在中國可用——無需 VPN。",
    "eyebrow": "為旅行者打造 · 亞洲 · 中東北非 · 歐洲",
    "h1_a": "看懂每一塊招牌。與任何人交談。",
    "h1_b": "在中國也行——無需 VPN。",
    "store_dl_on": "下載自",
    "store_get_on": "取得自",
    "reassure_free": "免費下載",
    "reassure_nosignup": "無需註冊",
    "reassure_china": "在中國可用——無需 VPN",
    "usecases_label": "你可以用來",
    "uc_food": "點餐",
    "uc_taxi": "叫計程車",
    "uc_contracts": "閱讀合約",
    "uc_friends": "結交朋友",
    "uc_hotels": "飯店辦理入住",
    "uc_signs": "閱讀博物館說明",
    "shot1_strong": "即時相機文字辨識",
    "shot1_body": "辨識出的文字與逐字拼音顯示在相機畫面底部的深色面板中——支援朗讀 / 顯示 / 儲存 / 複製功能,穩定辨識的行還會顯示 STABLE READ 標籤。",
    "shot2_strong": "三個人,一場對話",
    "shot2_body": "Pro Plus 會議室模式同時聽懂三種語言並在它們之間翻譯——非常適合跨境會議。",
    "shot3_strong": "雙向語音翻譯",
    "shot3_body": "自然地說——幾秒內就能看到拼音讀音和譯文,點選 Listen 即可聽到譯文朗讀。",
    "dial_eyebrow": "國語還是廣東話?",
    "dial_h2": "Tova 兩者都支援——每種語言都配上正確的羅馬化方式。",
    "dial_p1_a": "其他應用程式把中文當作一種語言,在每個字上都加上拼音。",
    "dial_p1_b": "Tova 不一樣。選擇簡體中文,你會看到真正的",
    "dial_p1_c": "標在每個字上方。選擇廣東話,你會看到真正的",
    "dial_p1_d": "這才是香港粵語使用者真正使用的羅馬拼音。",
    "dial_p2": "同樣的英文問題,兩種方言,兩種正確讀法——內建支援,不必調整任何設定。",
    "feat_eyebrow": "應用程式內建",
    "feat_h2": "不會在國境止步的旅行翻譯應用程式。",
    "feat_lead": "以招牌辨識為核心的 OCR 引擎,以離線為優先的翻譯管線,以及尊重真實對話方式的對話模式。",
    "feat1_title": "即時相機 OCR —— 11 種文字",
    "feat1_body": "對準。看見。讀懂。中日韓、泰文、阿拉伯文、希伯來文、天城體、藏文等,即時在每個字符上方顯示拼音、羅馬音與韓文讀音。",
    "feat2_title": "雙向語音翻譯",
    "feat2_body": "裝置端語音辨識、自然語音回放,加上 Pro Plus 三方 Boardroom 會議室模式,適用於三種語言之間的會議。",
    "feat3_title": "在中國可用 —— 無需 VPN",
    "feat3_body": "當後端無法連線時,自動啟用裝置端神經翻譯。iOS 使用 Apple Translation,Android 使用 ML Kit。不必設定,不必繞路。",
    "feat4_title": "29 個離線短語包",
    "feat4_body": "精心整理的旅行短語,加上完整的 CC-CEDICT 中英詞典。下載一次,永久使用——找洗手間不再需要手機訊號。",
    "cta_h2_a": "行李輕一點。走得遠一點。",
    "cta_h2_b": "與任何人交談。",
    "cta_lead": "免費下載。無需帳號,無需註冊。帶上 Tova 踏上下一段旅程,再也不會迷失在翻譯之中。",
    "cta_reassure_free": "免費下載",
    "lang_switcher_label": "用其他語言閱讀",
    "view_english": "Read in English",
}

T["ja"] = {
    "title": "Tova Translate — 中国でもオフラインで動くカメラ+音声翻訳アプリ(VPN不要)",
    "meta_desc": "中国・アジア旅行のためのカメラ+音声翻訳アプリ。中国語(普通話)はピンイン、広東語はジュッピン、118言語に対応、Pro Plus は3者会議モード。中国でもオフラインで動作 — VPN 不要。",
    "og_title": "Tova Translate — 中国語・広東語・118言語、中国でもオフライン",
    "og_desc": "看板やメニューをスキャン。誰とでも話せる。中国語にはピンイン、広東語にはジュッピン、Pro Plus の3者会議モード搭載。中国でもオフライン動作 — VPN 不要。",
    "tw_title": "Tova — 中国語・広東語・118言語、中国でもオフライン",
    "tw_desc": "カメラ+音声+テキスト翻訳。中国語はピンイン、広東語はジュッピン、Pro Plus 3者会議モード。中国で動作 — VPN 不要。",
    "eyebrow": "旅行者のために · アジア · 中東 · ヨーロッパ",
    "h1_a": "あらゆる看板を読む。誰とでも話す。",
    "h1_b": "中国でも — VPN 不要。",
    "store_dl_on": "ダウンロード",
    "store_get_on": "入手する",
    "reassure_free": "無料ダウンロード",
    "reassure_nosignup": "登録不要",
    "reassure_china": "中国で動作 — VPN 不要",
    "usecases_label": "こんなときに",
    "uc_food": "料理を注文",
    "uc_taxi": "タクシーを呼ぶ",
    "uc_contracts": "契約書を読む",
    "uc_friends": "友達をつくる",
    "uc_hotels": "ホテルでチェックイン",
    "uc_signs": "美術館の説明を読む",
    "shot1_strong": "ライブカメラ OCR",
    "shot1_body": "認識された文字と1文字ごとのピンインが、カメラ画面下部の単一の暗色パネルに表示されます — 読み上げ / 表示 / 保存 / コピーの操作と、認識が安定した行に表示される STABLE READ バッジ。",
    "shot2_strong": "3人の話者、1つの会話",
    "shot2_body": "Pro Plus の Boardroom モードは3言語すべてを聞き取り、それぞれの間を翻訳します — 国境を越えた会議に最適。",
    "shot3_strong": "双方向の音声翻訳",
    "shot3_body": "自然に話すだけ — ピンインの読みと翻訳が数秒で表示され、Listen をタップすれば翻訳を音声で聞けます。",
    "dial_eyebrow": "中国語?それとも広東語?",
    "dial_h2": "Tova はどちらも対応 — 言語ごとに正しいローマ字表記で。",
    "dial_p1_a": "他のアプリは中国語を1つの言語として扱い、すべての文字にピンインを付けます。",
    "dial_p1_b": "Tova は違います。简体中文 を選ぶと、本物の",
    "dial_p1_c": "がすべての字の上に表示されます。廣東話 を選ぶと、本物の",
    "dial_p1_d": "が表示されます — 香港の広東語話者が実際に使うローマ字表記です。",
    "dial_p2": "同じ英語の質問、2つの方言、2つの正しい読み — 標準搭載、設定不要。",
    "feat_eyebrow": "アプリの中身",
    "feat_h2": "国境で止まらない旅行翻訳アプリ。",
    "feat_lead": "看板を最優先に設計した OCR エンジン、オフライン優先の翻訳パイプライン、そして実際の話し方を尊重する会話モード。",
    "feat1_title": "ライブカメラ OCR — 11 種類の文字",
    "feat1_body": "向けるだけで、見て、読める。CJK、タイ語、アラビア語、ヘブライ語、デーヴァナーガリー、チベット語など、ピンイン・ローマ字・ハングルの読みをリアルタイムで各文字の上に表示。",
    "feat2_title": "双方向の音声翻訳",
    "feat2_body": "オンデバイスの音声認識、自然な音声再生、そして3言語の会議に対応する Pro Plus 3-way Boardroom モード。",
    "feat3_title": "中国でも動く — VPN 不要",
    "feat3_body": "バックエンドに接続できない場合、自動的にオンデバイスのニューラル翻訳に切り替わります。iOS は Apple Translation、Android は ML Kit。設定不要、迂回不要。",
    "feat4_title": "29 のオフライン会話集",
    "feat4_body": "厳選された旅行用フレーズに加え、完全な CC-CEDICT 中国語辞典。一度ダウンロードすればずっと使える — トイレを探すのに電波は要りません。",
    "cta_h2_a": "荷物は軽く、もっと遠くへ。",
    "cta_h2_b": "誰とでも話そう。",
    "cta_lead": "無料ダウンロード。アカウント不要、登録不要。次の旅に Tova を連れて行けば、翻訳で迷うことはもうありません。",
    "cta_reassure_free": "無料ダウンロード",
    "lang_switcher_label": "他の言語で読む",
    "view_english": "Read in English",
}

T["ko"] = {
    "title": "Tova Translate — 중국에서도 오프라인으로 작동하는 카메라+음성 번역 앱 (VPN 불필요)",
    "meta_desc": "중국과 아시아 여행을 위한 카메라+음성 번역 앱. 만다린은 한어 병음, 광동어는 정자, 118개 언어, Pro Plus 3자 보드룸 모드. 중국에서도 오프라인 — VPN 불필요.",
    "og_title": "Tova Translate — 만다린, 광동어 및 118개 언어, 중국에서도 오프라인",
    "og_desc": "메뉴와 표지판을 스캔하세요. 누구와도 대화하세요. 만다린에는 한어 병음, 광동어에는 정자, Pro Plus 3자 보드룸 모드. 중국에서도 오프라인 — VPN 불필요.",
    "tw_title": "Tova — 만다린, 광동어 및 118개 언어, 중국에서도 오프라인",
    "tw_desc": "카메라+음성+텍스트 번역. 만다린에는 한어 병음, 광동어에는 정자, Pro Plus 3자 보드룸 모드. 중국에서 작동 — VPN 불필요.",
    "eyebrow": "여행자를 위해 · 아시아 · 중동·북아프리카 · 유럽",
    "h1_a": "어떤 표지판이든 읽고, 누구와도 대화하세요.",
    "h1_b": "중국에서도 — VPN 불필요.",
    "store_dl_on": "다운로드",
    "store_get_on": "받기",
    "reassure_free": "무료 다운로드",
    "reassure_nosignup": "가입 불필요",
    "reassure_china": "중국에서 작동 — VPN 불필요",
    "usecases_label": "이런 일에 사용하세요",
    "uc_food": "음식 주문",
    "uc_taxi": "택시 부르기",
    "uc_contracts": "계약서 읽기",
    "uc_friends": "친구 사귀기",
    "uc_hotels": "호텔 체크인",
    "uc_signs": "박물관 안내문 읽기",
    "shot1_strong": "실시간 카메라 OCR",
    "shot1_body": "인식된 텍스트와 문자별 병음이 카메라 화면 하단의 단일 어두운 패널에 표시됩니다 — 읽기 / 보기 / 저장 / 복사 동작과, 안정적으로 인식된 줄에 표시되는 STABLE READ 배지.",
    "shot2_strong": "세 명의 화자, 하나의 대화",
    "shot2_body": "Pro Plus 보드룸 모드는 세 언어를 모두 듣고 그 사이를 번역합니다 — 국경을 넘는 회의에 최적입니다.",
    "shot3_strong": "양방향 음성 번역",
    "shot3_body": "자연스럽게 말하세요 — 병음 발음과 번역이 몇 초 안에 표시되고, Listen을 탭하면 번역을 음성으로 들을 수 있습니다.",
    "dial_eyebrow": "만다린일까요, 광동어일까요?",
    "dial_h2": "Tova는 둘 다 지원합니다 — 각 언어에 맞는 올바른 로마자 표기로.",
    "dial_p1_a": "다른 앱들은 중국어를 하나의 언어로 다루며 모든 글자에 병음을 표시합니다.",
    "dial_p1_b": "Tova는 다릅니다. 简体中文을 선택하면 진짜",
    "dial_p1_c": "이 모든 글자 위에 표시됩니다. 廣東話를 선택하면 진짜",
    "dial_p1_d": "이 표시됩니다 — 홍콩 광동어 사용자가 실제로 쓰는 로마자 표기입니다.",
    "dial_p2": "같은 영어 질문, 두 가지 방언, 두 가지 올바른 발음 — 기본 내장, 별도 설정 불필요.",
    "feat_eyebrow": "앱에 포함된 기능",
    "feat_h2": "국경에서 멈추지 않는 여행 번역 앱.",
    "feat_lead": "표지판 인식을 우선한 OCR 엔진, 오프라인 우선 번역 파이프라인, 그리고 실제 대화 방식을 존중하는 대화 모드.",
    "feat1_title": "실시간 카메라 OCR — 11종 문자",
    "feat1_body": "겨누고, 보고, 읽으세요. 한·중·일, 태국어, 아랍어, 히브리어, 데바나가리, 티베트어 등, 병음·로마자·한글 발음이 실시간으로 각 글자 위에 표시됩니다.",
    "feat2_title": "양방향 음성 번역",
    "feat2_body": "온디바이스 음성 인식, 자연스러운 음성 재생, 세 언어의 회의를 위한 Pro Plus 3자 Boardroom 모드.",
    "feat3_title": "중국에서 작동 — VPN 불필요",
    "feat3_body": "백엔드에 연결할 수 없을 때, 온디바이스 신경망 번역이 자동으로 작동합니다. iOS는 Apple Translation, Android는 ML Kit. 설정도, 우회도 필요 없습니다.",
    "feat4_title": "29개의 오프라인 구문 팩",
    "feat4_body": "엄선된 여행 구문에 전체 CC-CEDICT 중국어 사전까지. 한 번 다운로드하면 평생 사용 — 화장실을 찾는데 셀룰러 신호가 필요 없습니다.",
    "cta_h2_a": "짐은 가볍게, 더 멀리.",
    "cta_h2_b": "누구와도 대화하세요.",
    "cta_lead": "무료 다운로드. 계정도, 가입도 필요 없습니다. 다음 여행에 Tova를 데려가세요, 더 이상 번역에 막혀 길을 잃지 않습니다.",
    "cta_reassure_free": "무료 다운로드",
    "lang_switcher_label": "다른 언어로 읽기",
    "view_english": "Read in English",
}

T["es"] = {
    "title": "Tova Translate — Traductor de cámara y voz que funciona sin conexión en China (sin VPN)",
    "meta_desc": "Traductor de cámara + voz para viajar a China y Asia. Pinyin Hanyu para mandarín, Jyutping para cantonés, 118 idiomas, modo Boardroom de 3 voces (Pro Plus). Sin conexión en China — sin VPN.",
    "og_title": "Tova Translate — Mandarín, cantonés y 118 idiomas, sin conexión en China",
    "og_desc": "Escanea menús y carteles. Habla con cualquiera. Pinyin Hanyu real para mandarín, Jyutping real para cantonés, modo Boardroom de 3 voces. Funciona sin conexión en China — sin VPN.",
    "tw_title": "Tova — Mandarín, cantonés y 118 idiomas, sin conexión en China",
    "tw_desc": "Traductor de cámara + voz + texto. Pinyin para mandarín, Jyutping para cantonés, modo Boardroom de 3 voces. Funciona en China — sin VPN.",
    "eyebrow": "Hecho para viajeros · Asia · MENA · Europa",
    "h1_a": "Lee cualquier letrero. Habla con cualquiera.",
    "h1_b": "Incluso en China — sin VPN.",
    "store_dl_on": "Descárgalo en",
    "store_get_on": "Disponible en",
    "reassure_free": "Descarga gratis",
    "reassure_nosignup": "Sin registro",
    "reassure_china": "Funciona en China — sin VPN",
    "usecases_label": "Úsalo para",
    "uc_food": "Pedir comida",
    "uc_taxi": "Tomar un taxi",
    "uc_contracts": "Leer contratos",
    "uc_friends": "Hacer amigos",
    "uc_hotels": "Hacer check-in en hoteles",
    "uc_signs": "Leer letreros de museo",
    "shot1_strong": "OCR de cámara en vivo",
    "shot1_body": "Texto detectado y pinyin carácter por carácter en un único panel oscuro en la parte inferior de la cámara — acciones de leer / mostrar / guardar / copiar, y una insignia STABLE READ en la línea más estable.",
    "shot2_strong": "Tres voces, una conversación",
    "shot2_body": "El modo Boardroom de Pro Plus escucha los tres idiomas y traduce entre ellos — perfecto para reuniones internacionales.",
    "shot3_strong": "Traducción de voz bidireccional",
    "shot3_body": "Habla con naturalidad — verás el pinyin y la traducción en segundos, y al pulsar Listen escucharás la traducción en voz alta.",
    "dial_eyebrow": "¿Mandarín o cantonés?",
    "dial_h2": "Tova hace ambos — con la romanización correcta para cada uno.",
    "dial_p1_a": "Otras apps tratan el chino como un solo idioma y ponen pinyin sobre cada carácter.",
    "dial_p1_b": "Tova no. Elige 简体中文 y obtendrás verdadero",
    "dial_p1_c": "encima de cada carácter. Elige 廣東話 y obtendrás verdadero",
    "dial_p1_d": "la romanización que los cantoneses de Hong Kong realmente usan.",
    "dial_p2": "Misma pregunta en inglés, dos dialectos, dos lecturas correctas — viene incluido, sin ajustes que tocar.",
    "feat_eyebrow": "Qué incluye",
    "feat_h2": "Un traductor de viajes que no se rinde en la frontera.",
    "feat_lead": "Un motor de OCR pensado para letreros, una canalización de traducción que prioriza el modo sin conexión, y un modo conversación que respeta cómo la gente habla de verdad.",
    "feat1_title": "OCR de cámara en vivo — 11 escrituras",
    "feat1_body": "Apunta. Ve. Lee. CJK, tailandés, árabe, hebreo, devanagari, tibetano y más, con pinyin, romaji y hangul mostrados sobre cada glifo en tiempo real.",
    "feat2_title": "Traducción de voz bidireccional",
    "feat2_body": "Reconocimiento de voz en el dispositivo, reproducción natural y un modo Boardroom de 3 vías (Pro Plus) para reuniones entre tres idiomas.",
    "feat3_title": "Funciona en China — sin VPN",
    "feat3_body": "Cuando el servidor no es accesible, la traducción neuronal en el dispositivo se activa sola. Apple Translation en iOS, ML Kit en Android. Sin configurar nada.",
    "feat4_title": "29 paquetes de frases sin conexión",
    "feat4_body": "Frases de viaje seleccionadas más el diccionario chino CC-CEDICT completo. Descarga una vez, úsalo siempre — encontrar el baño sin cobertura.",
    "cta_h2_a": "Carga menos. Llega más lejos.",
    "cta_h2_b": "Habla con cualquiera.",
    "cta_lead": "Descarga gratis. Sin cuentas, sin registros. Lleva Tova en tu próximo viaje y no vuelvas a perderte en la traducción.",
    "cta_reassure_free": "Descarga gratis",
    "lang_switcher_label": "Leer esta página en",
    "view_english": "Read in English",
}

T["fr"] = {
    "title": "Tova Translate — Traducteur caméra et voix qui fonctionne hors ligne en Chine (sans VPN)",
    "meta_desc": "Traducteur caméra + voix pour voyager en Chine et en Asie. Pinyin Hanyu pour le mandarin, Jyutping pour le cantonais, 118 langues, mode Boardroom 3 voix Pro Plus. Hors ligne en Chine — sans VPN.",
    "og_title": "Tova Translate — Mandarin, cantonais et 118 langues, hors ligne en Chine",
    "og_desc": "Scannez les menus et panneaux. Parlez à tout le monde. Vrai pinyin Hanyu pour le mandarin, vrai Jyutping pour le cantonais, mode Boardroom 3 voix Pro Plus. Hors ligne en Chine — sans VPN.",
    "tw_title": "Tova — Mandarin, cantonais et 118 langues, hors ligne en Chine",
    "tw_desc": "Traducteur caméra + voix + texte. Pinyin pour le mandarin, Jyutping pour le cantonais, mode Boardroom 3 voix Pro Plus. Fonctionne en Chine — sans VPN.",
    "eyebrow": "Conçu pour les voyageurs · Asie · MENA · Europe",
    "h1_a": "Lisez n'importe quel panneau. Parlez à n'importe qui.",
    "h1_b": "Même en Chine — sans VPN.",
    "store_dl_on": "Télécharger sur",
    "store_get_on": "Disponible sur",
    "reassure_free": "Téléchargement gratuit",
    "reassure_nosignup": "Sans inscription",
    "reassure_china": "Fonctionne en Chine — sans VPN",
    "usecases_label": "Utilisez-le pour",
    "uc_food": "Commander à manger",
    "uc_taxi": "Héler un taxi",
    "uc_contracts": "Lire des contrats",
    "uc_friends": "Vous faire des amis",
    "uc_hotels": "Vous enregistrer à l'hôtel",
    "uc_signs": "Lire les panneaux de musée",
    "shot1_strong": "OCR caméra en direct",
    "shot1_body": "Texte détecté et pinyin caractère par caractère affichés dans un seul panneau sombre en bas de l'écran caméra — actions parler / afficher / enregistrer / copier, et un badge STABLE READ sur la ligne la plus fiable.",
    "shot2_strong": "Trois interlocuteurs, une conversation",
    "shot2_body": "Le mode Boardroom de Pro Plus écoute les trois langues et traduit entre elles — parfait pour les réunions internationales.",
    "shot3_strong": "Traduction vocale bidirectionnelle",
    "shot3_body": "Parlez naturellement — voyez le pinyin et la traduction en quelques secondes, puis touchez Listen pour entendre la traduction.",
    "dial_eyebrow": "Mandarin ou cantonais ?",
    "dial_h2": "Tova fait les deux — avec la bonne romanisation pour chacun.",
    "dial_p1_a": "Les autres applis traitent le chinois comme une seule langue et collent du pinyin sur chaque caractère.",
    "dial_p1_b": "Tova non. Choisissez 简体中文 et vous obtenez du vrai",
    "dial_p1_c": "au-dessus de chaque caractère. Choisissez 廣東話 et vous obtenez du vrai",
    "dial_p1_d": "la romanisation que les Cantonais de Hong Kong utilisent réellement.",
    "dial_p2": "Même question en anglais, deux dialectes, deux lectures correctes — intégré, aucun réglage à toucher.",
    "feat_eyebrow": "Ce qu'il y a dedans",
    "feat_h2": "Un traducteur de voyage qui ne s'arrête pas à la frontière.",
    "feat_lead": "Un moteur OCR pensé d'abord pour les panneaux, un pipeline de traduction qui privilégie le hors ligne, et un mode conversation qui respecte la façon dont les gens parlent vraiment.",
    "feat1_title": "OCR caméra en direct — 11 écritures",
    "feat1_body": "Visez. Voyez. Lisez. CJK, thaï, arabe, hébreu, devanagari, tibétain et plus, avec pinyin, romaji et hangeul affichés au-dessus de chaque glyphe en temps réel.",
    "feat2_title": "Traduction vocale bidirectionnelle",
    "feat2_body": "Reconnaissance vocale sur l'appareil, lecture vocale naturelle, et un mode Boardroom 3 voix Pro Plus pour les réunions entre trois langues.",
    "feat3_title": "Fonctionne en Chine — sans VPN",
    "feat3_body": "Quand le serveur est inaccessible, la traduction neuronale sur l'appareil prend le relais automatiquement. Apple Translation sur iOS, ML Kit sur Android. Aucun réglage.",
    "feat4_title": "29 packs de phrases hors ligne",
    "feat4_body": "Phrases de voyage soignées plus le dictionnaire chinois CC-CEDICT complet. Téléchargez une fois, utilisez à vie — aucune couverture nécessaire pour trouver les toilettes.",
    "cta_h2_a": "Voyagez léger. Allez plus loin.",
    "cta_h2_b": "Parlez à n'importe qui.",
    "cta_lead": "Téléchargement gratuit. Pas de compte, pas d'inscription. Emmenez Tova lors de votre prochain voyage et ne soyez plus jamais perdu en traduction.",
    "cta_reassure_free": "Téléchargement gratuit",
    "lang_switcher_label": "Lire cette page en",
    "view_english": "Read in English",
}

T["de"] = {
    "title": "Tova Translate — Kamera- und Sprachübersetzer, der in China offline funktioniert (ohne VPN)",
    "meta_desc": "Kamera- + Sprachübersetzer fürs Reisen in China und Asien. Hanyu-Pinyin für Mandarin, Jyutping für Kantonesisch, 118 Sprachen, Pro Plus 3-Wege-Boardroom-Modus. Offline in China — kein VPN.",
    "og_title": "Tova Translate — Mandarin, Kantonesisch und 118 Sprachen, offline in China",
    "og_desc": "Scannen Sie Menüs und Schilder. Sprechen Sie mit allen. Echtes Hanyu-Pinyin für Mandarin, echtes Jyutping für Kantonesisch, Pro Plus 3-Wege-Boardroom-Modus. Offline in China — kein VPN.",
    "tw_title": "Tova — Mandarin, Kantonesisch und 118 Sprachen, offline in China",
    "tw_desc": "Kamera- + Sprach- + Textübersetzer. Pinyin für Mandarin, Jyutping für Kantonesisch, Pro Plus 3-Wege-Boardroom-Modus. Funktioniert in China — kein VPN.",
    "eyebrow": "Für Reisende gemacht · Asien · MENA · Europa",
    "h1_a": "Lies jedes Schild. Sprich mit jedem.",
    "h1_b": "Auch in China — ohne VPN.",
    "store_dl_on": "Lade es im",
    "store_get_on": "Hol es bei",
    "reassure_free": "Kostenlos herunterladen",
    "reassure_nosignup": "Ohne Anmeldung",
    "reassure_china": "Funktioniert in China — ohne VPN",
    "usecases_label": "Verwende es, um",
    "uc_food": "Essen zu bestellen",
    "uc_taxi": "Ein Taxi zu rufen",
    "uc_contracts": "Verträge zu lesen",
    "uc_friends": "Freunde zu finden",
    "uc_hotels": "Im Hotel einzuchecken",
    "uc_signs": "Museumsschilder zu lesen",
    "shot1_strong": "Live-Kamera-OCR",
    "shot1_body": "Erkannter Text und zeichenweise Pinyin in einem einzigen dunklen Panel unten am Kamera-Bildschirm — Sprechen / Anzeigen / Speichern / Kopieren-Aktionen und ein STABLE-READ-Hinweis auf der zuverlässig erkannten Zeile.",
    "shot2_strong": "Drei Sprecher, ein Gespräch",
    "shot2_body": "Der Pro Plus Boardroom-Modus hört alle drei Sprachen und übersetzt zwischen ihnen — perfekt für grenzüberschreitende Meetings.",
    "shot3_strong": "Zweiwege-Sprachübersetzung",
    "shot3_body": "Sprich natürlich — du siehst die Pinyin-Aussprache und Übersetzung in Sekunden, tippe Listen, um die Übersetzung gesprochen zu hören.",
    "dial_eyebrow": "Mandarin oder Kantonesisch?",
    "dial_h2": "Tova kann beides — mit der richtigen Romanisierung für jede Sprache.",
    "dial_p1_a": "Andere Apps behandeln Chinesisch als eine Sprache und klatschen Pinyin auf jedes Zeichen.",
    "dial_p1_b": "Tova nicht. Wähle 简体中文 und du bekommst echtes",
    "dial_p1_c": "über jedem Zeichen. Wähle 廣東話 und du bekommst echtes",
    "dial_p1_d": "die Romanisierung, die Hongkonger Kantonesisch-Sprecher tatsächlich verwenden.",
    "dial_p2": "Gleiche englische Frage, zwei Dialekte, zwei korrekte Aussprachen — eingebaut, keine Einstellungen nötig.",
    "feat_eyebrow": "Was drin ist",
    "feat_h2": "Ein Reise-Übersetzer, der an der Grenze nicht aufgibt.",
    "feat_lead": "Eine OCR-Engine, die zuerst für Schilder entworfen wurde, eine offline-zuerst-Übersetzungspipeline und ein Konversationsmodus, der respektiert, wie Menschen wirklich sprechen.",
    "feat1_title": "Live-Kamera-OCR — 11 Schriften",
    "feat1_body": "Zielen. Sehen. Lesen. CJK, Thai, Arabisch, Hebräisch, Devanagari, Tibetisch und mehr, mit Pinyin, Romaji und Hangul in Echtzeit über jedem Zeichen angezeigt.",
    "feat2_title": "Zweiwege-Sprachübersetzung",
    "feat2_body": "Spracherkennung auf dem Gerät, natürliche Sprachwiedergabe und ein Pro Plus 3-Wege-Boardroom-Modus für Meetings zwischen drei Sprachen.",
    "feat3_title": "Funktioniert in China — ohne VPN",
    "feat3_body": "Wenn das Backend nicht erreichbar ist, springt die neuronale Übersetzung auf dem Gerät automatisch ein. Apple Translation auf iOS, ML Kit auf Android. Keine Einrichtung, keine Umwege.",
    "feat4_title": "29 Offline-Phrasenpakete",
    "feat4_body": "Sorgfältig kuratierte Reisephrasen plus das vollständige CC-CEDICT-Chinesisch-Wörterbuch. Einmal herunterladen, immer nutzen — kein Mobilfunk nötig, um die Toilette zu finden.",
    "cta_h2_a": "Reise leichter. Komm weiter.",
    "cta_h2_b": "Sprich mit jedem.",
    "cta_lead": "Kostenlos herunterladen. Keine Konten, keine Anmeldung. Nimm Tova auf deine nächste Reise mit und verirre dich nie wieder in der Übersetzung.",
    "cta_reassure_free": "Kostenlos herunterladen",
    "lang_switcher_label": "Diese Seite lesen auf",
    "view_english": "Read in English",
}

T["pt"] = {
    "title": "Tova Translate — Tradutor de câmera e voz que funciona offline na China (sem VPN)",
    "meta_desc": "Tradutor de câmera + voz para viajar pela China e Ásia. Pinyin Hanyu para mandarim, Jyutping para cantonês, 118 idiomas, modo Boardroom de 3 vozes (Pro Plus). Offline na China — sem VPN.",
    "og_title": "Tova Translate — Mandarim, cantonês e 118 idiomas, offline na China",
    "og_desc": "Escaneie cardápios e placas. Fale com qualquer um. Pinyin Hanyu real para mandarim, Jyutping real para cantonês, modo Boardroom de 3 vozes Pro Plus. Funciona offline na China — sem VPN.",
    "tw_title": "Tova — Mandarim, cantonês e 118 idiomas, offline na China",
    "tw_desc": "Tradutor de câmera + voz + texto. Pinyin para mandarim, Jyutping para cantonês, modo Boardroom de 3 vozes Pro Plus. Funciona na China — sem VPN.",
    "eyebrow": "Feito para viajantes · Ásia · MENA · Europa",
    "h1_a": "Leia qualquer placa. Fale com qualquer um.",
    "h1_b": "Mesmo na China — sem VPN.",
    "store_dl_on": "Baixe na",
    "store_get_on": "Disponível no",
    "reassure_free": "Download grátis",
    "reassure_nosignup": "Sem cadastro",
    "reassure_china": "Funciona na China — sem VPN",
    "usecases_label": "Use para",
    "uc_food": "Pedir comida",
    "uc_taxi": "Chamar um táxi",
    "uc_contracts": "Ler contratos",
    "uc_friends": "Fazer amigos",
    "uc_hotels": "Fazer check-in no hotel",
    "uc_signs": "Ler placas de museu",
    "shot1_strong": "OCR de câmera ao vivo",
    "shot1_body": "Texto detectado e pinyin caractere por caractere em um único painel escuro na parte inferior da tela da câmera — ações de falar / mostrar / salvar / copiar, e um selo STABLE READ na linha de leitura mais estável.",
    "shot2_strong": "Três falantes, uma conversa",
    "shot2_body": "O modo Boardroom do Pro Plus escuta os três idiomas e traduz entre eles — perfeito para reuniões internacionais.",
    "shot3_strong": "Tradução de voz bidirecional",
    "shot3_body": "Fale com naturalidade — veja o pinyin e a tradução em segundos, depois toque em Listen para ouvir a tradução em voz alta.",
    "dial_eyebrow": "Mandarim ou cantonês?",
    "dial_h2": "Tova faz os dois — com a romanização certa para cada um.",
    "dial_p1_a": "Outros apps tratam o chinês como um único idioma e colocam pinyin em cada caractere.",
    "dial_p1_b": "Tova não. Escolha 简体中文 e você recebe o verdadeiro",
    "dial_p1_c": "acima de cada caractere. Escolha 廣東話 e você recebe o verdadeiro",
    "dial_p1_d": "a romanização que os cantoneses de Hong Kong realmente usam.",
    "dial_p2": "Mesma pergunta em inglês, dois dialetos, duas leituras corretas — embutido, sem ajustes para mexer.",
    "feat_eyebrow": "O que há dentro",
    "feat_h2": "Um tradutor de viagem que não desiste na fronteira.",
    "feat_lead": "Um motor de OCR pensado para placas, um pipeline de tradução que prioriza o offline, e um modo conversação que respeita como as pessoas realmente falam.",
    "feat1_title": "OCR de câmera ao vivo — 11 escritas",
    "feat1_body": "Aponte. Veja. Leia. CJK, tailandês, árabe, hebraico, devanagari, tibetano e mais, com pinyin, romaji e hangul mostrados sobre cada glifo em tempo real.",
    "feat2_title": "Tradução de voz bidirecional",
    "feat2_body": "Reconhecimento de voz no dispositivo, reprodução natural e modo Boardroom de 3 vozes (Pro Plus) para reuniões entre três idiomas.",
    "feat3_title": "Funciona na China — sem VPN",
    "feat3_body": "Quando o servidor não está acessível, a tradução neural no dispositivo entra automaticamente. Apple Translation no iOS, ML Kit no Android. Sem configurar nada.",
    "feat4_title": "29 pacotes de frases offline",
    "feat4_body": "Frases de viagem curadas mais o dicionário chinês CC-CEDICT completo. Baixe uma vez, use sempre — sem precisar de sinal para achar o banheiro.",
    "cta_h2_a": "Leve menos. Vá mais longe.",
    "cta_h2_b": "Fale com qualquer um.",
    "cta_lead": "Download grátis. Sem contas, sem cadastros. Leve Tova na sua próxima viagem e nunca mais se perca na tradução.",
    "cta_reassure_free": "Download grátis",
    "lang_switcher_label": "Leia esta página em",
    "view_english": "Read in English",
}

T["it"] = {
    "title": "Tova Translate — Traduttore fotocamera e voce che funziona offline in Cina (senza VPN)",
    "meta_desc": "Traduttore fotocamera + voce per viaggiare in Cina e Asia. Pinyin Hanyu per il mandarino, Jyutping per il cantonese, 118 lingue, modalità Boardroom a 3 voci Pro Plus. Offline in Cina — senza VPN.",
    "og_title": "Tova Translate — Mandarino, cantonese e 118 lingue, offline in Cina",
    "og_desc": "Scansiona menu e cartelli. Parla con chiunque. Vero pinyin Hanyu per il mandarino, vero Jyutping per il cantonese, modalità Boardroom a 3 voci Pro Plus. Offline in Cina — senza VPN.",
    "tw_title": "Tova — Mandarino, cantonese e 118 lingue, offline in Cina",
    "tw_desc": "Traduttore fotocamera + voce + testo. Pinyin per il mandarino, Jyutping per il cantonese, modalità Boardroom a 3 voci Pro Plus. Funziona in Cina — senza VPN.",
    "eyebrow": "Fatto per i viaggiatori · Asia · MENA · Europa",
    "h1_a": "Leggi qualsiasi cartello. Parla con chiunque.",
    "h1_b": "Anche in Cina — senza VPN.",
    "store_dl_on": "Scarica su",
    "store_get_on": "Disponibile su",
    "reassure_free": "Download gratuito",
    "reassure_nosignup": "Senza registrazione",
    "reassure_china": "Funziona in Cina — senza VPN",
    "usecases_label": "Usalo per",
    "uc_food": "Ordinare cibo",
    "uc_taxi": "Chiamare un taxi",
    "uc_contracts": "Leggere contratti",
    "uc_friends": "Fare amicizia",
    "uc_hotels": "Fare il check-in in hotel",
    "uc_signs": "Leggere cartelli museali",
    "shot1_strong": "OCR fotocamera in tempo reale",
    "shot1_body": "Testo rilevato e pinyin carattere per carattere in un singolo pannello scuro nella parte inferiore dello schermo della fotocamera — azioni parla / mostra / salva / copia e una targhetta STABLE READ sulla riga più stabile.",
    "shot2_strong": "Tre interlocutori, una conversazione",
    "shot2_body": "La modalità Boardroom di Pro Plus ascolta tutte e tre le lingue e traduce tra di esse — perfetta per riunioni internazionali.",
    "shot3_strong": "Traduzione vocale bidirezionale",
    "shot3_body": "Parla naturalmente — vedi pinyin e traduzione in pochi secondi, poi tocca Listen per sentire la traduzione ad alta voce.",
    "dial_eyebrow": "Mandarino o cantonese?",
    "dial_h2": "Tova li fa entrambi — con la romanizzazione giusta per ognuno.",
    "dial_p1_a": "Le altre app trattano il cinese come una sola lingua e mettono pinyin su ogni carattere.",
    "dial_p1_b": "Tova no. Scegli 简体中文 e ottieni vero",
    "dial_p1_c": "sopra ogni carattere. Scegli 廣東話 e ottieni vero",
    "dial_p1_d": "la romanizzazione che i cantonesi di Hong Kong usano davvero.",
    "dial_p2": "Stessa domanda in inglese, due dialetti, due letture corrette — integrato, niente da configurare.",
    "feat_eyebrow": "Cosa c'è dentro",
    "feat_h2": "Un traduttore da viaggio che non si ferma alla frontiera.",
    "feat_lead": "Un motore OCR pensato prima di tutto per i cartelli, una pipeline di traduzione orientata all'offline e una modalità conversazione che rispetta come parlano davvero le persone.",
    "feat1_title": "OCR fotocamera in tempo reale — 11 scritture",
    "feat1_body": "Punta. Vedi. Leggi. CJK, thailandese, arabo, ebraico, devanagari, tibetano e altro, con pinyin, romaji e hangul mostrati sopra ogni glifo in tempo reale.",
    "feat2_title": "Traduzione vocale bidirezionale",
    "feat2_body": "Riconoscimento vocale sul dispositivo, riproduzione vocale naturale e una modalità Boardroom a 3 voci Pro Plus per riunioni tra tre lingue.",
    "feat3_title": "Funziona in Cina — senza VPN",
    "feat3_body": "Quando il backend non è raggiungibile, la traduzione neurale sul dispositivo si attiva automaticamente. Apple Translation su iOS, ML Kit su Android. Nessuna configurazione.",
    "feat4_title": "29 pacchetti di frasi offline",
    "feat4_body": "Frasi di viaggio selezionate più l'intero dizionario cinese CC-CEDICT. Scarica una volta, usalo per sempre — niente segnale per trovare il bagno.",
    "cta_h2_a": "Bagaglio leggero. Più lontano.",
    "cta_h2_b": "Parla con chiunque.",
    "cta_lead": "Download gratuito. Niente account, niente registrazione. Porta Tova nel tuo prossimo viaggio e non perderti più nella traduzione.",
    "cta_reassure_free": "Download gratuito",
    "lang_switcher_label": "Leggi questa pagina in",
    "view_english": "Read in English",
}

T["th"] = {
    "title": "Tova Translate — แอปแปลภาษาด้วยกล้องและเสียง ใช้ออฟไลน์ในจีนได้ (ไม่ต้องใช้ VPN)",
    "meta_desc": "แอปแปลภาษาด้วยกล้อง + เสียง สำหรับเดินทางในจีนและเอเชีย รองรับพินอินจีนกลาง จุดผิงสำหรับกวางตุ้ง 118 ภาษา โหมด Boardroom 3 ทาง (Pro Plus) ใช้ออฟไลน์ในจีน — ไม่ต้องใช้ VPN",
    "og_title": "Tova Translate — จีนกลาง กวางตุ้ง และอีก 118 ภาษา ใช้ออฟไลน์ในจีน",
    "og_desc": "สแกนเมนูและป้าย คุยกับใครก็ได้ พินอินจีนกลางของจริง จุดผิงกวางตุ้งของจริง โหมด Boardroom 3 ทาง Pro Plus ใช้ออฟไลน์ในจีนได้ — ไม่ต้องใช้ VPN",
    "tw_title": "Tova — จีนกลาง กวางตุ้ง และอีก 118 ภาษา ใช้ออฟไลน์ในจีน",
    "tw_desc": "แอปแปลภาษากล้อง + เสียง + ข้อความ พินอินสำหรับจีนกลาง จุดผิงสำหรับกวางตุ้ง โหมด Boardroom 3 ทาง Pro Plus ใช้ในจีนได้ — ไม่ต้องใช้ VPN",
    "eyebrow": "ออกแบบเพื่อผู้เดินทาง · เอเชีย · ตะวันออกกลาง · ยุโรป",
    "h1_a": "อ่านป้ายได้ทุกป้าย คุยกับใครก็ได้",
    "h1_b": "แม้แต่ในจีน — ไม่ต้องใช้ VPN",
    "store_dl_on": "ดาวน์โหลดบน",
    "store_get_on": "รับได้ที่",
    "reassure_free": "ดาวน์โหลดฟรี",
    "reassure_nosignup": "ไม่ต้องสมัคร",
    "reassure_china": "ใช้ในจีนได้ — ไม่ต้องใช้ VPN",
    "usecases_label": "ใช้สำหรับ",
    "uc_food": "สั่งอาหาร",
    "uc_taxi": "เรียกแท็กซี่",
    "uc_contracts": "อ่านสัญญา",
    "uc_friends": "หาเพื่อน",
    "uc_hotels": "เช็คอินโรงแรม",
    "uc_signs": "อ่านป้ายในพิพิธภัณฑ์",
    "shot1_strong": "OCR กล้องสด",
    "shot1_body": "ข้อความที่ตรวจพบและพินอินรายตัวอักษรในแผงสีเข้มเดียวที่ด้านล่างของหน้าจอกล้อง — มีปุ่ม พูด / แสดง / บันทึก / คัดลอก และตรา STABLE READ บนบรรทัดที่อ่านได้แม่นยำ",
    "shot2_strong": "สามคนคุย หนึ่งบทสนทนา",
    "shot2_body": "โหมด Boardroom ของ Pro Plus ฟังภาษาทั้งสามและแปลระหว่างกัน — เหมาะกับการประชุมข้ามชาติ",
    "shot3_strong": "แปลเสียงสองทาง",
    "shot3_body": "พูดได้เป็นธรรมชาติ — เห็นพินอินและคำแปลในไม่กี่วินาที จากนั้นแตะ Listen เพื่อฟังคำแปล",
    "dial_eyebrow": "จีนกลางหรือกวางตุ้ง?",
    "dial_h2": "Tova ทำได้ทั้งสองภาษา — พร้อมระบบเขียนแบบโรมันที่ถูกต้องสำหรับแต่ละภาษา",
    "dial_p1_a": "แอปอื่นถือว่าภาษาจีนเป็นภาษาเดียวและใส่พินอินบนทุกตัวอักษร",
    "dial_p1_b": "Tova ไม่ใช่อย่างนั้น เลือก 简体中文 แล้วคุณจะได้",
    "dial_p1_c": "ของจริงบนทุกตัวอักษร เลือก 廣東話 แล้วคุณจะได้",
    "dial_p1_d": "ของจริง — ระบบเขียนแบบโรมันที่ผู้พูดกวางตุ้งฮ่องกงใช้กันจริง",
    "dial_p2": "คำถามภาษาอังกฤษเดียวกัน สองภาษาถิ่น สองคำอ่านที่ถูกต้อง — มีในตัว ไม่ต้องตั้งค่า",
    "feat_eyebrow": "มีอะไรในแอป",
    "feat_h2": "แอปแปลสำหรับนักเดินทาง ที่ไม่หยุดทำงานที่ชายแดน",
    "feat_lead": "เครื่อง OCR ที่ออกแบบสำหรับป้ายเป็นหลัก ไปป์ไลน์แปลที่เน้นออฟไลน์ก่อน และโหมดสนทนาที่เคารพวิธีที่คนพูดจริง",
    "feat1_title": "OCR กล้องสด — 11 ระบบเขียน",
    "feat1_body": "เล็ง มอง อ่าน CJK ไทย อาหรับ ฮีบรู เทวนาครี ทิเบต และอื่นๆ พร้อมพินอิน โรมาจิ และฮันกึลแสดงเหนือทุกตัวอักษรแบบเรียลไทม์",
    "feat2_title": "แปลเสียงสองทาง",
    "feat2_body": "การรู้จำเสียงในเครื่อง เสียงเล่นกลับเป็นธรรมชาติ และโหมด Boardroom 3 ทาง Pro Plus สำหรับการประชุมระหว่างสามภาษา",
    "feat3_title": "ใช้ในจีนได้ — ไม่ต้องใช้ VPN",
    "feat3_body": "เมื่อเซิร์ฟเวอร์ไม่สามารถเข้าถึงได้ การแปลด้วย neural บนเครื่องจะทำงานอัตโนมัติ Apple Translation บน iOS, ML Kit บน Android ไม่ต้องตั้งค่า",
    "feat4_title": "29 ชุดวลีออฟไลน์",
    "feat4_body": "วลีท่องเที่ยวที่คัดสรรพร้อมพจนานุกรมจีน CC-CEDICT ครบชุด ดาวน์โหลดครั้งเดียว ใช้ตลอดไป — ไม่ต้องมีสัญญาณก็หาห้องน้ำได้",
    "cta_h2_a": "เดินทางเบาขึ้น ไปได้ไกลขึ้น",
    "cta_h2_b": "คุยกับใครก็ได้",
    "cta_lead": "ดาวน์โหลดฟรี ไม่ต้องมีบัญชี ไม่ต้องสมัคร พา Tova ไปทริปถัดไป แล้วจะไม่หลงทางในการแปลอีกเลย",
    "cta_reassure_free": "ดาวน์โหลดฟรี",
    "lang_switcher_label": "อ่านหน้านี้เป็นภาษาอื่น",
    "view_english": "Read in English",
}

T["vi"] = {
    "title": "Tova Translate — Ứng dụng dịch bằng camera và giọng nói, hoạt động ngoại tuyến tại Trung Quốc (không cần VPN)",
    "meta_desc": "Ứng dụng dịch bằng camera + giọng nói cho du lịch Trung Quốc và châu Á. Hán ngữ Bính âm cho tiếng Quan Thoại, Việt bính cho tiếng Quảng, 118 ngôn ngữ, chế độ Boardroom 3 chiều Pro Plus. Ngoại tuyến tại Trung Quốc — không cần VPN.",
    "og_title": "Tova Translate — Quan Thoại, Quảng Đông và 118 ngôn ngữ, ngoại tuyến tại Trung Quốc",
    "og_desc": "Quét thực đơn và biển báo. Trò chuyện với bất kỳ ai. Bính âm thật cho Quan Thoại, Việt bính thật cho Quảng Đông, chế độ Boardroom 3 chiều Pro Plus. Ngoại tuyến tại Trung Quốc — không cần VPN.",
    "tw_title": "Tova — Quan Thoại, Quảng Đông và 118 ngôn ngữ, ngoại tuyến tại Trung Quốc",
    "tw_desc": "Ứng dụng dịch bằng camera + giọng nói + văn bản. Bính âm cho Quan Thoại, Việt bính cho Quảng Đông, chế độ Boardroom 3 chiều Pro Plus. Hoạt động ở Trung Quốc — không cần VPN.",
    "eyebrow": "Dành cho người du lịch · Châu Á · Trung Đông · Châu Âu",
    "h1_a": "Đọc mọi biển báo. Nói chuyện với bất kỳ ai.",
    "h1_b": "Ngay cả ở Trung Quốc — không cần VPN.",
    "store_dl_on": "Tải xuống trên",
    "store_get_on": "Có trên",
    "reassure_free": "Tải xuống miễn phí",
    "reassure_nosignup": "Không cần đăng ký",
    "reassure_china": "Hoạt động ở Trung Quốc — không cần VPN",
    "usecases_label": "Dùng để",
    "uc_food": "Gọi món ăn",
    "uc_taxi": "Vẫy taxi",
    "uc_contracts": "Đọc hợp đồng",
    "uc_friends": "Kết bạn",
    "uc_hotels": "Nhận phòng khách sạn",
    "uc_signs": "Đọc bảng giới thiệu bảo tàng",
    "shot1_strong": "OCR camera trực tiếp",
    "shot1_body": "Văn bản nhận diện được và bính âm theo từng ký tự trong một bảng tối duy nhất ở dưới màn hình camera — các thao tác đọc / hiển thị / lưu / sao chép và huy hiệu STABLE READ trên dòng đọc ổn định nhất.",
    "shot2_strong": "Ba người nói, một cuộc trò chuyện",
    "shot2_body": "Chế độ Boardroom của Pro Plus nghe cả ba ngôn ngữ và dịch giữa chúng — hoàn hảo cho các cuộc họp xuyên biên giới.",
    "shot3_strong": "Dịch giọng nói hai chiều",
    "shot3_body": "Hãy nói tự nhiên — bạn sẽ thấy bính âm và bản dịch trong vài giây, sau đó nhấn Listen để nghe bản dịch.",
    "dial_eyebrow": "Quan Thoại hay Quảng Đông?",
    "dial_h2": "Tova làm cả hai — với cách phiên âm la-tinh đúng cho từng ngôn ngữ.",
    "dial_p1_a": "Các ứng dụng khác coi tiếng Trung là một ngôn ngữ duy nhất và đặt bính âm trên mọi ký tự.",
    "dial_p1_b": "Tova thì không. Chọn 简体中文 và bạn sẽ nhận được",
    "dial_p1_c": "thật trên mỗi ký tự. Chọn 廣東話 và bạn sẽ nhận được",
    "dial_p1_d": "thật — cách phiên âm la-tinh mà người Quảng Đông Hong Kong thực sự dùng.",
    "dial_p2": "Cùng một câu hỏi tiếng Anh, hai phương ngữ, hai cách đọc đúng — tích hợp sẵn, không cần điều chỉnh.",
    "feat_eyebrow": "Có gì trong ứng dụng",
    "feat_h2": "Ứng dụng dịch du lịch không bỏ cuộc ở biên giới.",
    "feat_lead": "Một engine OCR ưu tiên biển báo, một pipeline dịch ưu tiên ngoại tuyến, và một chế độ hội thoại tôn trọng cách mọi người thực sự nói chuyện.",
    "feat1_title": "OCR camera trực tiếp — 11 hệ chữ viết",
    "feat1_body": "Chỉ. Nhìn. Đọc. CJK, tiếng Thái, Ả Rập, Do Thái, Devanagari, Tây Tạng và nhiều hơn nữa, với bính âm, romaji, và hangeul hiển thị trên từng ký tự theo thời gian thực.",
    "feat2_title": "Dịch giọng nói hai chiều",
    "feat2_body": "Nhận diện giọng nói trên thiết bị, phát lại giọng nói tự nhiên, và chế độ Boardroom 3 chiều Pro Plus cho các cuộc họp giữa ba ngôn ngữ.",
    "feat3_title": "Hoạt động ở Trung Quốc — không cần VPN",
    "feat3_body": "Khi máy chủ không thể truy cập, bản dịch neural trên thiết bị tự động hoạt động. Apple Translation trên iOS, ML Kit trên Android. Không cần cài đặt, không cần đi đường vòng.",
    "feat4_title": "29 gói cụm từ ngoại tuyến",
    "feat4_body": "Các cụm từ du lịch được tuyển chọn cùng từ điển Trung Quốc CC-CEDICT đầy đủ. Tải một lần, dùng mãi mãi — không cần sóng để tìm phòng vệ sinh.",
    "cta_h2_a": "Hành lý nhẹ hơn. Đi xa hơn.",
    "cta_h2_b": "Nói chuyện với bất kỳ ai.",
    "cta_lead": "Tải xuống miễn phí. Không tài khoản, không đăng ký. Mang Tova trong chuyến đi tiếp theo và đừng bao giờ lạc lối trong việc dịch nữa.",
    "cta_reassure_free": "Tải xuống miễn phí",
    "lang_switcher_label": "Đọc trang này bằng",
    "view_english": "Read in English",
}

T["id"] = {
    "title": "Tova Translate — Penerjemah kamera dan suara yang berfungsi offline di Tiongkok (tanpa VPN)",
    "meta_desc": "Penerjemah kamera + suara untuk bepergian di Tiongkok dan Asia. Hanyu Pinyin untuk Mandarin, Jyutping untuk Kanton, 118 bahasa, mode Boardroom 3 arah Pro Plus. Offline di Tiongkok — tanpa VPN.",
    "og_title": "Tova Translate — Mandarin, Kanton, dan 118 bahasa, offline di Tiongkok",
    "og_desc": "Pindai menu dan papan tanda. Bicara dengan siapa saja. Hanyu Pinyin asli untuk Mandarin, Jyutping asli untuk Kanton, mode Boardroom 3 arah Pro Plus. Berfungsi offline di Tiongkok — tanpa VPN.",
    "tw_title": "Tova — Mandarin, Kanton, dan 118 bahasa, offline di Tiongkok",
    "tw_desc": "Penerjemah kamera + suara + teks. Pinyin untuk Mandarin, Jyutping untuk Kanton, mode Boardroom 3 arah Pro Plus. Berfungsi di Tiongkok — tanpa VPN.",
    "eyebrow": "Dibuat untuk pelancong · Asia · MENA · Eropa",
    "h1_a": "Baca tanda apa pun. Bicara dengan siapa pun.",
    "h1_b": "Bahkan di Tiongkok — tanpa VPN.",
    "store_dl_on": "Unduh di",
    "store_get_on": "Tersedia di",
    "reassure_free": "Unduh gratis",
    "reassure_nosignup": "Tanpa pendaftaran",
    "reassure_china": "Berfungsi di Tiongkok — tanpa VPN",
    "usecases_label": "Gunakan untuk",
    "uc_food": "Memesan makanan",
    "uc_taxi": "Menyetop taksi",
    "uc_contracts": "Membaca kontrak",
    "uc_friends": "Berteman",
    "uc_hotels": "Check-in di hotel",
    "uc_signs": "Membaca papan museum",
    "shot1_strong": "OCR kamera langsung",
    "shot1_body": "Teks yang terdeteksi dan pinyin per karakter dalam satu panel gelap di bagian bawah layar kamera — tindakan baca / tampilkan / simpan / salin, dan lencana STABLE READ pada baris paling stabil.",
    "shot2_strong": "Tiga pembicara, satu percakapan",
    "shot2_body": "Mode Boardroom Pro Plus mendengar ketiga bahasa dan menerjemahkan di antara mereka — sempurna untuk rapat lintas negara.",
    "shot3_strong": "Terjemahan suara dua arah",
    "shot3_body": "Bicara dengan natural — lihat pinyin dan terjemahan dalam hitungan detik, lalu ketuk Listen untuk mendengar terjemahan.",
    "dial_eyebrow": "Mandarin atau Kanton?",
    "dial_h2": "Tova melakukan keduanya — dengan romanisasi yang tepat untuk masing-masing.",
    "dial_p1_a": "Aplikasi lain memperlakukan bahasa Tionghoa sebagai satu bahasa dan menempelkan pinyin pada setiap karakter.",
    "dial_p1_b": "Tova tidak. Pilih 简体中文 dan Anda mendapatkan",
    "dial_p1_c": "asli di atas setiap karakter. Pilih 廣東話 dan Anda mendapatkan",
    "dial_p1_d": "asli — romanisasi yang benar-benar digunakan penutur Kanton Hong Kong.",
    "dial_p2": "Pertanyaan bahasa Inggris yang sama, dua dialek, dua bacaan yang benar — bawaan, tanpa pengaturan untuk diubah.",
    "feat_eyebrow": "Apa yang ada di dalamnya",
    "feat_h2": "Penerjemah perjalanan yang tidak berhenti di perbatasan.",
    "feat_lead": "Mesin OCR yang dirancang untuk papan tanda, pipeline terjemahan yang mengutamakan offline, dan mode percakapan yang menghormati cara orang berbicara sungguhan.",
    "feat1_title": "OCR kamera langsung — 11 sistem tulisan",
    "feat1_body": "Arahkan. Lihat. Baca. CJK, Thai, Arab, Ibrani, Devanagari, Tibet, dan lainnya, dengan pinyin, romaji, dan hangul ditampilkan di atas setiap glif secara real-time.",
    "feat2_title": "Terjemahan suara dua arah",
    "feat2_body": "Pengenalan suara di perangkat, pemutaran suara natural, dan mode Boardroom 3 arah Pro Plus untuk rapat antara tiga bahasa.",
    "feat3_title": "Berfungsi di Tiongkok — tanpa VPN",
    "feat3_body": "Saat backend tidak dapat dijangkau, terjemahan neural di perangkat aktif secara otomatis. Apple Translation di iOS, ML Kit di Android. Tanpa pengaturan, tanpa berputar.",
    "feat4_title": "29 paket frasa offline",
    "feat4_body": "Frasa perjalanan yang dikurasi plus kamus Tionghoa CC-CEDICT lengkap. Unduh sekali, gunakan selamanya — tidak perlu sinyal untuk menemukan toilet.",
    "cta_h2_a": "Bawa lebih sedikit. Pergi lebih jauh.",
    "cta_h2_b": "Bicara dengan siapa pun.",
    "cta_lead": "Unduh gratis. Tanpa akun, tanpa pendaftaran. Bawa Tova di perjalanan berikutnya dan jangan pernah tersesat dalam terjemahan lagi.",
    "cta_reassure_free": "Unduh gratis",
    "lang_switcher_label": "Baca halaman ini dalam",
    "view_english": "Read in English",
}

T["tl"] = {
    "title": "Tova Translate — Camera at voice translator na gumagana offline sa Tsina (walang VPN)",
    "meta_desc": "Camera + voice translator para sa paglalakbay sa Tsina at Asia. Hanyu Pinyin para sa Mandarin, Jyutping para sa Cantonese, 118 wika, Pro Plus 3-way Boardroom mode. Offline sa Tsina — walang VPN.",
    "og_title": "Tova Translate — Mandarin, Cantonese, at 118 wika, offline sa Tsina",
    "og_desc": "I-scan ang menu at signage. Makipag-usap kahit kanino. Tunay na Hanyu Pinyin para sa Mandarin, tunay na Jyutping para sa Cantonese, Pro Plus 3-way Boardroom mode. Gumagana offline sa Tsina — walang VPN.",
    "tw_title": "Tova — Mandarin, Cantonese, at 118 wika, offline sa Tsina",
    "tw_desc": "Camera + voice + text translator. Pinyin para sa Mandarin, Jyutping para sa Cantonese, Pro Plus 3-way Boardroom mode. Gumagana sa Tsina — walang VPN.",
    "eyebrow": "Para sa mga manlalakbay · Asia · MENA · Europe",
    "h1_a": "Basahin ang kahit anong karatula. Makipag-usap kahit kanino.",
    "h1_b": "Kahit sa Tsina — walang VPN.",
    "store_dl_on": "I-download sa",
    "store_get_on": "Makukuha sa",
    "reassure_free": "Libre i-download",
    "reassure_nosignup": "Walang pag-sign up",
    "reassure_china": "Gumagana sa Tsina — walang VPN",
    "usecases_label": "Gamitin para sa",
    "uc_food": "Pag-order ng pagkain",
    "uc_taxi": "Pagtawag ng taxi",
    "uc_contracts": "Pagbabasa ng mga kontrata",
    "uc_friends": "Pakikipag-kaibigan",
    "uc_hotels": "Pag-check-in sa hotel",
    "uc_signs": "Pagbabasa ng museum signage",
    "shot1_strong": "Live camera OCR",
    "shot1_body": "Ang na-detect na teksto at per-character na pinyin ay nasa iisang madilim na panel sa ibaba ng camera screen — speak / show / save / copy actions, at STABLE READ badge sa pinaka-stable na linya.",
    "shot2_strong": "Tatlong nagsasalita, isang usapan",
    "shot2_body": "Naririnig ng Pro Plus Boardroom mode ang lahat ng tatlong wika at isinasalin sa pagitan nila — perpekto para sa cross-border meetings.",
    "shot3_strong": "Two-way voice translation",
    "shot3_body": "Magsalita nang natural — makikita ang pinyin at salin sa ilang segundo, pagkatapos i-tap ang Listen para marinig ang salin.",
    "dial_eyebrow": "Mandarin o Cantonese?",
    "dial_h2": "Pareho silang ginagawa ng Tova — gamit ang tamang romanization para sa bawat isa.",
    "dial_p1_a": "Ang ibang apps ay tinuturing ang Chinese bilang isang wika at naglalagay ng pinyin sa bawat character.",
    "dial_p1_b": "Hindi ang Tova. Piliin ang 简体中文 at makukuha mo ang totoong",
    "dial_p1_c": "sa bawat character. Piliin ang 廣東話 at makukuha mo ang totoong",
    "dial_p1_d": "ang romanization na talagang ginagamit ng mga Hong Kong Cantonese speakers.",
    "dial_p2": "Parehong tanong sa English, dalawang dialect, dalawang tamang bigkas — built-in, walang setting na kailangang baguhin.",
    "feat_eyebrow": "Ano ang nasa loob",
    "feat_h2": "Isang travel translator na hindi humihinto sa border.",
    "feat_lead": "Isang OCR engine na ginawa para sa signage, isang offline-first translation pipeline, at isang conversation mode na rumerespeto sa kung paano talaga nag-uusap ang mga tao.",
    "feat1_title": "Live camera OCR — 11 scripts",
    "feat1_body": "Itutok. Tingnan. Basahin. CJK, Thai, Arabic, Hebrew, Devanagari, Tibetan, at marami pa, kasama ang pinyin, romaji, at hangeul na ipinapakita sa ibabaw ng bawat glyph nang real-time.",
    "feat2_title": "Two-way voice translation",
    "feat2_body": "On-device speech recognition, natural na voice playback, at Pro Plus 3-way Boardroom mode para sa mga meeting sa pagitan ng tatlong wika.",
    "feat3_title": "Gumagana sa Tsina — walang VPN",
    "feat3_body": "Kapag hindi maabot ang backend, awtomatikong gumagana ang on-device neural translation. Apple Translation sa iOS, ML Kit sa Android. Walang setup, walang detour.",
    "feat4_title": "29 offline phrase packs",
    "feat4_body": "Mga piniling travel phrases plus ang kompletong CC-CEDICT Chinese dictionary. Mag-download minsan, gamitin nang pangmatagalan — hindi kailangan ng signal para mahanap ang banyo.",
    "cta_h2_a": "Magdala ng mas magaan. Magpunta nang mas malayo.",
    "cta_h2_b": "Makipag-usap kahit kanino.",
    "cta_lead": "Libre i-download. Walang account, walang sign-up. Dalhin ang Tova sa susunod mong byahe at huwag nang maligaw sa pagsasalin.",
    "cta_reassure_free": "Libre i-download",
    "lang_switcher_label": "Basahin ang pahinang ito sa",
    "view_english": "Read in English",
}


# ─── Build hreflang link block ────────────────────────────────────
def build_hreflang(self_slug=None):
    """Build the <link rel='alternate' hreflang> block for either the
    English page (self_slug=None → href '/') or a locale page."""
    lines = []
    # x-default → English apex
    lines.append('<link rel="alternate" hreflang="x-default" href="https://tovatranslate.app/">')
    lines.append('<link rel="alternate" hreflang="en" href="https://tovatranslate.app/">')
    for loc in LOCALES:
        href = f'https://tovatranslate.app/{loc["slug"]}/'
        lines.append(f'<link rel="alternate" hreflang="{loc["hreflang"]}" href="{href}">')
    return "\n".join(lines)


# ─── Build language switcher block ────────────────────────────────
def build_switcher(active_slug=None, t=None):
    """Footer pill row of language links. active_slug=None for English."""
    label = (t.get("lang_switcher_label") if t else None) or "Read this page in"
    en_label = (t.get("view_english") if t else None) or "Read in English"
    chips = []
    # English chip
    en_active = ' aria-current="page"' if active_slug is None else ''
    chips.append(f'<a class="lang-chip{" lang-chip-active" if active_slug is None else ""}" href="/"{en_active} hreflang="en">English</a>')
    for loc in LOCALES:
        is_active = (loc["slug"] == active_slug)
        cls = "lang-chip-active" if is_active else ""
        attr = ' aria-current="page"' if is_active else ''
        chips.append(f'<a class="lang-chip {cls}" href="/{loc["slug"]}/"{attr} hreflang="{loc["hreflang"]}">{loc["native"]}</a>')
    return f'''<section class="lang-switcher-band">
  <div class="lang-switcher-inner">
    <span class="lang-switcher-label">{label}</span>
    <div class="lang-switcher-chips">
{chr(10).join("      " + c for c in chips)}
    </div>
  </div>
</section>'''


# ─── CSS for the language switcher ────────────────────────────────
SWITCHER_CSS = """
/* ===== Language switcher band ===== */
.lang-switcher-band {
  background: #f6fbfd;
  border-top: 1px solid #e5edf2;
  padding: 32px 24px;
}
.lang-switcher-inner {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px 18px;
}
.lang-switcher-label {
  font-size: 13px;
  font-weight: 700;
  color: #5f6c76;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.lang-switcher-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.lang-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #d0dde4;
  color: #1A1A2E;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.lang-chip:hover {
  background: #e0f2f1;
  border-color: #22A8E0;
  color: #00695C;
}
.lang-chip-active {
  background: #22A8E0;
  border-color: #22A8E0;
  color: #fff;
}
.lang-chip-active:hover {
  background: #1090CC;
  border-color: #1090CC;
  color: #fff;
}
"""


# ─── Build one locale page ────────────────────────────────────────
def build_locale_page(loc, t):
    """Generate one locale's index.html from the English template."""
    src = TEMPLATE

    # 1. <html lang="en"> → locale BCP-47
    src = src.replace('<html lang="en">', f'<html lang="{loc["lang"]}">', 1)

    # 2. Replace marker strings. lang_switcher_label / view_english only
    # exist in the injected switcher block, not the template; skip lookup.
    SKIP_LOOKUP = {"lang_switcher_label", "view_english"}
    for key, en_val in EN_STRINGS.items():
        if key in SKIP_LOOKUP or key not in t:
            continue
        new_val = t[key]
        if en_val not in src:
            print(f"  [warn] {loc['slug']} key='{key}' not found in template")
            continue
        src = src.replace(en_val, new_val, 1)

    # 3. Canonical → locale URL
    src = src.replace(
        '<link rel="canonical" href="https://tovatranslate.app/">',
        f'<link rel="canonical" href="https://tovatranslate.app/{loc["slug"]}/">'
    )

    # 4. OG URL → locale URL
    src = src.replace(
        '<meta property="og:url" content="https://tovatranslate.app/">',
        f'<meta property="og:url" content="https://tovatranslate.app/{loc["slug"]}/">'
    )

    # 5. OG locale → locale BCP-47
    src = src.replace(
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:locale" content="{loc["lang"].replace("-", "_")}">'
    )

    # 6. Inject hreflang block + switcher CSS + apex link (rel=alternate
    # already added below)
    hreflang_block = build_hreflang(self_slug=loc["slug"])
    src = src.replace(
        '<link rel="canonical" href="https://tovatranslate.app/' + loc["slug"] + '/">',
        '<link rel="canonical" href="https://tovatranslate.app/' + loc["slug"] + '/">\n' + hreflang_block
    )

    # 7. Add switcher CSS
    src = src.replace('</style>', SWITCHER_CSS + '\n</style>', 1)

    # 8. Asset paths: rewrite relative paths to absolute (so /zh-cn/ pages
    # still resolve /media/, /faq/, /press/, /privacy/, /terms/, /support/).
    # In the template, links are already absolute starting with "/" — good.

    # 9. Inject the switcher BEFORE the footer
    switcher = build_switcher(active_slug=loc["slug"], t=t)
    # Find the </footer> end OR the last </section> before </body>
    src = src.replace('<footer', switcher + '\n<footer', 1)

    return src


# ─── Build English page (only switcher + hreflang gets added) ─────
def patch_english_page():
    """Add hreflang + language switcher to the English index without
    touching the marketing copy."""
    src = TEMPLATE
    hreflang_block = build_hreflang(self_slug=None)
    # Insert hreflang right after the canonical line
    canonical = '<link rel="canonical" href="https://tovatranslate.app/">'
    if hreflang_block not in src:
        src = src.replace(canonical, canonical + '\n' + hreflang_block, 1)
    # Switcher CSS
    if "lang-switcher-band" not in src:
        src = src.replace('</style>', SWITCHER_CSS + '\n</style>', 1)
    # Switcher block — placed BEFORE the footer
    en_strings_for_switcher = {
        "lang_switcher_label": "Read this page in",
        "view_english": "Read in English",
    }
    switcher = build_switcher(active_slug=None, t=en_strings_for_switcher)
    if "lang-switcher-band" not in src or "lang-switcher-inner" not in src:
        src = src.replace('<footer', switcher + '\n<footer', 1)
    elif switcher not in src:
        # CSS got added but switcher block somehow not — insert it
        src = src.replace('<footer', switcher + '\n<footer', 1)
    return src


def main():
    # Verify every English key from T matches an EN_STRINGS key
    for slug, t in T.items():
        for k in EN_STRINGS:
            if k not in t:
                print(f"[err] T[{slug!r}] missing key {k!r}")

    # Build each locale page
    for loc in LOCALES:
        slug = loc["slug"]
        if slug not in T:
            print(f"[skip] no translations for {slug}")
            continue
        t = T[slug]
        out_dir = ROOT / slug
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "index.html"
        page = build_locale_page(loc, t)
        out_path.write_text(page, encoding="utf-8")
        size_kb = out_path.stat().st_size // 1024
        print(f"wrote /{slug}/index.html ({size_kb} KB)")

    # Patch English page
    en_out = patch_english_page()
    (ROOT / "index.html").write_text(en_out, encoding="utf-8")
    size_kb = (ROOT / "index.html").stat().st_size // 1024
    print(f"patched /index.html ({size_kb} KB) — hreflang + switcher")


if __name__ == "__main__":
    main()
