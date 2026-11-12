# LenzKare social

Finished posters and reels for @lenzkare_official (Instagram, Facebook, YouTube), one folder per month.
Scheduled through Metricool. Public on purpose: these are published posts only, never customer data.

## tools/ — LenzKare YouTube video maker
`bash tools/setup.sh` then `python3 tools/make_short.py spec.json out.mp4 [--landscape]`.
Makes Shorts (1080x1920) / long videos (1920x1080) with an offline English voiceover, Tamil + English on-screen text, the LenzKare logo and the standard closing card. Daily YouTube specs and videos live in `YYYY-MM/yt/`.
