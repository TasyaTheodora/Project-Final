# file: app/ui.py
import os
import tempfile
import streamlit as st
from app.utils import transcribe_video, estimate_virality
from moviepy.editor import VideoFileClip
# … (rest of your ui.py seperti patch sebelumnya) …


# —————— CONFIG HALAMAN ——————
st.set_page_config(
    page_title="Video Trimmer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# —————— SIDEBAR NAVIGASI ——————
st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Video Editor", "Tentang"])

# —————— HALAMAN HOME ——————
if menu == "Home":
    st.title("🚀 Selamat Datang")
    st.write("Gunakan menu **Video Editor** untuk memotong video Anda.")

# —————— HALAMAN VIDEO EDITOR ——————
elif menu == "Video Editor":
    st.title("✂️ Video Trimmer")
    st.write("Unggah video Anda, lalu atur titik potongnya.")

    uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi"])
    if uploaded:
        # simpan sementara agar MoviePy bisa membacanya
        suffix = os.path.splitext(uploaded.name)[1]
        tfile = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tfile.write(uploaded.read())
        tfile.flush()

        # transkripsi + beri skor viralitas
        result = transcribe_video(tfile.name)
        transcript = result["text"]
        viral_score = estimate_virality(transcript)
        st.metric("Viral Score", f"{viral_score:.1f}/100")

        # load video
        clip = VideoFileClip(tfile.name)
        duration = clip.duration

        st.subheader("Preview Video Asli")
        st.video(tfile.name)

        st.subheader("Atur Waktu Potong")
        start = st.slider("Mulai (detik)", 0.0, duration, 0.0, 0.1)
        end   = st.slider("Selesai (detik)", 0.0, duration, duration, 0.1)

        if st.button("▶️ Potong Video"):
            if end <= start:
                st.error("Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                with st.spinner("Memproses potongan…"):
                    subclip = clip.subclip(start, end)
                    out_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                    subclip.write_videofile(
                        out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None
                    )
                st.success("Selesai memotong!")
                st.subheader("Hasil Potongan")
                st.video(out_path)
                with open(out_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Potongan",
                        data=f,
                        file_name="potongan.mp4",
                        mime="video/mp4"
                    )

# —————— HALAMAN TENTANG ——————
else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write(
        """
        Aplikasi ini dibuat untuk memotong video secara cepat langsung di browser  
        menggunakan MoviePy & Streamlit.

        **Penulis:** Nama Anda  
        **Versi:** 1.1  
        """
    )
