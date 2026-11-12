#!/usr/bin/env python3
"""Insert / refresh the "New ways to use Tova" block on the 14 homepages.

  python3 _build/ways_band.py              # keyboard, Apple Watch, Shortcuts
  python3 _build/ways_band.py --lockscreen # + the iOS 18 Lock Screen button

Only add --lockscreen once Tova 1.4.1 is live on the App Store.
Idempotent: the block is rewritten IN PLACE between <!-- WAYS:start --> /
<!-- WAYS:end --> (since 2026-11-11 it has its own band right under the hero,
so index.html decides where it sits), the CSS between /* WAYS:css */ markers.
The Apple Watch alt text is the "w_alt" key of home_i18n.json.
"""
import html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCK = "--lockscreen" in sys.argv
HOME = json.load(open(ROOT / "_build" / "home_i18n.json", encoding="utf-8"))

# keyboard image per page (localized real captures where they exist)
IMG = {"de": "de", "es": "es", "fr": "fr", "it": "it", "ja": "ja", "ko": "ko",
       "pt": "pt", "zh-cn": "zh-cn", "zh-tw": "zh-tw"}

T = {
"en": dict(
  eyebrow="New ways to use Tova",
  h="Tova now works outside the app, too.",
  kb_t="Tova Keyboard — translate inside any app",
  kb_b="Write in WhatsApp, Messages, WeChat or any chat. Tap Translate, check the reading (pinyin, romaji, Korean romanization or Jyutping) and the “Means:” line, then tap Replace. A Polite switch for hosts, drivers and shops; copy a reply to read it in your language.",
  kb_n="iPhone and Android · 5 free translations a day, unlimited with Pro",
  lk_t="Lock Screen button",
  lk_b="On iOS 18, swap the flashlight or camera button for a Tova button, or add it to Control Center. You choose where it opens: Camera, Translate, Speak or Saved.",
  w_t="Apple Watch (Pro)",
  w_b="Dictate a phrase on your wrist and read the translation there, or start a camera scan on your iPhone.",
  s_t="Siri &amp; Shortcuts",
  s_b="Say “Translate clipboard with Tova” to translate whatever you copied, or add it to the Shortcuts app.",
  alt="Tova Keyboard open in a chat: an English message translated into Chinese, with pinyin, a “Means:” line and a Replace button"),
"de": dict(
  eyebrow="Neue Wege, Tova zu nutzen",
  h="Tova funktioniert jetzt auch außerhalb der App.",
  kb_t="Tova-Tastatur — übersetzen in jeder App",
  kb_b="Schreib in WhatsApp, Nachrichten, WeChat oder jedem Chat. Tippe auf Übersetzen, prüfe die Aussprache (Pinyin, Romaji, koreanische Umschrift oder Jyutping) und die Zeile „Bedeutet:“, dann auf Ersetzen. Mit Höflich-Schalter für Gastgeber, Fahrer und Läden; kopiere eine Antwort, um sie in deiner Sprache zu lesen.",
  kb_n="iPhone und Android · 5 kostenlose Übersetzungen pro Tag, unbegrenzt mit Pro",
  lk_t="Taste auf dem Sperrbildschirm",
  lk_b="Ab iOS 18 ersetzt du die Taschenlampen- oder Kamerataste durch eine Tova-Taste oder fügst sie zum Kontrollzentrum hinzu. Du wählst, was sich öffnet: Kamera, Übersetzen, Sprechen oder Gespeichert.",
  w_t="Apple Watch (Pro)",
  w_b="Diktiere einen Satz am Handgelenk und lies dort die Übersetzung, oder starte einen Kamera-Scan auf dem iPhone.",
  s_t="Kurzbefehle",
  s_b="In der Kurzbefehle-App: übersetze, was du kopiert hast, oder öffne die Kamera mit einem Tipp.",
  alt="Tova-Tastatur in einem Chat: eine Nachricht übersetzt, mit Aussprache, einer Bedeutungszeile und der Taste Ersetzen"),
"es": dict(
  eyebrow="Nuevas formas de usar Tova",
  h="Tova ahora también funciona fuera de la app.",
  kb_t="Teclado Tova: traduce dentro de cualquier app",
  kb_b="Escribe en WhatsApp, Mensajes, WeChat o cualquier chat. Toca Traducir, revisa la pronunciación (pinyin, romaji, romanización coreana o jyutping) y la línea «Significa:», y toca Reemplazar. Con interruptor Cortés para anfitriones, conductores y tiendas; copia una respuesta para leerla en tu idioma.",
  kb_n="iPhone y Android · 5 traducciones gratis al día, ilimitadas con Pro",
  lk_t="Botón en la pantalla de bloqueo",
  lk_b="En iOS 18, cambia el botón de linterna o de cámara por un botón de Tova, o añádelo al centro de control. Tú eliges qué abre: Cámara, Traducir, Hablar o Guardados.",
  w_t="Apple Watch (Pro)",
  w_b="Dicta una frase en la muñeca y lee ahí la traducción, o inicia un escaneo con la cámara del iPhone.",
  s_t="Atajos",
  s_b="En la app Atajos: traduce lo que has copiado o abre la cámara con un toque.",
  alt="Teclado Tova abierto en un chat: un mensaje traducido, con su pronunciación, una línea de significado y el botón Reemplazar"),
"fr": dict(
  eyebrow="De nouvelles façons d'utiliser Tova",
  h="Tova fonctionne désormais aussi en dehors de l'app.",
  kb_t="Clavier Tova : traduisez dans n'importe quelle app",
  kb_b="Écrivez dans WhatsApp, Messages, WeChat ou n'importe quelle messagerie. Touchez Traduire, vérifiez la prononciation (pinyin, romaji, romanisation coréenne ou jyutping) et la ligne « Signifie : », puis touchez Remplacer. Un interrupteur Poli pour les hôtes, chauffeurs et commerçants ; copiez une réponse pour la lire dans votre langue.",
  kb_n="iPhone et Android · 5 traductions gratuites par jour, illimitées avec Pro",
  lk_t="Bouton de l'écran verrouillé",
  lk_b="Sous iOS 18, remplacez le bouton lampe torche ou appareil photo par un bouton Tova, ou ajoutez-le au centre de contrôle. Vous choisissez ce qu'il ouvre : Appareil photo, Traduire, Parler ou Enregistrés.",
  w_t="Apple Watch (Pro)",
  w_b="Dictez une phrase au poignet et lisez la traduction, ou lancez un scan avec l'appareil photo de l'iPhone.",
  s_t="Raccourcis",
  s_b="Dans l'app Raccourcis : traduisez ce que vous avez copié ou ouvrez l'appareil photo en un geste.",
  alt="Clavier Tova ouvert dans une conversation : un message traduit, avec sa prononciation, une ligne de sens et le bouton Remplacer"),
"id": dict(
  eyebrow="Cara baru memakai Tova",
  h="Kini Tova juga bekerja di luar aplikasi.",
  kb_t="Keyboard Tova — terjemahkan di aplikasi apa pun",
  kb_b="Tulis di WhatsApp, Pesan, WeChat, atau chat apa pun. Ketuk Terjemahkan, periksa cara bacanya (pinyin, romaji, romanisasi Korea, atau Jyutping) dan baris “Artinya:”, lalu ketuk Ganti. Ada sakelar Sopan untuk tuan rumah, sopir, dan toko; salin balasan untuk membacanya dalam bahasamu.",
  kb_n="iPhone dan Android · 5 terjemahan gratis per hari, tanpa batas dengan Pro",
  lk_t="Tombol di Layar Kunci",
  lk_b="Di iOS 18, ganti tombol senter atau kamera dengan tombol Tova, atau tambahkan ke Pusat Kontrol. Kamu pilih yang dibuka: Kamera, Terjemahkan, Bicara, atau Tersimpan.",
  w_t="Apple Watch (Pro)",
  w_b="Diktekan kalimat di pergelangan tangan dan baca terjemahannya di sana, atau mulai pindai kamera di iPhone.",
  s_t="Pintasan",
  s_b="Di aplikasi Pintasan: terjemahkan teks yang kamu salin, atau buka kamera dengan sekali ketuk.",
  alt="Keyboard Tova di sebuah chat: pesan bahasa Inggris diterjemahkan ke bahasa Mandarin, dengan pinyin, baris arti, dan tombol Ganti"),
"it": dict(
  eyebrow="Nuovi modi di usare Tova",
  h="Ora Tova funziona anche fuori dall'app.",
  kb_t="Tastiera Tova: traduci dentro qualsiasi app",
  kb_b="Scrivi su WhatsApp, Messaggi, WeChat o qualsiasi chat. Tocca Traduci, controlla la pronuncia (pinyin, romaji, romanizzazione coreana o jyutping) e la riga «Significa:», poi tocca Sostituisci. Con l'interruttore Cortese per host, autisti e negozi; copia una risposta per leggerla nella tua lingua.",
  kb_n="iPhone e Android · 5 traduzioni gratuite al giorno, illimitate con Pro",
  lk_t="Pulsante sulla schermata di blocco",
  lk_b="Con iOS 18, sostituisci il pulsante torcia o fotocamera con un pulsante Tova, oppure aggiungilo al Centro di Controllo. Scegli tu cosa apre: Fotocamera, Traduci, Parla o Salvati.",
  w_t="Apple Watch (Pro)",
  w_b="Detta una frase al polso e leggi lì la traduzione, oppure avvia una scansione con la fotocamera dell'iPhone.",
  s_t="Comandi Rapidi",
  s_b="Nell'app Comandi Rapidi: traduci ciò che hai copiato o apri la fotocamera con un tocco.",
  alt="Tastiera Tova aperta in una chat: un messaggio tradotto, con la pronuncia, una riga di significato e il pulsante Sostituisci"),
"ja": dict(
  eyebrow="Tova の新しい使い方",
  h="Tova がアプリの外でも使えるようになりました。",
  kb_t="Tova キーボード：どのアプリの中でも翻訳",
  kb_b="LINE、WhatsApp、メッセージ、WeChat など、どのチャットでも入力して「翻訳」をタップ。読み方（ピンイン、ローマ字、韓国語ローマ字、粤拼）と「意味:」の行を確かめて「置き換え」をタップします。宿の人、運転手、お店向けの「丁寧」スイッチ付き。相手の返信はコピーすると自分の言語で読めます。",
  kb_n="iPhone・Android 対応 · 1日5回まで無料、Pro なら無制限",
  lk_t="ロック画面のボタン",
  lk_b="iOS 18 なら、ロック画面の懐中電灯やカメラのボタンを Tova のボタンに置き換えたり、コントロールセンターに追加したりできます。開く画面は、カメラ、翻訳、会話、保存済みから選べます。",
  w_t="Apple Watch（Pro）",
  w_b="手首でフレーズを音声入力してその場で翻訳を確認。iPhone のカメラスキャンも手首から開始できます。",
  s_t="ショートカット",
  s_b="ショートカットアプリから、コピーしたテキストの翻訳やカメラの起動がワンタップで。",
  alt="チャットで開いた Tova キーボード：翻訳されたメッセージと読み方、意味の行、置き換えボタン"),
"ko": dict(
  eyebrow="Tova를 쓰는 새로운 방법",
  h="이제 Tova를 앱 밖에서도 쓸 수 있습니다.",
  kb_t="Tova 키보드: 어떤 앱에서든 번역",
  kb_b="카카오톡, WhatsApp, 메시지, WeChat 등 어떤 채팅에서든 입력하고 '번역'을 탭하세요. 읽는 법(병음, 로마자, 한국어 로마자 표기, 월어 병음)과 '의미:' 줄을 확인한 뒤 '바꾸기'를 탭합니다. 숙소, 기사님, 가게에 쓰기 좋은 '공손하게' 스위치도 있고, 상대의 답장은 복사하면 내 언어로 읽을 수 있습니다.",
  kb_n="iPhone 및 Android · 하루 5회 무료, Pro는 무제한",
  lk_t="잠금 화면 버튼",
  lk_b="iOS 18에서는 잠금 화면의 손전등이나 카메라 버튼을 Tova 버튼으로 바꾸거나 제어 센터에 추가할 수 있습니다. 카메라, 번역, 말하기, 저장됨 중 열릴 화면을 고르세요.",
  w_t="Apple Watch(Pro)",
  w_b="손목에서 문장을 받아쓰고 바로 번역을 확인하거나, iPhone 카메라 스캔을 시작하세요.",
  s_t="단축어",
  s_b="단축어 앱에서 복사한 텍스트를 번역하거나 카메라를 한 번에 열 수 있습니다.",
  alt="채팅에서 연 Tova 키보드: 번역된 메시지와 읽는 법, 의미 줄, 바꾸기 버튼"),
"pt": dict(
  eyebrow="Novas formas de usar o Tova",
  h="Agora o Tova também funciona fora do app.",
  kb_t="Teclado Tova: traduza dentro de qualquer app",
  kb_b="Escreva no WhatsApp, Mensagens, WeChat ou em qualquer chat. Toque em Traduzir, confira a pronúncia (pinyin, romaji, romanização coreana ou jyutping) e a linha “Significa:”, depois toque em Substituir. Tem o botão Educado para anfitriões, motoristas e lojas; copie uma resposta para lê-la no seu idioma.",
  kb_n="iPhone e Android · 5 traduções grátis por dia, ilimitadas com o Pro",
  lk_t="Botão na Tela Bloqueada",
  lk_b="No iOS 18, troque o botão de lanterna ou câmera por um botão do Tova, ou adicione-o à Central de Controle. Você escolhe o que ele abre: Câmera, Traduzir, Falar ou Salvos.",
  w_t="Apple Watch (Pro)",
  w_b="Dite uma frase no pulso e leia a tradução ali mesmo, ou comece uma leitura com a câmera do iPhone.",
  s_t="Atalhos",
  s_b="No app Atalhos: traduza o que você copiou ou abra a câmera com um toque.",
  alt="Teclado Tova aberto em um chat: uma mensagem traduzida, com a pronúncia, uma linha de significado e o botão Substituir"),
"th": dict(
  eyebrow="วิธีใหม่ในการใช้ Tova",
  h="ตอนนี้ใช้ Tova นอกแอปได้แล้ว",
  kb_t="แป้นพิมพ์ Tova — แปลได้ในทุกแอป",
  kb_b="พิมพ์ใน LINE, WhatsApp, ข้อความ, WeChat หรือแชทไหนก็ได้ แตะ แปล แล้วตรวจคำอ่าน (พินอิน โรมาจิ อักษรโรมันเกาหลี หรือยฺหวิดเพ็ง) และบรรทัด “หมายถึง:” จากนั้นแตะ แทนที่ มีสวิตช์ สุภาพ สำหรับเจ้าของที่พัก คนขับ และร้านค้า และคัดลอกข้อความตอบกลับเพื่ออ่านเป็นภาษาของคุณ",
  kb_n="iPhone และ Android · แปลฟรีวันละ 5 ครั้ง ไม่จำกัดเมื่อใช้ Pro",
  lk_t="ปุ่มบนหน้าจอล็อก",
  lk_b="บน iOS 18 เปลี่ยนปุ่มไฟฉายหรือกล้องเป็นปุ่ม Tova หรือเพิ่มไว้ในศูนย์ควบคุม แล้วเลือกหน้าที่จะเปิด: กล้อง แปล พูด หรือที่บันทึกไว้",
  w_t="Apple Watch (Pro)",
  w_b="พูดประโยคบนข้อมือแล้วอ่านคำแปลได้ทันที หรือเริ่มสแกนด้วยกล้องบน iPhone",
  s_t="คำสั่งลัด",
  s_b="ในแอปคำสั่งลัด: แปลข้อความที่คัดลอกไว้ หรือเปิดกล้องได้ในแตะเดียว",
  alt="แป้นพิมพ์ Tova ในแชท: ข้อความภาษาอังกฤษแปลเป็นภาษาจีน พร้อมพินอิน บรรทัดความหมาย และปุ่มแทนที่"),
"tl": dict(
  eyebrow="Mga bagong paraan ng paggamit ng Tova",
  h="Gumagana na rin ang Tova sa labas ng app.",
  kb_t="Tova Keyboard — mag-translate sa kahit anong app",
  kb_b="Mag-type sa Messenger, WhatsApp, Messages, WeChat o kahit anong chat. I-tap ang Translate, tingnan ang basa (pinyin, romaji, Korean romanization o Jyutping) at ang linyang “Means:”, saka i-tap ang Replace. May Polite switch para sa host, driver at tindahan; kopyahin ang reply para mabasa ito sa sarili mong wika.",
  kb_n="iPhone at Android · 5 libreng translation kada araw, walang limit sa Pro",
  lk_t="Button sa Lock Screen",
  lk_b="Sa iOS 18, palitan ang flashlight o camera button ng Tova button, o idagdag ito sa Control Center. Ikaw ang pipili kung saan ito bubukas: Camera, Translate, Speak o Saved.",
  w_t="Apple Watch (Pro)",
  w_b="Mag-dictate ng parirala sa iyong pulso at basahin doon ang translation, o magsimula ng camera scan sa iPhone.",
  s_t="Shortcuts",
  s_b="Sa Shortcuts app: i-translate ang kinopya mo, o buksan ang camera sa isang tap.",
  alt="Tova Keyboard sa isang chat: mensaheng Ingles na isinalin sa Chinese, may pinyin, linyang Means at Replace button"),
"vi": dict(
  eyebrow="Những cách mới để dùng Tova",
  h="Giờ đây Tova dùng được cả bên ngoài ứng dụng.",
  kb_t="Bàn phím Tova — dịch ngay trong mọi ứng dụng",
  kb_b="Gõ trong Zalo, WhatsApp, Tin nhắn, WeChat hay bất kỳ ứng dụng trò chuyện nào. Chạm Dịch, xem cách đọc (bính âm, romaji, phiên âm tiếng Hàn hoặc Việt bính) và dòng “Nghĩa là:”, rồi chạm Thay thế. Có công tắc Lịch sự khi nhắn cho chủ nhà, tài xế và cửa hàng; sao chép tin trả lời để đọc bằng ngôn ngữ của bạn.",
  kb_n="iPhone và Android · 5 lượt dịch miễn phí mỗi ngày, không giới hạn với Pro",
  lk_t="Nút trên Màn hình khóa",
  lk_b="Trên iOS 18, thay nút đèn pin hoặc camera bằng nút Tova, hoặc thêm vào Trung tâm điều khiển. Bạn chọn màn hình sẽ mở: Camera, Dịch, Nói hoặc Đã lưu.",
  w_t="Apple Watch (Pro)",
  w_b="Đọc một câu trên cổ tay và xem bản dịch ngay tại đó, hoặc bắt đầu quét bằng camera trên iPhone.",
  s_t="Phím tắt",
  s_b="Trong ứng dụng Phím tắt: dịch nội dung bạn vừa sao chép, hoặc mở camera chỉ với một chạm.",
  alt="Bàn phím Tova trong một cuộc trò chuyện: tin nhắn tiếng Anh được dịch sang tiếng Trung, có bính âm, dòng nghĩa và nút Thay thế"),
"zh-cn": dict(
  eyebrow="Tova 的新用法",
  h="现在在 App 之外也能用 Tova。",
  kb_t="Tova 键盘：在任何 App 里翻译",
  kb_b="在微信、WhatsApp、信息等任何聊天 App 里输入，点按“翻译”，核对读音（拼音、罗马字、韩文罗马字或粤拼）和“意思”一行，再点按“替换”。还有“礼貌”开关，给房东、司机和店家发消息更得体；复制对方的回复，就能用你的语言读懂。",
  kb_n="iPhone 和 Android · 每天免费 5 次，Pro 不限次数",
  lk_t="锁定屏幕按钮",
  lk_b="在 iOS 18 上，把锁定屏幕的手电筒或相机按钮换成 Tova 按钮，或添加到控制中心。打开哪个页面由你选：相机、翻译、说话或收藏。",
  w_t="Apple Watch（Pro）",
  w_b="在手腕上说一句话，直接看译文；也能从手表开始用 iPhone 相机扫描。",
  s_t="快捷指令",
  s_b="在“快捷指令”App 中，一键翻译你复制的文字，或打开相机。",
  alt="在聊天中打开的 Tova 键盘：已翻译的消息、读音、意思一行和“替换”按钮"),
"zh-tw": dict(
  eyebrow="Tova 的新用法",
  h="現在在 App 之外也能用 Tova。",
  kb_t="Tova 鍵盤：在任何 App 裡翻譯",
  kb_b="在 LINE、WhatsApp、訊息、WeChat 等任何聊天 App 裡輸入，點一下「翻譯」，核對讀音（拼音、羅馬字、韓文羅馬字或粵拼）和「意思」一行，再點一下「取代」。還有「禮貌」開關，傳訊給房東、司機和店家更得體；複製對方的回覆，就能用你的語言讀懂。",
  kb_n="iPhone 和 Android · 每天免費 5 次，Pro 不限次數",
  lk_t="鎖定畫面按鈕",
  lk_b="在 iOS 18 上，把鎖定畫面的手電筒或相機按鈕換成 Tova 按鈕，或加入控制中心。打開哪個頁面由你選：相機、翻譯、說話或收藏。",
  w_t="Apple Watch（Pro）",
  w_b="在手腕上說一句話，直接看譯文；也能從手錶開始用 iPhone 相機掃描。",
  s_t="捷徑",
  s_b="在「捷徑」App 中，一鍵翻譯你複製的文字，或打開相機。",
  alt="在聊天中打開的 Tova 鍵盤：已翻譯的訊息、讀音、意思一行和「取代」按鈕"),
}

