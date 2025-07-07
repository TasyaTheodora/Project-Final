# file: utils.py

import os
import tempfile
import subprocess
import whisper

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Mengekstrak audio dari video, lalu mentranskripsinya dengan Whisper.
    """
    # buat temp file untuk wav
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    # panggil ffmpeg untuk extract audio 16kHz mono
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ac", "1",        # mono
        "-ar", "16000",    # 16 kHz
        "-vn",             # no video
        "-y",              # overwrite
        audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # load model Whisper
    model = whisper.load_model("base")
    # transcribe
    result = model.transcribe(audio_path, verbose=verbose)

    # bersihkan file sementara
    try:
        os.remove(audio_path)
    except OSError:
        pass

    return result
