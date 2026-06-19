# 🎬 TikTok Transcriber

> Turn a TikTok link **or an entire profile** into clean Markdown transcripts, each one
> stamped with the post's metrics: views, likes, comments, reposts, **saves** and date.

Built to drop straight into [Obsidian](https://obsidian.md), but the output is just plain
Markdown, so it works anywhere. No login, no cookies, no browser automation.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![whisper](https://img.shields.io/badge/transcription-Groq%20Whisper-orange)

---

## ✨ What you get

Run it on one video or a whole creator's profile and you get one note per video:

```markdown
# 10 broken ChatGPT codes to change how it answers you

- **Profile:** sabrina_ramonov
- **Date:** 2026-06-05 15:43 (BRT)
- **Views:** 11K (10,800)
- **Likes:** 457
- **Comments:** 74
- **Saves:** 590
- **Shares/Reposts:** 156
- **Language:** English
- **Link:** https://www.tiktok.com/@sabrina_ramonov/video/7647983635416616206

## Caption
...

## Transcript
...
```

---

## 🚀 Features

- **One video or a full profile** — paste a link, an `@handle`, or just a username.
- **Every public metric** — views, likes, comments, reposts, **saves**, and the post date.
  (TikTok exposes saves publicly; most tools don't surface them.)
- **No login / no cookies** — `yt-dlp` lists the profile and pulls the metrics for you.
- **Accurate transcripts** — audio goes through [Groq](https://groq.com)'s
  `whisper-large-v3`, which auto-detects the language.
- **Resumable** — re-running skips videos that are already done and retries the ones
  that failed. Great for big back-catalogs.
- **Self-healing downloads** — yt-dlp's TikTok extractor hiccups sometimes; a built-in
  retry recovers it.

---

## 📦 Requirements

| Tool | Why | Install |
|------|-----|---------|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | lists profiles + downloads audio | `pip install -U yt-dlp` |
| [`ffmpeg`](https://ffmpeg.org) | extracts the audio track | [ffmpeg.org/download](https://ffmpeg.org/download.html) |
| `curl` | calls the Groq API | preinstalled on macOS/Linux/Win10+ |
| **Groq API key** | transcription (free tier) | [console.groq.com/keys](https://console.groq.com/keys) |

No Python packages needed beyond the standard library.

---

## 🛠️ Setup

```bash
git clone https://github.com/pedroccm/tiktok-transcriber.git
cd tiktok-transcriber

# 1) free Groq key -> https://console.groq.com/keys
export GROQ_API_KEY="gsk_..."           # Windows (PowerShell): $env:GROQ_API_KEY="gsk_..."

# 2) (optional) where notes are saved. Defaults to ~/Documents/Obsidian Vault/TikTok
export OBSIDIAN_VAULT="/path/to/your/Obsidian Vault"
```

---

## ▶️ Usage

```bash
# one video
python tiktok.py "https://www.tiktok.com/@user/video/7647983635416616206"

# a whole profile (newest -> oldest)
python tiktok.py "https://www.tiktok.com/@sabrina_ramonov"

# just the 50 most recent
python tiktok.py @sabrina_ramonov --limit 50

# several at once
python tiktok.py @user1 @user2 "https://www.tiktok.com/@user3/video/123"
```

Flags:
- `--limit N` — only the **N newest** videos of the profile.
- `--force` — ignore the resume cache and re-transcribe everything.

Windows users can also double-click-friendly run `tiktok.cmd @user`.

> **Big profiles:** some creators have thousands of videos. Check first with
> `yt-dlp --flat-playlist --print id "https://www.tiktok.com/@user" | wc -l`, then use
> `--limit`. The Groq free tier limits audio minutes per hour/day; the script waits out
> the limit and continues, and it's resumable, so you can chip away across runs.

---

## 📁 Output

```
$OBSIDIAN_VAULT/TikTok/
└── <profile>/
    └── <video title>/
        └── Transcript.md
```

The title comes from the first line of the caption (cleaned up). Already-transcribed
videos are detected by their link, so nothing gets done twice.

---

## ⚙️ How it works

1. **List** — for a profile, `yt-dlp --flat-playlist` enumerates every video URL.
2. **Download** — `yt-dlp -x` grabs just the audio as a tiny 16 kHz mono mp3 (with retry).
3. **Transcribe** — the mp3 is sent to Groq Whisper (`whisper-large-v3`).
4. **Write** — caption + metrics + transcript are saved as a Markdown note.

Metrics come directly from yt-dlp's metadata (`view_count`, `like_count`, `comment_count`,
`repost_count`, `save_count`, `timestamp`) — no scraping, no second request.

---

## 🤖 Use it as a Claude Code skill

This repo is also a [Claude Code](https://claude.com/claude-code) skill. Drop it into your
skills folder and invoke it in chat:

```bash
git clone https://github.com/pedroccm/tiktok-transcriber.git \
  ~/.claude/skills/tiktok-transcriber
```

Then just say *"transcribe this TikTok profile: @user"* and Claude runs it for you.

---

## 📝 Notes & limits

- **Saves** are TikTok-only here; the Instagram sibling tool can't get them (Instagram
  keeps saves private to the post owner).
- Hidden counts come back as `-1` from yt-dlp and are simply omitted from the note.
- Photo (carousel) posts are skipped — there's no speech to transcribe.

---

## 📄 License

MIT — see [LICENSE](LICENSE).
