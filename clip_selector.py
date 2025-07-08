# file: clip_selector.py
import os, re
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video

def select_clips(video_path: str, keywords: list[str], clip_duration: int=30) -> list[str]:
    os.makedirs("outputs", exist_ok=True)
    res = transcribe_video(video_path)
    matches = []
    for seg in res["segments"]:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", seg["text"], re.IGNORECASE):
                start = max(seg["start"] - clip_duration/2, 0)
                end = start + clip_duration
                matches.append((start,end))
                break

    out_paths = []
    for i,(s,e) in enumerate(matches):
        out = f"outputs/clip_{i}.mp4"
        clip = VideoFileClip(video_path).subclip(s,e)
        clip.write_videofile(out, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clip.close()
        out_paths.append(out)
    return out_paths
