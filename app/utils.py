import whisper

def transcribe_video(video_path: str, verbose: bool = True) -> dict:
    """
    Mengubah video menjadi hasil transkripsi Whisper.
    - video_path: path ke file video
    - verbose: False untuk sembunyikan progress bar
    Returns: dict hasil transkripsi lengkap dengan segments.
    """
    model = whisper.load_model("base")
    # pass verbose flag into Whisper
    result = model.transcribe(video_path, verbose=verbose)
    return result
