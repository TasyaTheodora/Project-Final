import os
import re
import warnings
import random
import whisper
import uuid
import subprocess
import logging
from math import floor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURASI ---
TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# Daftar kata kunci untuk analisis
HOOK_WORDS = ["cara", "rahasia", "terbukti", "jangan", "stop", "ini dia", "ternyata", "begini"]
POWER_WORDS = ["gratis", "diskon", "terbatas", "viral", "kaget", "terungkap", "wajib", "penting"]
POSITIVE_WORDS = ["luar biasa", "terbaik", "cinta", "hebat", "sukses", "solusi", "mudah"]
NEGATIVE_WORDS = ["buruk", "gagal", "kecewa", "masalah", "bahaya", "hindari", "salah"]
# ------------------------------------

def load_whisper_model():
    """Memuat model Whisper dengan penanganan error."""
    try:
        # --- PERUBAHAN KUNCI ---
        # Mengganti "base" dengan "tiny" untuk menghemat memori di server cloud.
        return whisper.load_model("tiny")
    except Exception as e:
        warnings.warn(f"Gagal memuat model Whisper: {e}")
        return None

_whisper_model = load_whisper_model()

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """Mengekstrak audio, mentranskripsi, dan membersihkan file sementara."""
    if _whisper_model is None:
        raise RuntimeError("Model Whisper tidak tersedia atau gagal dimuat.")
    temp_wav_path = os.path.join(TEMP_DIR, f"audio_{uuid.uuid4()}.wav")
    try:
        logging.info(f"Mengekstrak audio dari '{video_path}' ke '{temp_wav_path}'")
        
        command = [
            "ffmpeg",
            '-y',
            '-i', video_path,
            '-ar', '16000',
            '-ac', '1',
            '-vn',
            temp_wav_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            raise RuntimeError(f"FFMPEG gagal mengekstrak audio.\nError: {result.stderr}")
        if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
            raise RuntimeError(f"Ekstraksi audio gagal, file '{temp_wav_path}' kosong.")
        
        transcription = _whisper_model.transcribe(temp_wav_path, verbose=verbose)
        text = transcription.get("text", "").strip()
        segments = transcription.get("segments", [])
        return {"text": text, "segments": segments}
    finally:
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

def estimate_virality(transcription_data: dict) -> dict:
    """
    Menganalisis potensi viral sebuah klip video berdasarkan transkrip.
    """
    text = transcription_data.get("text", "")
    segments = transcription_data.get("segments", [])

    if not text or not segments:
        return {"total_score": 0, "details": {"Kesalahan": "Tidak ada transkrip untuk dianalisis."}}

    word_count = len(re.findall(r'\w+', text))
    duration = segments[-1]['end'] if segments else 0

    # 1. Analisis Hook (5 detik pertama)
    hook_text = " ".join([s['text'] for s in segments if s['start'] < 5])
    hook_score = 0
    hook_reason = "❌ Hook standar atau tidak terdeteksi."
    if "?" in hook_text:
        hook_score = 100
        hook_reason = "✅ Hook kuat! Dimulai dengan pertanyaan."
    else:
        for word in HOOK_WORDS:
            if re.search(rf"\b{word}\b", hook_text, re.IGNORECASE):
                hook_score = 80
                hook_reason = f"✅ Hook baik! Menggunakan kata kunci '{word}'."
                break
    
    # 2. Analisis Kecepatan Bicara (Words Per Minute)
    wpm = (word_count / duration) * 60 if duration > 0 else 0
    wpm_score = 0
    if 140 <= wpm <= 170: wpm_score = 100
    elif 120 <= wpm < 140 or 170 < wpm <= 190: wpm_score = 75
    elif wpm > 190: wpm_score = 60
    else: wpm_score = 40
    wpm_reason = f"⚡ Kecepatan bicara: {floor(wpm)} kata/menit."

    # 3. Analisis Kata Kunci & Sentimen
    power_word_count = sum(1 for word in POWER_WORDS if re.search(rf"\b{word}\b", text, re.IGNORECASE))
    keyword_score = min(power_word_count * 25, 100)
    keyword_reason = f"🔑 Ditemukan {power_word_count} kata kunci kuat."

    positive_count = sum(1 for word in POSITIVE_WORDS if re.search(rf"\b{word}\b", text, re.IGNORECASE))
    negative_count = sum(1 for word in NEGATIVE_WORDS if re.search(rf"\b{word}\b", text, re.IGNORECASE))
    sentiment_score = 50
    sentiment_reason = "😐 Sentimen netral."
    if positive_count > negative_count:
        sentiment_score = 85
        sentiment_reason = "😊 Sentimen cenderung positif."
    elif negative_count > positive_count:
        sentiment_score = 75
        sentiment_reason = "😠 Sentimen cenderung negatif (memicu perdebatan)."

    # 4. Kalkulasi Skor Akhir
    weights = {"hook": 0.40, "keyword": 0.25, "wpm": 0.20, "sentiment": 0.15}
    final_score = (hook_score * weights["hook"] + keyword_score * weights["keyword"] + wpm_score * weights["wpm"] + sentiment_score * weights["sentiment"])

    return {
        "total_score": round(final_score),
        "details": {
            "Hook 5 Detik Pertama": hook_reason,
            "Analisis Kata Kunci": keyword_reason,
            "Tempo & Kecepatan": wpm_reason,
            "Analisis Sentimen": sentiment_reason
        }
    }