ICON = {
 "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
 "watch": '<rect x="6" y="6" width="12" height="12" rx="3"/><path d="M9 6l1-4h4l1 4M9 18l1 4h4l1-4"/>',
 "shortcut": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
}

CSS = """  /* WAYS:css */
  .ways { margin: 0; }
  .ways-grid { display: grid; grid-template-columns: 1fr; gap: 28px; align-items: center; margin-top: 24px; }
  @media (min-width: 820px) { .ways-grid { grid-template-columns: 320px 1fr; gap: 48px; } }
  .ways-shot { position: relative; width: 260px; max-width: 100%; margin: 0 auto 44px; }
  .ways-shot img.ways-kb { display: block; width: 100%; height: auto;
    border-radius: 30px; border: 7px solid #0B2536; box-shadow: 0 22px 50px rgba(0, 25, 45, 0.25); background: #fff; }
  .ways-shot img.ways-watch { position: absolute; right: -44px; bottom: -40px; width: 118px; height: auto;
    border-radius: 30px; border: 5px solid #23272E; background: #000; box-shadow: 0 14px 34px rgba(0, 25, 45, 0.42); }
  .ways-list { display: grid; gap: 14px; }
  .ways-item { display: flex; gap: 14px; align-items: flex-start; padding: 18px 20px; background: #fff;
    border: 1px solid #EDF1F3; border-radius: 16px; box-shadow: 0 2px 12px rgba(15, 40, 60, 0.06); }
  .ways-item .feature-icon { flex: none; margin: 0; }
  .ways-item h3 { font-weight: 700; font-size: 17px; margin: 2px 0 6px; color: var(--fg); letter-spacing: -0.01em; }
  .ways-item p { font-size: 14.5px; color: var(--muted); margin: 0; line-height: 1.55; }
  .ways-item .ways-note { margin-top: 8px; font-weight: 600; color: var(--accent); font-size: 13.5px; }
  .ways-item.ways-first { border-color: #C8E9F5; }
  .ways-item.ways-first h3 { font-size: 19px; }
  .ways-item .ways-note a { color: var(--accent); text-underline-offset: 3px; }
  /* WAYS:css-end */
"""

