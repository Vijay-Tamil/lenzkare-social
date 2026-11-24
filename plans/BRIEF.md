# Brief: LenzKare 45-day video batch (24 Nov 2026 – 7 Jan 2027)

Vijay T (owner-optometrist, LenzKare Optical & Eye Clinic, 1 Thiruveethi Amman Koil Street, Arumbakkam, Chennai)
posts these himself on YouTube Shorts, Instagram Reels, Facebook Reels, Google Business Profile and Threads
(Metricool is over its limit). Goal: maximum reach, subscribers, eye-test bookings and orders.

Repo: /home/claude/lenzkare-social (already set up; `bash tools/setup.sh` already ran). Plan: plans/2026-11-24-45-day-plan.json.
Each item: date, time, kind (eye-health / offer / long), slug, topic, format, voice, yt_category, file (path without extension).
For each item you own, produce:
1. `<file>.json` (video spec), 2. `<file>.mp4`, 3. `<file>.meta.json` (all platform text). Create folders as needed (2026-12/yt, 2027-01/yt).
DO NOT git commit or push — the lead does that.

## Video spec (read the docstring at the top of tools/make_short.py; look at 2026-11/yt/2026-11-23-floaters-flashes.json as a model)
- Shorts: 6–8 scenes, 35–55 s of voice (closing card is added automatically). Hook in scene 1 (`big`, under 8 words, curiosity/emotion).
- Teach more than a basic tip: the "why" (how the eye works, simple words), one "Did you know?" fact (well established; figures only from WHO/AAO/NEI/CDC and say "about"/"studies show"; if unsure leave numbers out), 2–3 practical steps, a "see an eye specialist urgently if…" line where relevant, and an eye-test call to action at the end.
- Use the plan's `voice` and `format`. Speed 1.0–1.1.
- Each scene: `big` (short), `en` (short readable line), `ta` (short, simple, correct spoken Tamil — re-read every word), `say` (English voiceover).
- Voiceover: never say "Arumbakkam" (say "our store"); the voice mispronounces "floaters" (say "floating specks"). Keep sentences short.
- Health rules: general education only, no diagnosis, no medicine names or doses, no AI images of eye diseases. Founder is "Vijay Tamil" (never "Dr").
- Offer rules: home eye test is "₹100 for the whole family" (NEVER "free"); in-store eye test is free; "Buy 1 Get 1 FREE on spectacles with LenzKare Fusion lenses" (never the word "cheaper", never any % discount, never compare Fusion against Essilor/ZEISS); app: "₹500 joining bonus on your first LenzKare app order (min ₹1,500), use within 30 days of downloading; works with Buy 1 Get 1 FREE". NEVER mention APP150 or ₹150. Don't put "Chennai" on product/online-order content except the home eye test and the store. Store appointments are not bookable — only the home eye test is booked (WhatsApp 044 4356 9998).
- Facts you may use: FOE (FrameOra Eyewear) frames from ₹899; single vision lenses from ₹1,500; Fusion lens indexes 1.50/1.56/1.60 only; photochromic +₹1,000 on Fusion lenses; FOE Kids polarised sunglasses (TR90, ages 4–10) are Buy 1 Get 1 FREE; B1G1 also works as one eyeglass + one power sunglass; 6-month frame warranty, 1-year coating warranty, 7-day exchange (no money back), one free lens remake if power doesn't suit after a LenzKare eye test; member levels Silver (₹5,000+ spend) and above get the home eye test fee waived; delivery across India (free in South India; elsewhere ₹80, free above ₹999); no cash on delivery; contact lenses: Acuvue, Bausch+Lomb, Alcon, CooperVision, Freshlook; corporate/community eye camps from 50 people; birthday & anniversary code works with B1G1 on bills ₹1,500+. Home eye test covers Chennai, needs 4+ hours' notice.

