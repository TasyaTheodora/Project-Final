# app/clip_selector.py
from moviepy.editor import VideoFileClip
from .utils import transcribe_video
import re
import os

def select_clips(
    video_path: str,
    keywords: list[str],
    clip_duration: int = 30
) -> list[str]:
    """
    Memotong klip berdurasi `clip_duration` detik
    di sekitar setiap keyword yang ditemukan.
    """
    # 1. Transkrip video & ambil segmen
    result = transcribe_video(video_path, verbose=False)
    segments = result.get("segments", [])

    # 2. Kumpulkan timestamps saat keyword muncul
    matches = []
    for seg in segments:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", seg["text"], flags=re.IGNORECASE):
                matches.append(seg["start"])
                break
    timestamps = sorted(set(matches))

    # 3. Buat folder output
    os.makedirs("outputs", exist_ok=True)
    clip_paths = []

    # 4. Potong Video
    video = VideoFileClip(video_path)
    for i, t in enumerate(timestamps):
        start = max(t - clip_duration/2, 0)
        end = min(start + clip_duration, video.duration)
        clip = video.subclip(start, end)
        out_path = f"outputs/clip_{i+1}_{int(start)}-{int(end)}.mp4"
        clip.write_videofile(
            out_path,
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        clip_paths.append(out_path)
    video.close()

    return clip_paths
    