
import pandas as pd
import warnings

os.environ["FFMPEG_BINARY"] = r"C:\Users\willi\Projects\video-clip-ai-capstone\ffmpeg\ffmpeg-2025-06-28-git-cfd1f81e7d-full_build\bin\ffmpeg.exe"
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


# ------ TENTANG APLIKASI ------
with st.expander("ℹ️ Tentang Aplikasi"):
    st.write(
        "Aplikasi ini memotong video berbasis transkripsi menggunakan Whisper lokal atau OpenAI API,"
        " dan menilai potensi viralnya dengan algoritma sederhana."
    )
    st.write("**Penulis:** Anastasia Theodora")
    st.write("**Versi:** 1.3")
