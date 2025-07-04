# file: utils.py
import os
import tempfile
import re
import whisper
import warnings

# Muat model Whisper lokal sekali saja
def load_whisper_model():
    try:
        return whisper.load_model("base")
    except Exception as e:
        warnings.warn(f"Gagal muat Whisper model: {e}")
        return None

_whisper_model = load_whisper_model()

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Transkripsi audio dari video menggunakan Whisper lokal.
    Kembalikan dict dengan 'text' dan 'segments'.
    """
    if _whisper_model is None:
        raise RuntimeError("Model Whisper lokal tidak tersedia.")

    # Ekstraksi audio ke file WAV sementara
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio.close()
    os.system(f"ffmpeg -y -i \"{video_path}\" -ar 16000 -ac 1 -vn \"{temp_audio.name}\"")

    # Transkripsi
    result = _whisper_model.transcribe(temp_audio.name)
    text = result.get("text", "")
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })
    return {"text": text, "segments": segments}

# Dummy untuk skor viral
import random
def estimate_virality(transcript: str) -> float:
    """
    Perkirakan viralitas konten secara acak sebagai fallback.
    """
    # scoring sederhana: panjang transcript mod 100
    base = len(transcript) % 100
    # tambahkan sedikit random
    return float(min(max(base + random.uniform(-10,10), 0), 100))
