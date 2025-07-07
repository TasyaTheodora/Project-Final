# file: ui.py
import os

# 1) Pastikan MoviePy tahu di mana ffmpeg.exe
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.abspath(
    "ffmpeg/ffmpeg-2025-06-28-git-cfd1f81e7d-full_build/bin/ffmpeg.exe"
)

import tempfile
import streamlit as st
from moviepy.editor import VideoFileClip
from utils import transcribe_video, estimate_virality

# ─── CONFIG HALAMAN ───
st.set_page_config(page_title="Video Trimmer", layout="wide")
st.title("✂️ Video Trimmer")
st.write("Unggah video, atur start & durasi, lalu potong dan transkrip klip-nya.")

# ─── UPLOADER ───
uploaded = st.file_uploader("Pilih file video:", type=["mp4","mov","avi"])
if not uploaded:
    st.stop()

# simpan ke temp
suffix = os.path.splitext(uploaded.name)[1]
tfile = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
tfile.write(uploaded.getbuffer())
tfile.flush()

# tampilkan
st.video(tfile.name)

# ─── ATUR KLIP ───
st.markdown("### Atur Klip")
start_time = st.number_input("Mulai (detik):", min_value=0.0, value=0.0, step=0.5)
clip_duration = st.slider("Durasi klip (detik):", 1, int(VideoFileClip(tfile.name).duration), 30)

if st.button("Potong Video ✂️"):
    try:
        # potong
        clip = VideoFileClip(tfile.name).subclip(start_time, start_time + clip_duration)
        out_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        clip.write_videofile(out_tmp.name, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clip.close()

        st.success(f"Klip: {start_time:.1f}s → {start_time+clip_duration:.1f}s")
        st.video(out_tmp.name)

        # download
        st.download_button(
            "⬇️ Unduh Klip",
            data=open(out_tmp.name,"rb").read(),
            file_name=f"clip_{start_time:.1f}-{start_time+clip_duration:.1f}.mp4",
            mime="video/mp4"
        )

        # transkripsi & viral score
        with st.spinner("Mentranskrip klip..."):
            d = transcribe_video(out_tmp.name)
        st.markdown("#### Transcript")
        st.write(d["text"])

        score = estimate_virality(d["text"])
        st.markdown(f"#### Viral Score: **{score}/100**")

    except Exception as e:
        st.error(f"Gagal memproses klip: {e}")
