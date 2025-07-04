# file: ui.py
import os
import tempfile
import streamlit as st
import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality

# ------ CONFIG HALAMAN ------
st.set_page_config(
    page_title="Video Trimmer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("✂️ Video Trimmer")
st.write("Unggah video Anda, kemudian pilih segmen, lihat skor viral, dan unduh klipnya.")

# Upload video
uploaded = st.file_uploader(
    "Pilih file video:", type=["mp4", "mov", "avi", "mpeg4"]
)

if uploaded:
    suffix = os.path.splitext(uploaded.name)[1]
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tfile.write(uploaded.read())
    tfile.flush()

    st.subheader("▶️ Preview Video Asli")
    st.video(tfile.name)

    # Transcribe offline dan dapatkan segmen
    with st.spinner("Mentranskrip video secara offline…"):
        result = transcribe_video(tfile.name)
    segments = result.get("segments", [])
    full_text = result.get("text", "")

    if segments:
        st.subheader("📄 Daftar Segmen Transkrip")
        df = pd.DataFrame([
            {"Index": i, "Start (s)": seg["start"], "Teks": seg["text"]}
            for i, seg in enumerate(segments)
        ])
        st.dataframe(df, use_container_width=True)

        choice = st.selectbox("Pilih segmen untuk dipotong:", df["Index"])
        start = float(df.loc[df.Index == choice, "Start (s)"].values[0])
    else:
        st.warning("Transkripsi tidak menghasilkan segmen. Gunakan slider manual.")
        start = 0.0

    duration = st.slider("Durasi klip (detik)", min_value=1, max_value=60, value=30)
    end = start + duration

    if st.button("Potong Video ✂️"):
        with st.spinner("Memproses klip…"):
            clip = VideoFileClip(tfile.name)
            sub = clip.subclip(start, end)
            ofile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            sub.write_videofile(ofile, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.subheader("▶️ Preview Klip")
        st.video(ofile)

        with open(ofile, "rb") as f:
            video_bytes = f.read()
        st.download_button(
            "⬇️ Unduh Klip", video_bytes,
            file_name=f"clip_{int(start)}_{int(end)}.mp4",
            mime="video/mp4"
        )

        # Tampilkan skor viral
        score = estimate_virality(full_text)
        st.metric("🔥 Skor Viral", f"{score:.1f}/100")
else:
    st.info("Unggah video untuk memulai analisis dan pemotongan.")

# ------ TENTANG APLIKASI ------
with st.expander("ℹ️ Tentang Aplikasi"):
    st.write(
        "Aplikasi ini memotong video berbasis transkripsi offline menggunakan Whisper + MoviePy,"
        " dan menilai potensi viralnya dengan algoritma sederhana."
    )
    st.write("**Penulis:** Anastasia Theodora")
    st.write("**Versi:** 1.2")
