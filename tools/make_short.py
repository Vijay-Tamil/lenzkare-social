#!/usr/bin/env python3
"""LenzKare video maker: builds a YouTube Short (1080x1920) or long video (1920x1080)
from a JSON spec, with an offline English voiceover, Tamil + English on-screen text,
the real LenzKare logo, soft background music and a fixed LenzKare closing card.

Usage:
  bash tools/setup.sh                      # once per session (voice model + pip deps)
  python3 tools/make_short.py spec.json out.mp4 [--landscape]

Spec:
{
  "voice": "hf_alpha",            # hf_alpha / hf_beta (Indian female), hm_omega / hm_psi (Indian male)
  "speed": 1.0,
  "scenes": [
    {"en": "Can you read this in 3 seconds?",   # big on-screen English line
     "ta": "3 வினாடியில் படிக்க முடியுமா?",       # Tamil line under it (optional)
     "say": "Can you read this line in three seconds?",  # voiceover (English)
     "image": "tools/assets/pro-1.jpg",          # optional photo (product photo, or AI image in tools/assets/ai/)
     "full": true,                               # optional: photo fills the whole screen (Shorts only),
                                                 #   text sits on a dark gradient at the bottom;
                                                 #   no label on screen; only the LenzKare logo appears
     "big": "E  F  P",                           # optional extra-large text (eye-chart style)
     "video": "tools/assets/clips/x.mp4",        # optional: a video clip (AI clip or Vijay's real home eye test
                                                 #   clip) fills the screen instead of a photo; same text overlay
                                                 #   as "full"; looped/trimmed to the voiceover length; its own
                                                 #   sound is dropped. "video_start": seconds to skip at the start.
    }
  ],
  "cta": true                      # append the standard LenzKare closing card (default true)
}
"""
import json, os, subprocess, sys, tempfile, textwrap
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HERE, "fonts", n)
TEAL, TEAL_D, MINT, INK = (13, 148, 136), (15, 118, 110), (240, 253, 250), (15, 23, 42)
SR = 24000

