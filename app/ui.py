
import streamlit as st
import tempfile
from moviepy.video.io.VideoFileClip import VideoFileClip
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
        # simpan sementara agar moviepy bisa membacanya
        tfile = tempfile.NamedTemporaryFile(suffix="." + uploaded.type.split("/")[-1], delete=False)
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
                    out_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                    # tulis file potongan
                    subclip.write_videofile(
                        out_path,
                        codec="libx264",
                        audio_codec="aac",
                        verbose=False,
                        logger=None
                    )
                st.success("Selesai memotong!")
                st.subheader("Hasil Potongan")
                st.video(out_path)

# —————— HALAMAN TENTANG ——————
else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write("""
        Aplikasi ini dibuat untuk memotong video secara cepat langsung di browser menggunakan MoviePy & Streamlit.
        
        **Penulis:** Nama Anda  
        **Versi:** 1.0  
    """)