KB_ICON = '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 15h10"/>'

KB_LINK = {"en": "See how Tova Keyboard works →", "zh-cn": "看看 Tova 键盘怎么用 →", "ko": "Tova 키보드 사용법 보기 →"}

def item(icon, title, body, note=None, lead=False):
    n = f'\n          <p class="ways-note">{note}</p>' if note else ""
    cls = "ways-item ways-first" if lead else "ways-item"
    return f'''        <div class="{cls}">
          <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></div>
          <div><h3>{title}</h3>
          <p>{body}</p>{n}</div>
        </div>'''

def block(lang):
    t = T[lang]
    img = f"/media/app/keyboard-{IMG[lang]}.webp" if lang in IMG else "/media/app/keyboard.webp"
    walt = html.escape(HOME.get(lang, {}).get("w_alt") or HOME["en"]["w_alt"], quote=True)
    kb_note = t["kb_n"]
    # Link to the keyboard page in this language, where one exists.
    kb_page = "keyboard/index.html" if lang == "en" else f"{lang}/keyboard/index.html"
    if lang in KB_LINK and (ROOT / kb_page).exists():
        href = "/keyboard/" if lang == "en" else f"/{lang}/keyboard/"
        kb_note += f' · <a href="{href}">{KB_LINK[lang]}</a>'
    items = [item(KB_ICON, t["kb_t"], t["kb_b"], kb_note, lead=True)]
    if LOCK:
        items.append(item(ICON["lock"], t["lk_t"], t["lk_b"]))
    items.append(item(ICON["watch"], t["w_t"], t["w_b"]))
    items.append(item(ICON["shortcut"], t["s_t"], t["s_b"]))
    items_html = "\n".join(items)
    return f'''<!-- WAYS:start -->
    <div class="ways" id="new-ways">
      <div class="section-eyebrow">{t["eyebrow"]}</div>
      <h2 class="section-h2">{t["h"]}</h2>
      <div class="ways-grid">
        <figure class="ways-shot">
          <img class="ways-kb" src="{img}" width="280" height="608" loading="lazy" decoding="async" alt="{t["alt"]}">
          <img class="ways-watch" src="/media/app/watch-translate.webp" width="208" height="248" loading="lazy" decoding="async" alt="{walt}" data-ta="w_alt">
        </figure>
        <div class="ways-list">
{items_html}
        </div>
      </div>
    </div>
    <!-- WAYS:end -->
'''