def font(name, size):
    f = ImageFont.truetype(F(name), size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    return f

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def bg(W, H):
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    t = np.clip(0.65 * y + 0.35 * x, 0, 1)[..., None]
    a, b = np.array(TEAL_D), np.array((8, 70, 66))
    arr = (a * (1 - t) + b * t).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse((W * 0.55, -H * 0.1, W * 1.4, H * 0.35), fill=(255, 255, 255, 18))
    d.ellipse((-W * 0.4, H * 0.7, W * 0.5, H * 1.2), fill=(255, 255, 255, 14))
    return im

LOGO = Image.open(os.path.join(HERE, "assets", "logo.png")).convert("RGBA")

def logo_pill(im, cx, y, h):
    lw = int(LOGO.width * h / LOGO.height)
    lg = LOGO.resize((lw, h), Image.LANCZOS)
    pad = int(h * 0.25)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((cx - lw // 2 - pad, y - pad, cx + lw // 2 + pad, y + h + pad), radius=pad * 2, fill="white")
    im.paste(lg, (cx - lw // 2, y), lg)

def photo_card(im, path, box):
    x0, y0, x1, y1 = box
    p = Image.open(path).convert("RGB")
    bw, bh = x1 - x0, y1 - y0
    s = max(bw / p.width, bh / p.height)
    p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1), Image.LANCZOS)
    l, t = (p.width - bw) // 2, (p.height - bh) // 2
    p = p.crop((l, t, l + bw, t + bh))
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, bw, bh), radius=40, fill=255)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0 + 10, y0 + 20, x1 + 10, y1 + 20), radius=40, fill=(0, 0, 0, 90))
    im.paste(sh.filter(ImageFilter.GaussianBlur(18)), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    im.paste(p, (x0, y0), m)

def render_full(sc, idx, n, W, H, out):
    """Full-screen photo scene: image covers the frame, dark gradient at the bottom, text on top of it.
    For a "video" scene it writes a transparent overlay PNG (gradient + text + logo) to lay over the clip."""
    y = np.linspace(0, 1, H)[:, None]
    a = (np.clip((y - 0.36) / 0.30, 0, 1) ** 1.2 * 230 + np.clip((0.12 - y) / 0.12, 0, 1) * 110).astype(np.uint8)
    shade = Image.fromarray(np.repeat(a, W, axis=1), "L")
    if sc.get("video"):
        im = Image.new("RGBA", (W, H), (4, 40, 37, 0))
        im.putalpha(shade)
    else:
        p = Image.open(sc["image"]).convert("RGB")
        s = max(W / p.width, H / p.height)
        p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1), Image.LANCZOS)
        l, t = (p.width - W) // 2, int((p.height - H) * sc.get("crop_y", 0.0))
        im = p.crop((l, t, l + W, t + H))
        dark = Image.new("RGB", (W, H), (4, 40, 37))
        im = Image.composite(dark, im, shade)
    d = ImageDraw.Draw(im)
    M = int(W * 0.08)
    bw = W - 2 * M
    d.rounded_rectangle((M, int(H * 0.035), M + bw, int(H * 0.035) + 10), radius=5, fill=(180, 200, 198))
    d.rounded_rectangle((M, int(H * 0.035), M + int(bw * (idx + 1) / n), int(H * 0.035) + 10), radius=5, fill="white")
    logo_pill(im, W // 2, int(H * 0.065), int(H * 0.045))
    textw = W - 2 * M
    ops = []
    if sc.get("big"):
        fb = font("Poppins-Bold.ttf", int(H * 0.062))
        for ln in wrap(d, sc["big"], fb, textw):
            ops.append(("y", ln, fb, int(fb.size * 1.15)))
        ops.append(("gap", "", None, int(H * 0.012)))
    fe = font("Poppins-Bold.ttf", int(H * 0.037))
    for ln in wrap(d, sc.get("en", ""), fe, textw):
        ops.append(("w", ln, fe, int(fe.size * 1.25)))
    if sc.get("ta"):
        ops.append(("gap", "", None, int(H * 0.016)))
        ft = font("Catamaran.ttf", int(H * 0.028))
        for ln in wrap(d, sc["ta"], ft, textw - 60):
            ops.append(("t", ln, ft, int(ft.size * 1.6)))
    total = sum(o[3] for o in ops)
    y = int(H * 0.80) - total  # keep clear of the Shorts UI at the bottom
    cx = W // 2
    for kind, ln, f, h in ops:
        if kind in ("w", "y"):
            d.text((cx + 3, y + 4), ln, font=f, fill=(0, 0, 0), anchor="ma")
            d.text((cx, y), ln, font=f, fill=((253, 224, 71) if kind == "y" else "white"), anchor="ma")
        elif kind == "t":
            tw = d.textlength(ln, font=f)
            d.rounded_rectangle((cx - tw / 2 - 24, y - 6, cx + tw / 2 + 24, y + f.size * 1.35), radius=18, fill=MINT)
            d.text((cx, y), ln, font=f, fill=TEAL_D, anchor="ma")
        y += h
    if sc.get("ai_label", False):
        fs = font("Poppins-Bold.ttf", int(H * 0.014))
        d.text((M + 6, int(H * 0.058)), "AI-generated visual", font=fs, fill=(235, 245, 244), anchor="la")
    im.save(out)

def render_scene(sc, idx, n, W, H, out):
    if sc.get("video") or (sc.get("full") and sc.get("image") and W < H):
        return render_full(sc, idx, n, W, H, out)
    im = bg(W, H)
    d = ImageDraw.Draw(im)
    land = W > H
    M = int(W * (0.06 if land else 0.08))
    # progress bar
    bw = W - 2 * M
    d.rounded_rectangle((M, int(H * 0.035), M + bw, int(H * 0.035) + 10), radius=5, fill=(255, 255, 255, 60))
    d.rounded_rectangle((M, int(H * 0.035), M + int(bw * (idx + 1) / n), int(H * 0.035) + 10), radius=5, fill="white")
    logo_pill(im, W // 2 if not land else W - M - 120, int(H * (0.065 if not land else 0.07)), int(H * (0.045 if not land else 0.07)))
    textw = W - 2 * M
    has_img = bool(sc.get("image"))
    if land and has_img:
        photo_card(im, sc["image"], (W // 2 + M // 2, int(H * 0.2), W - M, int(H * 0.88)))
        textw = W // 2 - M - M // 2
    elif has_img:
        ph = int(H * 0.32)
        photo_card(im, sc["image"], (M, int(H * 0.56), W - M, int(H * 0.56) + ph))
    ops = []  # (kind, text, font, height)
    if sc.get("big"):
        fb = font("Poppins-Bold.ttf", int(H * (0.075 if not land else 0.12)))
        for ln in wrap(d, sc["big"], fb, textw):
            ops.append(("w", ln, fb, int(fb.size * 1.15)))
        ops.append(("gap", "", None, int(H * 0.02)))
    fe = font("Poppins-Bold.ttf", int(H * (0.043 if not land else 0.065)))
    for ln in wrap(d, sc.get("en", ""), fe, textw):
        ops.append(("w", ln, fe, int(fe.size * 1.25)))
    if sc.get("ta"):
        ops.append(("gap", "", None, int(H * 0.02)))
        ft = font("Catamaran.ttf", int(H * (0.03 if not land else 0.045)))
        for ln in wrap(d, sc["ta"], ft, textw - 60):
            ops.append(("t", ln, ft, int(ft.size * 1.6)))
    total = sum(o[3] for o in ops)
    top, bot = int(H * 0.15), (int(H * 0.53) if (has_img and not land) else int(H * 0.88))
    y = max(top, top + (bot - top - total) // 2)
    cx = M + textw // 2
    for kind, ln, f, h in ops:
        if kind == "w":
            d.text((cx, y), ln, font=f, fill="white", anchor="ma")
        elif kind == "t":
            tw = d.textlength(ln, font=f)
            d.rounded_rectangle((cx - tw / 2 - 24, y - 6, cx + tw / 2 + 24, y + f.size * 1.35), radius=18, fill=MINT)
            d.text((cx, y), ln, font=f, fill=TEAL_D, anchor="ma")
        y += h
    im.save(out)

def cta_scene(W, H, out):
    im = Image.new("RGB", (W, H), MINT)
    d = ImageDraw.Draw(im)
    land = W > H
    lh = int(H * (0.12 if not land else 0.25))
    lw = int(LOGO.width * lh / LOGO.height)
    lg = LOGO.resize((lw, lh), Image.LANCZOS)
    y = int(H * (0.2 if not land else 0.1))
    im.paste(lg, (W // 2 - lw // 2, y), lg)
    y += lh + int(H * 0.04)
    f1 = font("Poppins-Bold.ttf", int(H * (0.034 if not land else 0.055)))
    f2 = font("Catamaran.ttf", int(H * (0.028 if not land else 0.045)))
    lines = [("Optical & Eye Clinic, Arumbakkam, Chennai", f2, INK),
             ("Book an eye test on WhatsApp", f1, TEAL_D),
             ("044 4356 9998", f1, INK),
             ("Order online: lenzkare.com", f1, TEAL_D),
             ("கண் பரிசோதனைக்கு இன்றே புக் செய்யுங்கள்", f2, INK),
             ("Subscribe for daily eye-care tips", f2, TEAL)]
    maxw = W * 0.82
    for t, f, c in lines:
        while d.textlength(t, font=f) > maxw:
            f = ImageFont.truetype(f.path, f.size - 2, layout_engine=ImageFont.Layout.RAQM)
            try: f.set_variation_by_name("Bold")
            except Exception: pass
        d.text((W // 2, y), t, font=f, fill=c, anchor="ma")
        y += int(f.size * 1.6)
    im.save(out)

_K = None
def tts(text, voice, speed, out):
    global _K
    from kokoro_onnx import Kokoro
    if _K is None:
        md = os.environ.get("KOKORO_DIR", "/home/claude/tts")
        _K = Kokoro(os.path.join(md, "kokoro.onnx"), os.path.join(md, "voices.bin"))
    s, sr = _K.create(text, voice=voice, speed=speed, lang="en-us")
    if sr != SR:
        import scipy.signal as ss
        s = ss.resample(s, int(len(s) * SR / sr))
    sf.write(out, s, SR)
    return len(s) / SR

def music(seconds, out):
    t = np.arange(int(seconds * SR)) / SR
    chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
    y = np.zeros_like(t)
    seg = 4.0
    for i, ch in enumerate(chords * int(seconds // (seg * 4) + 2)):
        a, b = int(i * seg * SR), int((i + 1) * seg * SR)
        if a >= len(t): break
        tt = t[a:b]
        env = np.minimum(1, np.minimum((tt - tt[0]) / 0.8, (tt[-1] - tt + 1e-3) / 0.8))
        for f in ch:
            y[a:b] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt)) / 6
    # light pulse
    y *= 0.9 + 0.1 * np.sin(2 * np.pi * 2 * t)
    fade = np.minimum(1, np.minimum(t / 1.5, (seconds - t) / 1.5))
    sf.write(out, (y * fade * 0.25).astype(np.float32), SR)

def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    land = "--landscape" in sys.argv
    W, H = (1920, 1080) if land else (1080, 1920)
    spec = json.load(open(spec_path))
    voice, speed = spec.get("voice", "hf_alpha"), spec.get("speed", 1.0)
    scenes = spec["scenes"]
    tmp = tempfile.mkdtemp()
    n = len(scenes)
    clips = []
    for i, sc in enumerate(scenes):
        png, wav = f"{tmp}/s{i}.png", f"{tmp}/s{i}.wav"
        render_scene(sc, i, n, W, H, png)
        dur = tts(sc["say"], voice, speed, wav) + 0.35 if sc.get("say") else sc.get("seconds", 2.5)
        clips.append((png, wav if sc.get("say") else None, dur, sc.get("video"), sc.get("video_start", 0)))
    if spec.get("cta", True):
        png, wav = f"{tmp}/cta.png", f"{tmp}/cta.wav"
        cta_scene(W, H, png)
        dur = tts("Book your eye test with LenzKare on WhatsApp, and subscribe for daily eye care tips.", voice, speed, wav) + 0.6
        clips.append((png, wav, dur, None, 0))
    # voice track
    total = sum(c[2] for c in clips)
    vo = np.zeros(int(total * SR) + SR, dtype=np.float32)
    pos = 0.0
    for png, wav, dur, *_ in clips:
        if wav:
            s, _ = sf.read(wav, dtype="float32")
            f = min(len(s) // 4, int(0.012 * SR))
            if f > 0:
                s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
            a = int((pos + 0.15) * SR)
            vo[a:a + len(s)] += s[: len(vo) - a]
        pos += dur
    vo = vo[: int(total * SR)]
    pk = float(np.abs(vo).max()) or 1.0
    vo *= 0.6 / pk  # voice peaks at -4.4 dBFS: no clipping, mixed with music below
    sf.write(f"{tmp}/vo.wav", vo, SR)
    music(total, f"{tmp}/music.wav")
    # video: each scene a slow zoom, concat
    parts = []
    for i, (png, _, dur, vid, vstart) in enumerate(clips):
        p = f"{tmp}/p{i}.mp4"
        frames = int(dur * 30)
        if vid:
            fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1[b];"
                  f"[b][1:v]overlay=0:0,format=yuv420p")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-ss", str(vstart), "-i", vid,
                            "-i", png, "-filter_complex", fc, "-frames:v", str(frames), "-an",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", p], check=True)
            parts.append(p)
            continue
        z = f"zoompan=z='min(1+0.0006*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-vf", f"scale={W*2}:{H*2},{z},format=yuv420p",
                        "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", p], check=True)
        parts.append(p)
    with open(f"{tmp}/list.txt", "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-i", f"{tmp}/vo.wav", "-i", f"{tmp}/music.wav",
                    "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=0.45[m];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false,aresample=44100[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"{out}  {total:.1f}s")

if __name__ == "__main__":
    main()
