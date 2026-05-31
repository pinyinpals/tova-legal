#!/usr/bin/env python3
"""Tova Learn family OG/social card (1200x630) — Tova Learn + 3 real app icons."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
OUT = "og-learn.png"  # overwrite the existing OG card (referenced by the page)
CN = "tova-learn-icon.png"
JA = "tova-learn-japanese-icon.png"
KO = "tova-learn-korean-icon.png"
TEAL=(34,168,224); TEALB=(70,192,238); TEALD=(16,144,204); WHITE=(255,255,255)
BLACK="/System/Library/Fonts/Supplemental/Arial Black.ttf"
BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG="/System/Library/Fonts/Supplemental/Arial.ttf"
def F(p,s): return ImageFont.truetype(p,s)
def tw(d,t,f): b=d.textbbox((0,0),t,font=f); return b[2]-b[0]
def ctr(d,t,f,cx,y,fill): d.text((cx-tw(d,t,f)/2,y),t,font=f,fill=fill)

img=Image.new("RGB",(W,H)); px=img.load()
for y in range(H):
    t=y/(H-1)
    c=(tuple(int(TEALB[i]+(TEAL[i]-TEALB[i])*(t*2)) for i in range(3)) if t<.5
       else tuple(int(TEAL[i]+(TEALD[i]-TEAL[i])*((t-.5)*2)) for i in range(3)))
    for x in range(W): px[x,y]=c
img=img.convert("RGBA")
ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
od.ellipse([-150,-150,300,300],fill=(255,255,255,34))
od.ellipse([W-300,H-320,W+160,H+140],fill=(0,70,110,60))
img=Image.alpha_composite(img,ov.filter(ImageFilter.GaussianBlur(70)))
d=ImageDraw.Draw(img)

ctr(d,"Tova Learn",F(BLACK,84),W/2,52,WHITE)
ctr(d,"Wake. Trace. Speak.",F(BOLD,40),W/2,152,(240,250,255))

S=150; GAP=64; total=S*3+GAP*2; sx=(W-total)/2; top=232
def rounded(path,size,rad):
    ic=Image.open(path).convert("RGBA").resize((size,size),Image.LANCZOS)
    m=Image.new("L",(size,size),0); ImageDraw.Draw(m).rounded_rectangle([0,0,size,size],radius=rad,fill=255)
    o=Image.new("RGBA",(size,size),(0,0,0,0)); o.paste(ic,(0,0),m); return o
sh=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
for i in range(3):
    x=sx+i*(S+GAP); sd.rounded_rectangle([x,top+8,x+S,top+S+8],radius=34,fill=(8,30,54,110))
img=Image.alpha_composite(img,sh.filter(ImageFilter.GaussianBlur(18))); d=ImageDraw.Draw(img)
labels=["Chinese","Japanese","Korean"]
for i,(p,lab) in enumerate(zip([CN,JA,KO],labels)):
    x=int(sx+i*(S+GAP)); img.alpha_composite(rounded(p,S,34),(x,top))
    d=ImageDraw.Draw(img); ctr(d,lab,F(BOLD,28),x+S/2,top+S+14,WHITE)
ctr(d,"Chinese · Japanese · Korean — one character a day",F(REG,30),W/2,H-78,(235,248,255))
ctr(d,"From the makers of Tova Translate",F(REG,25),W/2,H-40,(225,243,253))
img.convert("RGB").save(OUT)
print("wrote",OUT,img.size)
