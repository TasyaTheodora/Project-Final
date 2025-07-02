# File: app/ui.py
import streamlit as st
import tempfile

# import MoviePy
from moviepy.editor import VideoFileClip

# import helper functions
from app.utils import transcribe_video, estimate_virality

st.set_page_config(
    page_title="Video Trimmer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Video Editor", "Tentang"])

if menu == "Home":
    st.title("🚀 Selamat Datang")
    st.write("Gunakan menu **Video Editor** untuk memotong video Anda.")

elif menu == "Video Editor":
    st.title("✂️ Video Trimmer")
    st.write("Unggah video Anda, atur titik potongnya, dan lihat skor viralitas!")

    uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi"])
    if uploaded:
        # simpan sementara
        suffix = os.path.splitext(uploaded.name)[1]
        tmp_video = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_video.write(uploaded.read())
        tmp_video.flush()

        # preview asli
        st.subheader("Preview Video Asli")
        st.video(tmp_video.name)

        # transkrip & skor viral
        with st.spinner("📝 Transkrip video…"):
            transcript = transcribe_video(tmp_video.name)
        with st.spinner("⭐️ Menghitung viralitas…"):
            score = estimate_virality(transcript)
        st.success(f"🎯 Skor Viralitas: **{score:.1f}** / 100")

        # slider potong
        clip = VideoFileClip(tmp_video.name)
        dur = clip.duration
        st.subheader("Atur Waktu Potong")
        start = st.slider("Mulai (detik)", 0.0, dur, 0.0, 0.1)
        end   = st.slider("Selesai (detik)", 0.0, dur, dur, 0.1)

        if st.button("▶️ Potong & Download"):
            if end <= start:
                st.error("⛔️ Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                with st.spinner("Memproses…"):
                    sub = clip.subclip(start, end)
                    out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                    sub.write_videofile(out, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                st.success("✅ Selesai memotong.")
                st.subheader("Preview Potongan")
                st.video(out)
                st.download_button(
                    "💾 Download Clip",
                    data=open(out, "rb").read(),
                    file_name=f"clip_{int(start)}-{int(end)}.mp4",
                    mime="video/mp4"
                )
        clip.close()

else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write("""
        Aplikasi ini dibuat untuk memotong video secara cepat langsung di browser,
        plus memberikan skor viralitas menggunakan OpenAI.

        **Penulis:** Anastasia Theodora
        **Versi:** 1.1  
    """)
