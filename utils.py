## utils.py
import os
import tempfile
import re
import whisper
import warnings
import random

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
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        "-vn",
        temp_file.name
    ]
    os.system(" ".join(cmd))

    # Transkripsi
    result = _whisper_model.transcribe(temp_file.name, verbose=verbose)
    text = result.get("text", "")
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })

    try:
        os.remove(temp_file.name)
    except OSError:
        pass

    return {"text": text, "segments": segments}


def estimate_virality(transcript: str) -> float:
    """
    Perkirakan viralitas konten berdasarkan panjang teks.
    Skor 0-100.
    """
    # scoring sederhana: (jumlah kata / 10) + faktor random kecil
    words = re.findall(r"\w+", transcript)
    base_score = min(len(words) / 10 * 5, 100)
    noise = random.uniform(-5, 5)
    score = max(min(base_score + noise, 100), 0)
    return round(score, 1)