FEAT = ['"Tova Keyboard: translate inside WhatsApp, Messages, WeChat and any other app, with readings (iPhone and Android)"',
        '"Apple Watch app (Pro)"',
        '"Siri and Shortcuts: translate the clipboard"']
FEAT_LOCK = '"Lock Screen and Control Center button that opens a chosen screen (iOS 18)"'

def page(lang):
    return ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")

ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
for lang in T:
    if ONLY and lang != ONLY:
        continue
    p = page(lang); s = p.read_text()
    # CSS
    s = re.sub(r"  /\* WAYS:css \*/.*?/\* WAYS:css-end \*/\n", "", s, flags=re.S)
    anchor = "  /* ===== Tova Learn cross-promo ===== */"
    assert s.count(anchor) == 1, (lang, "css anchor")
    s = s.replace(anchor, CSS + anchor)
    # block
    pat = re.compile(r"    <!-- WAYS:start -->.*?<!-- WAYS:end -->\n", re.S)
    assert len(pat.findall(s)) == 1, (lang, "WAYS markers")
    s = pat.sub(lambda m: "    " + block(lang), s)
    # the same keyboard capture sits in the hero rail
    kb = re.compile(r'<img class="rail-phone rail-kb" src="[^"]*"([^>]*?) alt="[^"]*">')
    assert len(kb.findall(s)) == 1, (lang, "hero rail keyboard image")
    kimg = f"/media/app/keyboard-{IMG[lang]}.webp" if lang in IMG else "/media/app/keyboard.webp"
    s = kb.sub(lambda m: f'<img class="rail-phone rail-kb" src="{kimg}"{m.group(1)} alt="{T[lang]["alt"]}">', s)
    # JSON-LD featureList (English in every page)
    want = FEAT + ([FEAT_LOCK] if LOCK else [])
    for f in FEAT + [FEAT_LOCK]:
        s = s.replace(",\n        " + f, "")
    fl = re.search(r'("featureList": \[\n(?:.*\n)*?)(        "[^\n]*")\n      \]', s)
    assert fl, (lang, "featureList")
    add = "".join(",\n        " + f for f in want)
    s = s[:fl.end(2)] + add + s[fl.end(2):]
    p.write_text(s)
    print("ok", lang)