## AI images (Figma)
- Call mcp__Figma__create_session (fileKey ak69eNHfbHHDYuTn0FjXqd) once, then mcp__Figma__generate_image (model gpt-image-2.5-sunburst, width 1024, height 1792 for Shorts / width 1792 height 1024 for long videos, sessionId).
- 4 images per Short (use them as `"full": true` scenes; the rest are text scenes). Photoreal Tamil/South Indian people in Chennai homes/streets/offices/schools. Give each Short its own named characters and describe their looks and clothes identically in every prompt so they stay consistent. End every prompt with "Realistic faces and hands. No text, no logos, no watermark." Never show an eye disease close-up, never a phone screen with text, never a LenzKare sign or staff uniform. AI people are never Vijay, staff, real patients or testimonials.
- Download image.url with curl, convert to JPG (PIL, quality 92) at tools/assets/ai/<date>-<name>.jpg.
- Look at every image (Read a small contact sheet): realistic faces/hands/glasses, no garbled text. Regenerate any bad one once.
- If Figma image generation fails (credits), fall back to existing images in tools/assets/ai/ only if they match the topic, otherwise text scenes; report it.

## Rendering + QC (the machine has 2 CPUs — ALWAYS use the shared lock)
- Render: `flock /tmp/claude-0/render.lock python3 tools/make_short.py <file>.json <file>.mp4` (add `--landscape` for long videos).
- QC each video: extract ~6 frames (start, middle, each image scene, end) with ffmpeg at 270x480, make one contact sheet, Read it: no cut-off text, logo visible, Tamil renders, no watermark.
- Audio: `flock /tmp/claude-0/render.lock python3 /tmp/claude-0/tr.py <file>.mp4` prints the peak (must be < 0.95) and a faster-whisper transcript. Every sentence must come out clean; if a word is misheard, rephrase that `say` line and re-render (max 2 retries).
- grep the spec and meta for APP150 / ₹150 — must be zero.

## <file>.meta.json (all platform text; Vijay copy-pastes it)
{
 "date": "...", "time": "13:00", "kind": "...", "topic": "...", "video": "<file>.mp4",
 "youtube": {"title": "<70 chars: hook + emoji + #Shorts (long videos: no #Shorts, end with | LenzKare)>",
   "description": "hook line\nTamil line\n\n4–7 bullet lines of extra useful detail (more than the video)\n\n📍 LenzKare Optical & Eye Clinic, Arumbakkam, Chennai\n💬 Book an eye test on WhatsApp: 044 4356 9998 (wa.me/914443569998)\n🛒 https://www.lenzkare.com\n🔔 Subscribe for daily eye-care tips!\n\n8–10 hashtags starting with #Shorts",
   "tags": [8–12 tags], "category": "Howto & Style" or "People & Blogs" (from yt_category), "made_for_kids": false, "altered_content": true,
   "pinned_comment": "Book an eye test on WhatsApp: wa.me/914443569998 | Order online: lenzkare.com | 📲 Get ₹500 joining bonus on your first LenzKare app order (₹1,500+): play.google.com/store/apps/details?id=com.sd.lenzkare" (+ " | Home eye test in Chennai: ₹100 for the whole family" on offer videos)},
 "instagram": {"caption": "hook + Tamil line + 3–5 short value lines + CTA (WhatsApp 044 4356 9998 / link in bio) — Instagram-friendly, emojis ok", "hashtags": "15–20 hashtags mixing broad (#eyecare), niche (#eyehealthtips) and local (#chennai #chennaidiaries #tamil)", "cover_text": "<6 words for the Reel cover>", "first_comment": "same as YouTube pinned comment", "ai_label": true},
 "facebook": {"caption": "conversational caption, 3–5 lines, Tamil line, CTA, 3–5 hashtags"},
 "gmb": {"text": "Google Business update ≤ 1,000 chars, no hashtags, plain helpful tone, ends with 'Book an eye test on WhatsApp: 044 4356 9998'", "button": "Book" or "Learn more"},
 "threads": {"text": "≤ 450 chars conversational post with a question to drive replies, 1–3 hashtags"}
}

## Report back (keep it short, under 150 words): which files are done, any that failed and why, any image fallback.
