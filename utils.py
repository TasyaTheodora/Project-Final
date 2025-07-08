import os
import re
import warnings
import random
import whisper
import uuid
import subprocess # Menggunakan library yang lebih modern
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mendefinisikan path FFMPEG dan folder sementara di satu tempat
FFMPEG_EXE = os.path.abspath("ffmpeg/ffmpeg-2025-06-28-git-cfd1f81e7d-full_build/bin/ffmpeg.exe")
TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# Pastikan environment variable diset untuk moviepy juga
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_EXE

def load_whisper_model():
    """Memuat model Whisper dengan penanganan error."""
    try:
        # Anda bisa ganti "base" dengan "tiny" untuk lebih cepat, atau "small" untuk lebih akurat
        return whisper.load_model("base")
    except Exception as e:
        warnings.warn(f"Gagal memuat model Whisper: {e}")
        return None

_whisper_model = load_whisper_model()

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Mengekstrak audio dari video, mentranskripsikannya, dan membersihkan file sementara.
    Menggunakan metode yang lebih tangguh untuk menangani file.
    """
    if _whisper_model is None:
        raise RuntimeError("Model Whisper tidak tersedia atau gagal dimuat.")

    # Buat path untuk file .wav sementara di folder lokal kita
    temp_wav_path = os.path.join(TEMP_DIR, f"audio_{uuid.uuid4()}.wav")
    
    try:
        logging.info(f"Mengekstrak audio dari '{video_path}' ke '{temp_wav_path}'")
        
        # Command untuk ffmpeg dalam bentuk list (lebih aman)
        command = [
            FFMPEG_EXE,
            '-y',  # Timpa file output jika sudah ada
            '-i', video_path,
            '-ar', '16000',  # Sample rate yang dibutuhkan Whisper
            '-ac', '1',      # Audio mono
            '-vn',           # Abaikan video
            temp_wav_path
        ]
        
        # Jalankan command dengan subprocess untuk kontrol penuh
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Periksa jika ffmpeg menghasilkan error
        if result.returncode != 0:
            error_message = f"FFMPEG gagal mengekstrak audio.\nError: {result.stderr}"
            logging.error(error_message)
            raise RuntimeError(error_message)

        # Periksa apakah file audio benar-benar dibuat
        if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
            raise RuntimeError(f"Ekstraksi audio sepertinya berhasil, tapi file '{temp_wav_path}' kosong.")

        logging.info("Audio berhasil diekstrak. Memulai transkripsi...")
        
        # Transkripsi file audio yang sudah valid
        transcription = _whisper_model.transcribe(temp_wav_path, verbose=verbose)
        logging.info("Transkripsi selesai.")

        text = transcription.get("text", "").strip()
        segments = [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in transcription.get("segments", [])
        ]
        return {"text": text, "segments": segments}

    finally:
        # Selalu pastikan file .wav sementara dihapus setelah selesai
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            logging.info(f"File audio sementara '{temp_wav_path}' dihapus.")


def estimate_virality(transcript: str) -> float:
    """Memperkirakan skor viralitas berdasarkan transkrip."""
    if not transcript:
        return 0.0
    # contoh scoring buatan: panjang kata mod 100 + noise
    words = re.findall(r"\w+", transcript)
    base = (len(words) % 100)
    score = max(min(base + random.uniform(-10,10), 100), 0)
    return round(score, 1)

