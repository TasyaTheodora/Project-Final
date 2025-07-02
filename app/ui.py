# file: app/ui.py
import os
import streamlit as st
import tempfile

# import fungsi transkripsi dan virality
from .utils import transcribe_video, estimate_virality

# import moviepy, sesuaikan path
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip


# ----- CONFIG HALAMAN -----
st.set_page_config(
    page_title="Video Trimmer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----- SIDEBAR NAVIGASI -----
st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Video Editor", "Tentang"])

# ----- HALAMAN HOME -----
if menu == "Home":
    st.title("🚀 Selamat Datang")
    st.write("Gunakan menu **Video Editor** untuk memotong video Anda dan mengecek potensi viral-nya.")

# ----- HALAMAN VIDEO EDITOR -----
elif menu == "Video Editor":
    st.title("✂️ Video Trimmer & Virality Checker")
    uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi"])

    if uploaded:
        # simpan sementara agar moviepy bisa membacanya
        ext = os.path.splitext(uploaded.name)[1]
        tfile = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tfile.write(uploaded.read())
        tfile.flush()

        # load video
        clip = VideoFileClip(tfile.name)
        duration = clip.duration

        # Tampilkan preview asli
        st.subheader("Preview Video Asli")
        st.video(tfile.name)

        # Slider potong
        st.subheader("Atur Waktu Potong")
        start = st.slider("Mulai (detik)", 0.0, duration, 0.0, 0.1)
        end   = st.slider("Selesai (detik)", 0.0, duration, duration, 0.1)

        if st.button("▶️ Potong & Cek Viral"):
            if end <= start:
                st.error("Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                with st.spinner("Memproses potongan…"):
                    subclip = clip.subclip(start, end)
                    out_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                    subclip.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                # transkripsi & virality
                st.subheader("Transkrip & Viral Score")
                result = transcribe_video(out_path, verbose=False)
                transcript = "\n".join([seg["text"] for seg in result.get("segments", [])])
                score = estimate_virality(transcript)
                st.metric(label="Viral Score", value=f"{score:.1f}/100")

                # tampilkan klip & download
                st.subheader("Hasil Potongan")
                st.video(out_path)
                with open(out_path, "rb") as f:
                    data = f.read()
                st.download_button(
                    label="⬇️ Download Klip",
                    data=data,
                    file_name="clip_potongan.mp4",
                    mime="video/mp4"
                )

# ----- HALAMAN TENTANG -----
else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write("""
    Aplikasi ini memotong video langsung di browser, lalu menganalisis potensi viral-nya menggunakan AI.

    **Penulis:** Nama Anda  
    **Versi:** 1.1
    """)
