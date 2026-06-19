#!/usr/bin/env python3
"""
TikTok -> Transcript -> Markdown notes

Usage:
    python tiktok.py <link_or_profile> [...] [--limit N] [--force]

Accepts:
    video   -> https://www.tiktok.com/@user/video/123...   (or vm.tiktok.com/...)
    profile -> https://www.tiktok.com/@user   or   @user   or   user

For a profile, yt-dlp lists every video (no login / no cookies needed) and pulls
ALL the public metrics: views, likes, comments, reposts, saves and the post date.
Each video's audio is downloaded, transcribed with Groq Whisper, and saved as a
Markdown note (great for Obsidian).

Requirements: yt-dlp, ffmpeg and curl on PATH. Set GROQ_API_KEY (free key at
https://console.groq.com/keys). Output dir = $OBSIDIAN_VAULT/TikTok
(defaults to ~/Documents/Obsidian Vault/TikTok), override with $OBSIDIAN_VAULT.
"""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "whisper-large-v3")

VAULT = Path(os.environ.get("OBSIDIAN_VAULT") or (Path.home() / "Documents" / "Obsidian Vault"))
OUTPUT_DIR = VAULT / "TikTok"

INVALID_FS = r'[\\/:*?"<>|]'


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def humanize(n):
    if n is None or n < 0:                       # yt-dlp uses -1 when a count is hidden
        return None
    if n < 1000:
        return str(n)
    if n >= 1_000_000:
        short = f"{n/1_000_000:.1f}M".replace(".0M", "M")
    else:
        short = f"{round(n/1000)}K"
    return f"{short} ({n:,})"


def clean_title(caption, fallback):
    if not caption:
        return fallback
    line = caption.strip().splitlines()[0].strip()
    line = re.sub(r"#\S+", "", line)                         # drop hashtags
    line = re.sub(r"[^\w\sÀ-ſ.,!?'\"\-:()]", "", line)  # drop emoji/symbols
    line = re.sub(r"\s+", " ", line).strip().strip("?!.:, ").strip()
    if not line:
        line = re.sub(r"\s+", " ", re.sub(r"#\S+", "", caption)).strip() or fallback
    return line[:80].strip()


def safe_name(name):
    name = re.sub(INVALID_FS, "", name).strip().rstrip(".")
    return name or "tiktok"


def fmt_date(ts):
    """Epoch (UTC) -> 'YYYY-MM-DD HH:MM (BRT)'. Brazil = UTC-3, no DST."""
    if not ts:
        return None
    dt = datetime.datetime.utcfromtimestamp(int(ts) - 3 * 3600)
    return dt.strftime("%Y-%m-%d %H:%M") + " (BRT)"


def _parse_wait(msg):
    """Read 'try again in 1m23.4s' from a Groq error message -> seconds."""
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", msg)
    if not m:
        return None
    return int(m.group(1) or 0) * 60 + float(m.group(2))


