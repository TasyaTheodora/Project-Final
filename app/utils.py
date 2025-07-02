import whisper

# load once at import time for speed
_model = whisper.load_model("base")

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Transcribe a video file locally with Whisper.
    """
    return _model.transcribe(video_path, verbose=verbose)
