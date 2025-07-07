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


## ui.py
import os
import tempfile
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality

st.set_page_config(page_title="Video Trimmer", layout="wide")

st.title("✂️ Video Trimmer & Viral Score")

uploaded = st.file_uploader("Unggah video (mp4,mov,avi):", type=["mp4","mov","avi"])
if uploaded:
    # simpan sementara
    ext = os.path.splitext(uploaded.name)[1]
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.write(uploaded.read())
    tmp.flush()
    video_path = tmp.name

    # tampil preview
    st.subheader("Preview Video")
    st.video(video_path)

    # transcribe
    with st.spinner("Menjalankan transkripsi…"):
        data = transcribe_video(video_path)
    st.subheader("Transkrip")
    st.write(data["text"])

    # estimate virality
    score = estimate_virality(data["text"])
    st.metric(label="Viral Score", value=f"{score}/100")

    # potong berdasarkan segmen
    st.subheader("Segments")
    for seg in data["segments"]:
        if st.button(f"Play {seg['start']:.1f}-{seg['end']:.1f} sec:"):
            clip = VideoFileClip(video_path).subclip(seg['start'], seg['end'])
            out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            clip.write_videofile(out, codec="libx264", audio_codec="aac", verbose=False)
            st.video(out)
            st.download_button("Download Clip", data=open(out, "rb"), file_name=f"clip_{int(seg['start'])}_{int(seg['end'])}.mp4")
