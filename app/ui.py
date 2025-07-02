import os
import streamlit as st
import tempfile

# import fungsi transkripsi & virality dari utils
from app.utils import transcribe_video, estimate_virality

# import MoviePy
from moviepy.editor import VideoFileClip


# —————— CONFIG HALAMAN ——————
st.set_page_config(
    page_title="Video Trimmer & Viral Score",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Video Editor", "Tentang"])

if menu == "Home":
    st.title("🚀 Selamat Datang")
    st.write("Gunakan menu **Video Editor** untuk memotong video Anda dan mendapatkan viral-score.")

elif menu == "Video Editor":
    st.title("✂️ Video Trimmer & Viral Score")
    st.write("Unggah video Anda, lalu potong, preview, download, dan lihat prediksi viral-score.")

    uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi"])
    if uploaded:
        # simpan sementara agar bisa dioper ke ffmpeg & Whisper
        suffix = os.path.splitext(uploaded.name)[1]
        t_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        t_in.write(uploaded.read())
        t_in.flush()

        # tampilkan preview asli
        st.subheader("▶️ Preview Video Asli")
        st.video(t_in.name)

        # slider waktu potong
        duration_cmd = [
            ffmpeg.get_ffmpeg_exe(),
            "-i", t_in.name,
            "-hide_banner", "-loglevel", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1"
        ]
        # dapatkan durasi via ffprobe
        try:
            dur = float(subprocess.check_output(
                [ffmpeg.get_ffmpeg_exe().replace("ffmpeg","ffprobe"), 
                 "-i", t_in.name,
                 "-hide_banner", "-loglevel", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1"]
            ).strip())
        except Exception:
            dur = 0.0

        st.subheader("⏱️ Atur Waktu Potong")
        start = st.slider("Mulai (detik)", 0.0, dur, 0.0, 0.1)
        end   = st.slider("Selesai (detik)", 0.0, dur, dur, 0.1)

        if st.button("▶️ Potong, Transkrip & Hitung Viral-Score"):
            if end <= start:
                st.error("Waktu selesai harus lebih besar dari waktu mulai.")
            else:
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                cmd = [
                    ffmpeg.get_ffmpeg_exe(),
                    "-i", t_in.name,
                    "-ss", str(start),
                    "-to", str(end),
                    "-c", "copy",
                    out
                ]
                with st.spinner("Memproses potongan…"):
                    subprocess.run(cmd, check=True)

                st.success("✔️ Selesai memotong!")
                st.subheader("▶️ Preview Hasil Potongan")
                st.video(out)

                # transkripsi & viral-score
                with st.spinner("🔊 Transkripsi audio…"):
                    transcript = transcribe_video(out)
                st.subheader("📝 Transkrip")
                st.write(transcript)

                with st.spinner("📈 Menghitung viral-score…"):
                    score = estimate_virality(transcript)
                st.subheader("🔥 Viral-Score")
                st.metric(label="Prediksi Viral-Score (0–100)", value=f"{score:.1f}")

                st.download_button(
                    label="⬇️ Download Clip",
                    data=open(out, "rb").read(),
                    file_name="clip.mp4",
                    mime="video/mp4"
                )

else:
    st.title("ℹ️ Tentang Aplikasi")
    st.write("""
    Aplikasi ini memotong video langsung di browser menggunakan FFmpeg,  
    lalu mentranskrip audio & memberi prediksi seberapa viral konten Anda.
    
    **Penulis:** Nama Anda  
    **Versi:** 1.0  
    """)

