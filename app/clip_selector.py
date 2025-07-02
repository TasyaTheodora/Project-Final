# file: app/clip_selector.py
from moviepy.editor import VideoFileClip
from utils import transcribe_video
import re, os

def select_clips(video_path: str, keywords: list[str], clip_duration: int = 30) -> list[str]:
    """
    Memotong klip berdurasi clip_duration detik
    di sekitar setiap keyword yang ditemukan.
    """
    # 1. Transkrip & cari segmen
    result = transcribe_video(video_path, verbose=False)
    segments = result.get("segments", [])

    matches = []
    for seg in segments:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", seg["text"], flags=re.IGNORECASE):
                start = max(seg["start"] - clip_duration/2, 0)
                end   = start + clip_duration
                matches.append((start, end))
                break

    out_paths = []
    clip = VideoFileClip(video_path)
    for i, (s, e) in enumerate(matches):
        sub = clip.subclip(s, e)
        out_file = os.path.join("outputs", f"clip_{i}.mp4")
        sub.write_videofile(out_file, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        out_paths.append(out_file)

    return out_paths
