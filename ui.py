import os
import streamlit as st
# Menggunakan path import yang paling umum dan stabil
from moviepy.editor import VideoFileClip
from utils import transcribe_video, estimate_virality
import uuid
import logging

# Setup logging untuk melihat info lebih detail jika ada masalah
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        st.error(f"FFMPEG tidak ditemukan di path: {ffmpeg_path}. Pastikan struktur folder sudah benar.")
        st.stop()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
except Exception as e:
    st.error(f"Terjadi masalah saat mengatur path FFMPEG: {e}")
    st.stop()

# ─── UPLOADER & STATE MANAGEMENT ───
# Gunakan st.session_state untuk menyimpan path file antar rerun
if 'temp_video_path' not in st.session_state:
    st.session_state.temp_video_path = None
if 'output_clip_path' not in st.session_state:
    st.session_state.output_clip_path = None

uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi", "mkv"])

if uploaded:
    # Simpan file yang diunggah ke path sementara HANYA JIKA file baru diunggah
    suffix = os.path.splitext(uploaded.name)[1]
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{suffix}")
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.session_state.temp_video_path = temp_path
    # Reset path klip output lama jika ada video baru
    st.session_state.output_clip_path = None

# Jangan lanjutkan jika tidak ada video yang valid di state
if not st.session_state.temp_video_path or not os.path.exists(st.session_state.temp_video_path):
    st.info("Silakan unggah file video untuk memulai.")
    st.stop()

# --- Tampilkan video dari path yang disimpan di session state ---
st.video(st.session_state.temp_video_path)

# ─── ATUR KLIP ───
try:
    # Dapatkan durasi dengan membuka klip sementara
    with VideoFileClip(st.session_state.temp_video_path) as video:
        duration = video.duration
    
    st.markdown("---")
    st.markdown("### Atur Klip")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.number_input("Mulai dari (detik):", min_value=0.0, max_value=duration, value=0.0, step=0.5)
    with col2:
        max_clip_duration = duration - start_time
        default_duration = min(30.0, max_clip_duration)
        clip_duration = st.slider("Durasi klip (detik):", 
                                  min_value=1.0, 
                                  max_value=max_clip_duration if max_clip_duration > 1.0 else 1.0, 
                                  value=default_duration,
                                  step=1.0)

    end_time = start_time + clip_duration
    st.info(f"Klip akan dipotong dari **{start_time:.1f} detik** hingga **{end_time:.1f} detik**.")

    if st.button("🚀 Potong, Transkrip, dan Analisa!", type="primary"):
        with st.spinner("Memotong video..."):
            # --- SOLUSI INTI ---
            # Muat ulang klip dari file TEPAT sebelum memotong
            # Gunakan 'with' untuk memastikan file tertutup dengan benar
            try:
                with VideoFileClip(st.session_state.temp_video_path) as video_to_clip:
                    logging.info(f"Memulai subclip dari {start_time} hingga {end_time}")
                    sub_clip = video_to_clip.subclip(start_time, end_time)
                    
                    # Simpan klip yang sudah dipotong
                    output_path = os.path.join(TEMP_DIR, f"clip_{uuid.uuid4()}.mp4")
                    sub_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                    st.session_state.output_clip_path = output_path
                    logging.info(f"Klip berhasil ditulis ke: {output_path}")

            except Exception as e:
                st.error(f"Gagal saat memotong klip: {e}")
                logging.error("Error dalam proses subclip/write:", exc_info=True)
                st.stop()

except Exception as e:
    st.error(f"Gagal membaca video. File mungkin rusak. Error: {e}")
    logging.error("Error saat membaca durasi video:", exc_info=True)
    st.stop()


# --- Tampilkan hasil HANYA JIKA klip sudah dibuat ---
if st.session_state.output_clip_path and os.path.exists(st.session_state.output_clip_path):
    st.success(f"✅ Klip berhasil dibuat!")
    
    st.video(st.session_state.output_clip_path)
    with open(st.session_state.output_clip_path, "rb") as f:
        st.download_button(
            "⬇️ Unduh Klip",
            data=f.read(),
            file_name=f"clip_{os.path.basename(st.session_state.temp_video_path)}",
            mime="video/mp4"
        )

    with st.spinner("Mentranskrip audio dari klip..."):
        try:
            transcript_data = transcribe_video(st.session_state.output_clip_path)
            transcript_text = transcript_data.get("text", "")
            
            if transcript_text:
                st.markdown("---")
                st.markdown("#### 📝 Transkrip Klip")
                st.markdown(f"> _{transcript_text}_")

                score = estimate_virality(transcript_text)
                st.markdown(f"#### 📈 Prediksi Skor Viralitas")
                st.progress(int(score), text=f"**{score}/100**")
            else:
                st.warning("Tidak ada teks yang terdeteksi dalam klip.")

        except Exception as e:
            st.error(f"Gagal mentranskrip klip: {e}")
            logging.error("Error saat transkripsi:", exc_info=True)

# Catatan: Pembersihan file sementara bisa dilakukan di sini atau secara periodik.
# Untuk aplikasi yang berjalan terus menerus, diperlukan strategi pembersihan yang lebih canggih.
# Untuk sesi pengguna tunggal, file akan ada di folder 'temp_videos' hingga aplikasi dihentikan.