def transcribe(mp3, retries=6):
    if not GROQ_API_KEY:
        raise RuntimeError("Set the GROQ_API_KEY env var (free key at https://console.groq.com/keys).")
    cmd = [
        "curl", "-s", "https://api.groq.com/openai/v1/audio/transcriptions",
        "-H", f"Authorization: Bearer {GROQ_API_KEY}",
        "-F", f"file=@{mp3}",
        "-F", f"model={GROQ_MODEL}",
        "-F", "response_format=verbose_json",
        "-F", "temperature=0",
    ]
    for attempt in range(retries):
        r = run(cmd)
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise RuntimeError(f"Unexpected response from Groq:\n{r.stdout[:800]}")
        if "error" in data:
            msg = data["error"].get("message", str(data["error"]))
            if "rate" in msg.lower() and "limit" in msg.lower() and attempt < retries - 1:
                wait = min((_parse_wait(msg) or 25) + 1, 300)
                print(f"   Groq rate limit, waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"Groq error: {msg}")
        return data.get("text", "").strip(), data.get("language", "")


def metric_lines(meta, lang):
    """Build the metric bullets in a fixed order (omits whatever is missing)."""
    out = []
    d = fmt_date(meta.get("date_ts"))
    if d:
        out.append(f"- **Date:** {d}")
    for label, key in [("Views", "views"), ("Likes", "likes"), ("Comments", "comments"),
                       ("Saves", "saves"), ("Shares/Reposts", "reshares")]:
        v = humanize(meta.get(key))
        if v:
            out.append(f"- **{label}:** {v}")
    if lang:
        out.append(f"- **Language:** {lang}")
    return out


def video_id(url):
    """Numeric video id (used for dedup). Short links have no id in the URL."""
    m = re.search(r"/(?:video|photo|v)/(\d+)", url or "")
    return m.group(1) if m else None


def classify(arg):
    """Decide whether the argument is a single video or a profile."""
    a = arg.strip()
    if re.search(r"tiktok\.com/.+/(?:video|photo)/\d+", a) or re.search(r"/v/\d+", a):
        return "single", a
    if re.search(r"(?:vm|vt)\.tiktok\.com/", a):             # short link -> treat as single
        return "single", a
    m = re.search(r"tiktok\.com/@([\w.\-]+)", a)
    user = (m.group(1) if m else a).lstrip("@").strip("/")
    return "profile", user


def list_profile(user):
    """List every video of a profile via yt-dlp (no login)."""
    user = user.lstrip("@").strip("/")
    url = f"https://www.tiktok.com/@{user}"
    r = run(["yt-dlp", "--flat-playlist", "--dump-json", url])
    urls = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = e.get("url") or e.get("webpage_url")
        if u and "/video/" in u:                             # videos only (skip /photo/)
            urls.append(u)
    if not urls:
        raise RuntimeError((r.stderr or "no videos found").strip()[-500:])
    return urls


def download_audio(url, tmp, retries=4):
    """Download audio (mp3 16kHz mono) + info json, with retry.

    yt-dlp's TikTok extractor fails transiently ('Unable to extract universal
    data for rehydration'); it almost always succeeds on a retry. TikTok needs
    no cookies, so we never try the browser.
    """
    out_tpl = str(Path(tmp) / "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp", "-x", "--audio-format", "mp3",
        "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1",
        "--write-info-json", "--no-playlist",
        "-o", out_tpl, url,
    ]
    last_err = ""
    for attempt in range(retries):
        r = run(cmd)
        mp3 = next(Path(tmp).glob("*.mp3"), None)
        info = next(Path(tmp).glob("*.info.json"), None)
        if mp3 and info:
            return mp3, info
        last_err = (r.stderr or r.stdout or "").strip()
        if attempt < retries - 1:
            time.sleep(3)
    raise RuntimeError(f"yt-dlp failed to download after {retries} attempts.\n{last_err[-400:]}")


def assemble_meta(info, url):
    """Metrics straight from yt-dlp's info json (TikTok already provides everything)."""
    perfil = (info.get("uploader") or "").lstrip("@")
    if not perfil:
        m = re.search(r"tiktok\.com/@([\w.\-]+)", info.get("uploader_url") or url or "")
        perfil = m.group(1) if m else "tiktok"
    return {
        "perfil": perfil,
        "caption": (info.get("description") or info.get("title") or "").strip(),
        "url": info.get("webpage_url") or info.get("original_url") or url,
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "comments": info.get("comment_count"),
        "saves": info.get("save_count"),
        "reshares": info.get("repost_count"),
        "date_ts": info.get("timestamp"),
    }


def build_note(meta, transcript, lang):
    perfil = (meta.get("perfil") or "tiktok").lstrip("@")
    caption = (meta.get("caption") or "").strip()
    url = meta.get("url") or ""
    title = clean_title(caption, video_id(url) or "tiktok")

    lines = [f"# {title}", "", f"- **Profile:** {perfil}"]
    lines += metric_lines(meta, lang)
    lines.append(f"- **Link:** {url}")
    lines += ["", "## Caption", "", caption if caption else "_(no caption)_", "", "---", "",
              "## Transcript", "", transcript if transcript else "_(empty transcript)_", ""]
    return perfil, title, "\n".join(lines)


def save(perfil, title, content):
    folder = OUTPUT_DIR / safe_name(perfil) / safe_name(title)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "Transcript.md"
    path.write_text(content, encoding="utf-8")
    return path


def load_done_ids():
    """Ids of videos already transcribed (scans existing notes' Link line)."""
    done = set()
    if not OUTPUT_DIR.exists():
        return done
    for f in OUTPUT_DIR.glob("**/Transcript.md"):
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(r"\*\*Link:\*\*\s*(\S+)", txt)
        vid = video_id(m.group(1)) if m else None
        if vid:
            done.add(vid)
    return done


def process(url):
    print(f"\n=> {url}")
    with tempfile.TemporaryDirectory() as tmp:
        print("   downloading audio...")
        mp3, info_path = download_audio(url, tmp)
        info = json.loads(Path(info_path).read_text(encoding="utf-8"))
        print("   transcribing (Groq Whisper)...")
        transcript, lang = transcribe(mp3)
    meta = assemble_meta(info, url)
    perfil, title, content = build_note(meta, transcript, lang)
    path = save(perfil, title, content)
    print(f"   OK -> {path}")
    print(f"   {len(transcript)} chars | language: {lang or '?'}"
          f" | date: {fmt_date(meta.get('date_ts')) or '?'}"
          f" | saves: {meta.get('saves') if meta.get('saves') is not None else '?'}")
    return path


def main():
    args = sys.argv[1:]
    limit, force, targets = None, False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--limit", "-n"):
            i += 1
            limit = int(args[i])
        elif a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
        elif a == "--force":
            force = True
        else:
            targets.append(a)
        i += 1

    if not targets:
        print("Usage: python tiktok.py <link_or_profile> [...] [--limit N] [--force]")
        print("  video   -> https://www.tiktok.com/@user/video/123...")
        print("  profile -> https://www.tiktok.com/@user   or   @user")
        sys.exit(1)

    # expand profiles into video lists; keep single links as-is
    jobs = []
    for t in targets:
        kind, val = classify(t)
        if kind == "single":
            jobs.append(val)
        else:
            print(f"\n# profile @{val} - listing videos...")
            try:
                vids = list_profile(val)
            except Exception as e:
                print(f"  FAILED: {e}")
                continue
            print(f"  {len(vids)} videos found")
            jobs.extend(vids)

    # intra-list dedup, preserving order (newest first)
    uniq, seen = [], set()
    for u in jobs:
        vid = video_id(u)
        if vid and vid in seen:
            continue
        if vid:
            seen.add(vid)
        uniq.append(u)
    if limit:
        uniq = uniq[:limit]                  # window of the N newest

    # within the window, skip ones that already have a note (resume/retry failures)
    done = set() if force else load_done_ids()
    queue, skipped = [], 0
    for u in uniq:
        vid = video_id(u)
        if vid and vid in done:
            skipped += 1
            continue
        queue.append(u)

    print(f"\n>> {len(queue)} to transcribe | {skipped} already done (skipped)\n")

    fails = 0
    for idx, url in enumerate(queue, 1):
        print(f"[{idx}/{len(queue)}]", end=" ")
        try:
            process(url)
        except Exception as e:
            fails += 1
            print(f"   FAILED: {e}")
    ok = len(queue) - fails
    print(f"\nDone: {ok} ok, {fails} failed, {skipped} skipped.")
    sys.exit(1 if (fails and not ok) else 0)


if __name__ == "__main__":
    main()
