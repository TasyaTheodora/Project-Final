import whisper

def transcribe_video(video_path: str) -> str:
    print("⏳  Mulai transkripsi…")  # tanda proses mulai
    model = whisper.load_model("base")
    result = model.transcribe(video_path, verbose=False)
    print("✅  Transkripsi selesai!")  # tanda proses selesai
    return result["text"]

