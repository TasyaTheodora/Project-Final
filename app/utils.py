import whisper

def transcribe_video(video_path: str) -> str:
    """
    Mengubah video menjadi transcript teks.
    """
    # Muat model Whisper (base)
    model = whisper.load_model("base")
    # Jalankan transkripsi
    result = model.transcribe(video_path)
    # Kembalikan teks transkrip
    return result["text"]
