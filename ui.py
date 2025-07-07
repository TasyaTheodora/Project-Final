# file: ui.py

import os
import tempfile

import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality

# ───── CONFIG HALAMAN ─────
st.set_page_config(
    page_title="Video Trimmer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("✂️ Video Trimmer")
st.write("Unggah video Anda, lalu tentukan kapan dan berapa detik klip yang ingin dipotong.")

uploaded = st.file_uploader(
    "Pilih file video:",
    type=["mp4", "mov", "avi", "mpeg4"],
    accept_multiple_files=False,
)

if not uploaded:
    st.stop()

# simpan upload ke tmp
tfile = tempfile.NamedTemporaryFile(suffix=os.path.splitext(uploaded.name)[1], delete=False)
tfile.write(uploaded.getbuffer())
tfile.flush()

# tampilkan full video dulu
st.video(tfile.name)

# ───── INPUT POTONG ─────
st.markdown("### Atur Klip")
start_time = st.number_input("Mulai (detik):", min_value=0.0, max_value=3000.0, value=0.0, step=0.5)
clip_duration = st.slider("Durasi klip (detik):", 1, 300, 30)

if st.button("Potong Video ✂️"):
    try:
        # potong
        clip = VideoFileClip(tfile.name).subclip(start_time, start_time + clip_duration)
        out_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        clip.write_videofile(out_tmp.name, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clip.close()

        st.success(f"Klip berhasil dibuat: {start_time:.1f} → {start_time+clip_duration:.1f} detik")
        st.video(out_tmp.name)

        st.download_button(
            "⬇️ Unduh Klip",
            data=open(out_tmp.name, "rb").read(),
            file_name=f"clip_{start_time:.1f}_{start_time+clip_duration:.1f}.mp4",
            mime="video/mp4",
        )

        # transcribe & viral score
        with st.spinner("Mentranskrip klip..."):
            data = transcribe_video(out_tmp.name, verbose=False)
        transcript = data["text"]
        st.markdown("#### Transcript klip:")
        st.write(transcript)

        score = estimate_virality(transcript)
        st.markdown(f"#### Viral Score: **{score:.1f}/100**")

    except Exception as e:
        st.error(f"Gagal memproses klip: {e}")
