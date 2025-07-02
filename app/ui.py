# file: app/ui.py
import streamlit as st
import tempfile
import random
from moviepy.editor import VideoFileClip

# —————— CONFIG HALAMAN ——————
st.set_page_config(
    page_title="Video Trimmer & Viral Score",
    layout="wide",
    initial_sidebar_state="expanded",
)

# —————— FUNCTION VIRAL SCORE ——————
def compute_viral_score(video_path: str) -> int:
    """
    Stub fungsi untuk menghitung tingkat keviralan video.
    Saat ini menghasilkan skor acak 0-100.
    """
    return random.randint(0, 100)

# —————— SIDEBAR NAVIGASI ——————
st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Video Editor", "Tentang"])

# —————— HALAMAN HOME ——————
if menu == "Home":
    st.title("🚀 Selamat Datang")
    st.write("Gunakan menu **Video Editor** untuk memotong video dan melihat skor keviralan.")

# —————— HALAMAN VIDEO EDITOR ——————
elif menu == "Video Editor":
    st.title("✂️ Video Trimmer & Viral Score")
    st.write("Unggah video Anda, atur titik potong, dan dapatkan perkiraan skor keviralan.")

    uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi"])
    if uploaded:
        # simpan sementara agar moviepy bisa membacanya
        suffix = uploaded.name.split('.')[-1]
        tfile = tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False)
        tfile.write(uploaded.read())
        tfile.flush()

        # load video
        clip = VideoFileClip(tfile.name)
        duration = clip.duration  # detik (float)

        st.subheader("Preview Video Asli")
        st.video(tfile.name)

        # slider untuk start/end
        st.subheader("Atur Waktu Potong")
        start = st.slider("Mulai (detik)", min_value=0.0, max_value=duration, value=0.0, step=0.1)
        end   = st.slider("Selesai (detik)", min_value=0.0, max_value=duration, value=duration, step=0.1)

        if st.button("▶️ Potong Video"):
            if end <= start:
                st.error("Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                with st.spinner("Memproses potongan…"):
                    subclip = clip.subclip(start, end)
                    out_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                    out_path = out_file.name
                    # tulis file potongan
                    subclip.write_videofile(
                        out_path,
                        codec="libx264",
                        audio_codec="aac",
                        verbose=False,
                        logger=None
                    )
                st.success("Selesai memotong!")

                # Hitung viral score
                score = compute_viral_score(out_path)
                st.metric(label="Tingkat Keviralan (0-100)", value=f"{score}")

                st.subheader("Preview Hasil Potongan")
                st.video(out_path)

                # Tombol download
                with open(out_path, "rb") as f:
                    video_bytes = f.read()
                st.download_button(
                    label="⬇️ Download Video Potongan",
                    data=video_bytes,
                    file_name="clip_potongan.mp4",
                    mime="video/mp4"
                )

# —————— HALAMAN TENTANG ——————
else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write("""
        Aplikasi ini dibuat untuk memotong video secara cepat langsung di browser menggunakan MoviePy & Streamlit, dilengkapi estimasi skor keviralan.
        
        **Penulis:** Anastasia Theodora
        **GitHub:** [github.com/TasyaTheodora]
        **Versi:** 1.1  
    """)
