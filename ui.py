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
st.write("Unggah video Anda, lalu atur titik potongnya, lihat skor viral, dan unduh klipnya.")

uploaded = st.file_uploader(
    "Pilih file video:", type=["mp4", "mov", "avi", "mpeg4"], accept_multiple_files=False
)

if uploaded:
    # Simpan file ke temp
    suffix = os.path.splitext(uploaded.name)[1]
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tfile.write(uploaded.read())
    tfile.flush()

    # Preview asli
    st.subheader("▶️ Preview Video Asli")
    st.video(tfile.name)

    # Transkrip dan dapatkan segments
    with st.spinner("Mentranskrip video..."):
        result = transcribe_video(tfile.name, verbose=False)
    segments = result.get("segments", [])

    if segments:
        # Tampilkan tabel segmen
        st.subheader("📄 Segmen Transkrip")
        df = pd.DataFrame([
            {"Index": i, "Start": seg["start"], "Text": seg["text"]}
            for i, seg in enumerate(segments)
        ])
        st.dataframe(df, use_container_width=True)

        # Pilih segmen untuk klip
        choice = st.selectbox("Pilih segmen yang ingin dipotong:", df["Index"])
        start = float(df.loc[df.Index == choice, "Start"].values[0])
    else:
        st.warning("Tidak ada segmen transkrip; gunakan slider manual.")
        start = 0.0

    # Atur durasi klip
    duration = st.slider("Durasi klip (detik)", min_value=1, max_value=60, value=30)
    end = start + duration

    # Tombol potong
    if st.button("Potong Video ✂️"):
        with st.spinner("Memotong dan memproses klip..."):
            clip = VideoFileClip(tfile.name)
            sub = clip.subclip(start, end)
            # simpan klip ke temp
            ofile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            sub.write_videofile(ofile, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        # Preview klip
        st.subheader("▶️ Preview Klip")
        st.video(ofile)

        # Download button
        with open(ofile, "rb") as f:
            data = f.read()
        st.download_button(
            "⬇️ Unduh Klip", data=data, file_name="clip_potongan.mp4", mime="video/mp4"
        )

        # Tampilkan skor viral
        transcript = result.get("text", "")
        score = estimate_virality(transcript)
        st.metric(label="🔥 Skor Viral", value=f"{score:.1f}/100")
else:
    st.info("Silakan unggah video untuk memulai.")

# ------ HALAMAN TENTANG ------

with st.expander("ℹ️ Tentang Aplikasi"):
    st.write(
        "Aplikasi ini dibuat untuk memotong video secara cepat langsung di browser menggunakan MoviePy & Streamlit."
    )
    st.write("**Penulis:** Anastasia Theodora")
    st.write("**Versi:** 1.1")

