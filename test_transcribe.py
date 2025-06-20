# test_transcribe.py
from app.clip_selector import select_clips

if __name__ == "__main__":
    # Ganti keywords sesuai hasil debug sebelumnya
    clips = select_clips(
        "data/sample.mp4",
        ["uang", "investasi", "kerja"], 
        clip_duration=30
    )
    print("Generated clips:", clips)
