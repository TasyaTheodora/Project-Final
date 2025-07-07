# file: clip_selector.py

import os
import re
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from utils import transcribe_video  # pastikan utils.py di folder yang sama

def select_clips(video_path: str, keywords: list[str], clip_duration: int = 30) -> list[str]:
    """
    Memotong klip berdurasi clip_duration detik
    di sekitar setiap keyword yang ditemukan.
    Mengembalikan list path ke klip yang dibuat.
    """

    # 1. Pastikan folder output ada
    os.makedirs("outputs", exist_ok=True)

    # 2. Transkripsi video dan dapatkan segments
    print("🕒 Running transcription...")
    result = transcribe_video(video_path, verbose=False)
    segments = result.get("segments", [])

    # 3. Cari kata kunci di setiap segment
    matches: list[tuple[float, float]] = []
    for seg in segments:
        text = seg.get("text", "")
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text, flags=re.IGNORECASE):
                # potong di tengah-tengah segmen
                start = max(seg["start"] - clip_duration/2, 0)
                end   = start + clip_duration
                matches.append((start, end))
                break  # cukup satu match per segmen

    # 4. Extract subclips via ffmpeg
    out_paths: list[str] = []
    for i, (start, end) in enumerate(matches):
        out_file = os.path.join("outputs", f"clip_{i}.mp4")
        try:
            ffmpeg_extract_subclip(video_path, start, end, targetname=out_file)
            out_paths.append(out_file)
        except Exception as e:
            print(f"⚠️ Gagal memproses klip #{i}: {e}")

    return out_paths
