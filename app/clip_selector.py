# app/clip_selector.py
from moviepy.video.io.VideoFileClip import VideoFileClip
from .utils import transcribe_video
import re
import os

def select_clips(
    video_path: str,
    keywords: list[str],
    clip_duration: int = 30
) -> list[str]:
    """
    Memotong klip berdurasi clip_duration detik
    di sekitar setiap keyword yang ditemukan.
    """
    # 1. Transkrip video & ambil segmen
    print("⏳  Running transcription…")
    result   = transcribe_video(video_path, verbose=False)
    segments = result.get("segments", [])
    print(f"🔍  Total segments: {len(segments)}")

    # 2. Pilih segmen yang matching keyword
    matches = []
    for seg in segments:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", seg["text"], flags=re.IGNORECASE):
                print(f"  ‣ Found '{kw}' @ {seg['start']:.1f}s: {seg['text']!r}")
                matches.append((seg["start"], seg["end"]))
                break

    # 3. Merge segmen yang berdekatan (<1 detik gap)
    merged = []
    for start, end in sorted(matches):
        if not merged or start - merged[-1][1] > 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    # 4. Potong klip dengan margin ±2 detik
    os.makedirs("outputs", exist_ok=True)
    video = VideoFileClip(video_path)
    clip_paths = []
    for i, (s, e) in enumerate(merged, start=1):
        start = max(s - 2, 0)
        end   = min(e + 2, video.duration)
        out   = f"outputs/clip_{i}_{int(start)}-{int(end)}.mp4"
        print(f"✂️  Generating clip {i}: {start:.1f}s → {end:.1f}s")
        clip = video.subclip(start, end)
        clip.write_videofile(out, audio_codec="aac", verbose=False, logger=None)
        clip_paths.append(out)
    video.close()

    print(f"✅  Done! {len(clip_paths)} clips generated.")
    return clip_paths
