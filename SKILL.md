---
name: tiktok-transcriber
description: Transcribes one TikTok video or an entire TikTok profile to Markdown notes (great for Obsidian), including all public metrics (views, likes, comments, reposts, saves and post date). Downloads audio with yt-dlp and transcribes with Groq Whisper, no login or cookies needed. Use when the user sends a TikTok link or @profile and asks to transcribe it / pull the transcripts.
triggerPhrases:
  - "tiktok-transcriber"
  - "transcribe this tiktok"
  - "transcribe this tiktok profile"
  - "pull the transcripts of this tiktok"
  - "transcreve esse tiktok"
  - "transcreve o perfil do tiktok"
  - "pega as transcrições desse tiktok"
---

# TikTok Transcriber

Turns a TikTok link **or** a whole `@profile` into Markdown transcript notes, each
one carrying the public metrics (views, likes, comments, reposts, **saves**, date).

## How to use

```bash
python tiktok.py "https://www.tiktok.com/@user/video/123..."   # one video
python tiktok.py "https://www.tiktok.com/@user"                # whole profile
python tiktok.py @user --limit 50                              # newest 50 only
```

If the user just pastes a TikTok link / `@handle` and asks to transcribe, this applies too.

## Instructions for Claude

### Step 1 — Get the target
A TikTok video URL (`/video/<id>`, also `vm.tiktok.com` short links) **or** a profile
(`tiktok.com/@user`, `@user`, or just `user`). Profiles can be huge: check the count first
with `yt-dlp --flat-playlist --print id "https://www.tiktok.com/@user" | wc -l` and, if it is
large, confirm the scope with the user and run with `--limit N`.

### Step 2 — Make sure the env is set
- `GROQ_API_KEY` must be set (free key at https://console.groq.com/keys).
- Output goes to `$OBSIDIAN_VAULT/TikTok` (default `~/Documents/Obsidian Vault/TikTok`).
  Set `OBSIDIAN_VAULT` to point at the user's vault if needed.

### Step 3 — Run
```bash
python tiktok.py "<link_or_profile>" [--limit N] [--force]
```
For large profiles, run it in the background (it is **resumable**: re-running skips notes
that already exist and retries the ones that failed). Groq's free tier rate-limits by the
minute/hour; the script waits and continues on its own.

### Step 4 — Report
Show the user the output folder and the run summary (`X ok, Y failed, Z skipped`). yt-dlp's
TikTok extractor fails transiently on some videos (`Unable to extract universal data for
rehydration`); the built-in retry recovers most, and a second pass picks up the rest.

## Output

`$OBSIDIAN_VAULT/TikTok/<profile>/<title>/Transcript.md` — one note per video with the
caption, the full transcript, and the metrics. **Saves** are included (TikTok exposes them
publicly, unlike Instagram).

## Dependencies
- `yt-dlp`, `ffmpeg`, `curl` on PATH.
- A Groq API key in `GROQ_API_KEY`.
- No Instagram/TikTok login or cookies required.
