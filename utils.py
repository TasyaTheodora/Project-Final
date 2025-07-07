# file: utils.py
import os
import tempfile
import re
import warnings
import random
import whisper  # pastikan sudah pip install git+https://github.com/openai/whisper.git

# Paksa moviepy/imageio-ffmpeg pakai binari ffmpeg kita
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.abspath(
    "ffmpeg/ffmpeg-2025-06-28-git-cfd1f81e7d-full_build/bin/ffmpeg.exe"
)

def load_whisper_model():
    try:
        return whisper.load_model("base")
    except Exception as e:
        warnings.warn(f"Gagal muat Whisper model: {e}")
        return None

_whisper_model = load_whisper_model()

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    if _whisper_model is None:
        raise RuntimeError("Model Whisper lokal tidak tersedia.")
    # ekstrak audio
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    cmd = (
        f"\"{os.environ['IMAGEIO_FFMPEG_EXE']}\" -y -i \"{video_path}\" "
        f"-ar 16000 -ac 1 -vn \"{tmp.name}\""
    )
    os.system(cmd)
    # transkripsi
    result = _whisper_model.transcribe(tmp.name, verbose=verbose)
    # bersihin file sementara
    try: os.remove(tmp.name)
    except: pass

    text = result.get("text", "").strip()
    segments = [
        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
        for s in result.get("segments", [])
    ]
    return {"text": text, "segments": segments}

def estimate_virality(transcript: str) -> float:
    # contoh scoring buatan: panjang kata mod 100 + noise
    words = re.findall(r"\w+", transcript)
    base = (len(words) % 100)
    score = max(min(base + random.uniform(-10,10), 100), 0)
    return round(score, 1)
