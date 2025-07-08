import os
import tempfile
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality
import uuid # Untuk membuat nama file unik

# ─── SETUP ───
st.set_page_config(page_title="Video Trimmer AI", layout="wide")
st.title("✂️ AI Video Trimmer & Scorer")
st.write("Unggah video, potong bagian terbaik, lalu dapatkan transkrip dan skor viralitasnya.")

# Buat folder sementara jika belum ada
TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── PATH FFMPEG (PENTING) ───
try:
    ffmpeg_path = os.path.abspath("ffmpeg/ffmpeg-2025-06-28-git-cfd1f81e7d-full_build/bin/ffmpeg.exe")
    if not os.path.exists(ffmpeg_path):
        st.error(f"FFMPEG tidak ditemukan di path: {ffmpeg_path}. Pastikan path sudah benar.")
        st.stop()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
except Exception as e:
    st.error(f"Terjadi masalah saat mengatur path FFMPEG: {e}")
    st.info("Pastikan Anda sudah mengunduh FFMPEG dan meletakkannya di folder yang benar.")
    st.stop()

# ─── UPLOADER ───
uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi", "mkv"])

if not uploaded:
    st.info("Silakan unggah file video untuk memulai.")
    st.stop()

# --- STRATEGI FILE BARU ---
# Buat path file yang unik di dalam folder sementara kita
suffix = os.path.splitext(uploaded.name)[1]
temp_video_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{suffix}")
output_clip_path = None # Inisialisasi variabel path klip output

try:
    # Tulis file yang diunggah ke path baru kita
    with open(temp_video_path, "wb") as f:
        f.write(uploaded.getbuffer())

    # Tampilkan video player dari path yang stabil
    st.video(temp_video_path)

    # ─── ATUR KLIP ───
    st.markdown("---")
    st.markdown("### Atur Klip")

    # Dapatkan durasi video dari path yang stabil
    with VideoFileClip(temp_video_path) as video:
        duration = video.duration

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.number_input("Mulai dari (detik):", min_value=0.0, max_value=duration, value=0.0, step=0.5)
    with col2:
        max_clip_duration = duration - start_time
        default_duration = min(30.0, max_clip_duration)
        clip_duration = st.slider("Durasi klip (detik):", 
                                  min_value=1.0, 
                                  max_value=max_clip_duration, 
                                  value=default_duration,
                                  step=1.0)

    end_time = start_time + clip_duration
    st.info(f"Klip akan dipotong dari **{start_time:.1f} detik** hingga **{end_time:.1f} detik**.")

    if st.button("🚀 Potong, Transkrip, dan Analisa!", type="primary"):
        with st.spinner("Memotong video..."):
            # Path untuk klip yang sudah dipotong
            output_clip_path = os.path.join(TEMP_DIR, f"clip_{uuid.uuid4()}.mp4")
            
            with VideoFileClip(temp_video_path) as video:
                clip = video.subclip(start_time, end_time)
                clip.write_videofile(output_clip_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.success(f"✅ Klip berhasil dibuat: {start_time:.1f}s → {end_time:.1f}s")
        
        # Tampilkan hasil klip dan tombol download
        st.video(output_clip_path)
        with open(output_clip_path, "rb") as f:
            st.download_button(
                "⬇️ Unduh Klip",
                data=f.read(),
                file_name=f"clip_{start_time:.1f}s-{end_time:.1f}s_{uploaded.name}",
                mime="video/mp4"
            )

        # Transkripsi & Viral Score
        with st.spinner("Mentranskrip audio dari klip..."):
            try:
                transcription_data = transcribe_video(output_clip_path)
                transcript_text = transcription_data["text"]
            except Exception as e:
                st.error(f"Gagal mentranskrip video: {e}")
                transcript_text = ""

        if transcript_text:
            st.markdown("---")
            st.markdown("#### 📝 Transkrip Klip")
            st.markdown(f"> _{transcript_text}_")

            score = estimate_virality(transcript_text)
            st.markdown(f"#### 📈 Prediksi Skor Viralitas")
            st.progress(int(score), text=f"**{score}/100**")

except Exception as e:
    st.error(f"Gagal memproses video. File mungkin rusak atau format tidak didukung. Error: {e}")

finally:
    # Pastikan semua file sementara dihapus
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)
    if output_clip_path and os.path.exists(output_clip_path):
        os.remove(output_clip_path)
