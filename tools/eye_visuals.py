#!/usr/bin/env python3
"""Draws simple, accurate eye-education visuals (no AI) for LenzKare Shorts.
Each output is 1404x921, the shape of the photo card in tools/make_short.py.
Usage: python3 tools/eye_visuals.py <kind> <out.jpg> [street.jpg]
kinds: eye_nerve (eye cross-section, optic nerve highlighted)
       side_vision (normal vs side vision fading, from a street photo)
       glaucoma_checks (3 tiles: eye pressure, optic nerve, side vision)
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1404, 921
TEAL, TEAL_D, MINT, INK, AMBER = (13,148,136), (15,118,110), (240,253,250), (15,23,42), (245,158,11)

def font(name, size):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", name), size, layout_engine=ImageFont.Layout.RAQM)
    try: f.set_variation_by_name("Bold")
    except Exception: pass
    return f
EN = lambda s: font("Poppins-Bold.ttf", s)
TA = lambda s: font("Catamaran.ttf", s)

def pill(d, xy, text, f, fill, color, anchor="mm", pad=(26, 12)):
    x, y = xy
    tw = d.textlength(text, font=f); th = f.size
    d.rounded_rectangle((x - tw/2 - pad[0], y - th*0.62 - pad[1], x + tw/2 + pad[0], y + th*0.62 + pad[1]), radius=28, fill=fill)
    d.text((x, y), text, font=f, fill=color, anchor="mm")

def eye_nerve(out):
    S = 2
    im = Image.new("RGB", (W*S, H*S), MINT); d = ImageDraw.Draw(im)
    s = lambda *v: [int(a*S) for a in v]
    cx, cy, r = 560, 470, 300
    # optic nerve (behind eyeball)
    glow = Image.new("RGBA", im.size, (0,0,0,0)); g = ImageDraw.Draw(glow)
    g.polygon(s(cx+r-40, cy-20, 1300, cy+70, 1300, cy+170, cx+r-40, cy+80), fill=(245,158,11,140))
    im.paste(glow.filter(ImageFilter.GaussianBlur(30)), (0,0), glow.filter(ImageFilter.GaussianBlur(30)))
    d.polygon(s(cx+r-40, cy+5, 1300, cy+90, 1300, cy+150, cx+r-40, cy+60), fill=AMBER, outline=(180,83,9), width=6)
    # cornea bulge, then eyeball on top so only the front bulge shows
    d.ellipse(s(cx-r-55, cy-135, cx-r+110, cy+135), fill="white", outline=TEAL_D, width=10)
    d.ellipse(s(cx-r, cy-r, cx+r, cy+r), fill="white", outline=TEAL_D, width=10)
    # retina (back half)
    d.arc(s(cx-r+22, cy-r+22, cx+r-22, cy+r-22), -80, 80, fill=(225,90,90), width=26)
    # iris + pupil gap
    d.rectangle(s(cx-r+52, cy-150, cx-r+68, cy-48), fill=(110,70,40))
    d.rectangle(s(cx-r+52, cy+48, cx-r+68, cy+150), fill=(110,70,40))
    # lens
    d.ellipse(s(cx-r+72, cy-95, cx-r+150, cy+95), fill=(200,230,250), outline=(70,130,180), width=6)
    # light rays to the back
    for dy in (-60, 60):
        d.line(s(60, cy+dy, cx-r+110, cy+dy*0.6), fill=(250,204,21), width=8)
        d.line(s(cx-r+110, cy+dy*0.6, cx+r-30, cy), fill=(250,204,21), width=6)
    im = im.resize((W, H), Image.LANCZOS); d = ImageDraw.Draw(im)
    # labels
    d.line((cx-r+110, cy-100, 250, 170), fill=INK, width=5)
    pill(d, (230, 140), "Lens", EN(46), "white", INK)
    d.line((cx+r-40, cy-180, 960, 150), fill=INK, width=5)
    pill(d, (1010, 125), "Retina", EN(46), "white", (190,40,40))
    d.line((1150, cy+120, 1080, 730), fill=INK, width=5)
    pill(d, (1080, 735), "Optic nerve", EN(58), AMBER, INK)
    pill(d, (1080, 830), "கண் நரம்பு", TA(54), "white", TEAL_D)
    d.text((1290, cy+40), "to the brain", font=EN(36), fill=INK, anchor="rm")
    im.save(out, quality=93)

def side_vision(out, src):
    p = Image.open(src).convert("RGB")
    pw = W // 2 - 9
    s = H / p.height; p = p.resize((int(p.width*s), H), Image.LANCZOS)
    l = (p.width - pw) // 2; a = p.crop((l, 0, l+pw, H))
    yy, xx = np.mgrid[0:H, 0:pw]
    rr = np.sqrt(((xx - pw/2)/(pw*0.62))**2 + ((yy - H*0.5)/(H*0.62))**2)
    m = np.clip((rr - 0.38) / 0.42, 0, 1) ** 1.3
    blur = np.asarray(a.filter(ImageFilter.GaussianBlur(26)), float)
    dark = blur * 0.25 + np.array((25,25,28)) * 0.75
    b = np.asarray(a, float) * (1 - m[..., None]) + dark * m[..., None]
    b = Image.fromarray(b.clip(0,255).astype(np.uint8))
    im = Image.new("RGB", (W, H), "white"); im.paste(a, (0, 0)); im.paste(b, (W - pw, 0))
    d = ImageDraw.Draw(im)
    pill(d, (pw//2, H-70), "Normal vision", EN(46), "white", TEAL_D)
    pill(d, (W - pw//2, H-70), "Side vision fading", EN(46), AMBER, INK)
    pill(d, (W - pw//2, 70), "Glaucoma (simulation)", EN(34), (15,23,42), "white")
    im.save(out, quality=93)

def glaucoma_checks(out):
    im = Image.new("RGB", (W, H), MINT); d = ImageDraw.Draw(im)
    d.text((W//2, 80), "A full eye check looks at:", font=EN(58), fill=INK, anchor="mm")
    tw, gap = 400, 52; x0 = (W - 3*tw - 2*gap)//2
    items = [("Eye pressure", "கண் அழுத்தம்"), ("Optic nerve", "கண் நரம்பு"), ("Side vision", "பக்கப் பார்வை")]
    for i, (en, ta) in enumerate(items):
        x = x0 + i*(tw+gap); cx, cy = x + tw//2, 370
        d.rounded_rectangle((x, 170, x+tw, H-50), radius=40, fill="white", outline=(190,225,220), width=4)
        if i == 0:   # eye + gauge
            xs = np.linspace(-150, 150, 61)
            top = [(cx+x, cy+20-100*(1-(x/150)**2)) for x in xs]
            bot = [(cx+x, cy+20+80*(1-(x/150)**2)) for x in xs[::-1]]
            d.polygon(top+bot, fill="white")
            d.ellipse((cx-55, cy-35, cx+55, cy+75), fill=TEAL); d.ellipse((cx-22, cy-2, cx+22, cy+42), fill=INK)
            d.line(top+bot+[top[0]], fill=TEAL_D, width=10, joint="curve")
            d.arc((cx-95, cy-205, cx+95, cy-15), 200, 340, fill=AMBER, width=14)
            a = math.radians(300); d.line((cx, cy-110, cx + 80*math.cos(a), cy-110 + 80*math.sin(a)), fill=INK, width=8)
            d.ellipse((cx-10, cy-120, cx+10, cy-100), fill=INK)
        elif i == 1:  # eyeball + nerve
            d.polygon((cx+60, cy+10, cx+175, cy+55, cx+175, cy+95, cx+60, cy+60), fill=AMBER)
            d.ellipse((cx-120, cy-100, cx+90, cy+110), fill="white", outline=TEAL_D, width=10)
            d.arc((cx-105, cy-85, cx+75, cy+95), -70, 70, fill=(225,90,90), width=14)
            d.ellipse((cx-128, cy-40, cx-88, cy+40), fill=TEAL)
        else:  # visual field target
            for k, rr in enumerate((140, 100, 60)):
                d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), outline=TEAL_D, width=6)
            d.ellipse((cx-14, cy-14, cx+14, cy+14), fill=AMBER)
            for ang in (30, 140, 230, 320):
                a = math.radians(ang); px, py = cx + 120*math.cos(a), cy + 120*math.sin(a)
                d.ellipse((px-11, py-11, px+11, py+11), fill=INK)
        d.text((cx, 640), en, font=EN(46), fill=INK, anchor="mm")
        pill(d, (cx, 740), ta, TA(42), MINT, TEAL_D, pad=(18, 8))
    im.save(out, quality=93)

if __name__ == "__main__":
    k, out = sys.argv[1], sys.argv[2]
    {"eye_nerve": lambda: eye_nerve(out), "side_vision": lambda: side_vision(out, sys.argv[3]),
     "glaucoma_checks": lambda: glaucoma_checks(out)}[k]()
