# test_transcribe.py
from app.utils import transcribe_video

if __name__ == "__main__":
    print("=== TRANSCRIPT OUTPUT ===")
    text = transcribe_video("data/sample.mp4")
    print(text)
