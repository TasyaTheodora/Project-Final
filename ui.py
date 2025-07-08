import os
import streamlit as st
from moviepy.editor import VideoFileClip
from utils import transcribe_video, estimate_virality
import uuid
import logging

# Setup logging untuk melihat info lebih detail jika ada masalah
logging.basicConfig(level=logging.INFO)

# ─── SETUP ───
st.set_page_config(page_title="Video Trimmer AI", layout="wide")
st.title("✂️ AI Video Trimmer & Scorer")
st.write("Unggah video, potong bagian terbaik, lalu dapatkan transkrip dan skor viralitasnya.")

# Buat folder sementara jika belum ada
TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── PATH FFMPEG (PENTING) ───
try:
    # Menggunakan path relatif yang lebih sederhana
    ffmpeg_path = os.path.join("ffmpeg", "ffmpeg-2025-06-28-git-cfd1f81e7d-full_build", "bin", "ffmpeg.exe")
    ffmpeg_path = os.path.abspath(ffmpeg_path) # Ubah ke path absolut
    if not os.path.exists(ffmpeg_path):
        st.error(f"FFMPEG tidak ditemukan di path: {ffmpeg_path}. Pastikan struktur folder sudah benar.")
        st.stop()
    # Moviepy tidak lagi memerlukan variabel environment ini secara eksplisit jika ffmpeg ada di PATH sistem,
    # tapi mengaturnya di sini adalah cara yang paling pasti.
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
suffix = os.path.splitext(uploaded.name)[1]
temp_video_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{suffix}")
output_clip_path = None
video_clip_object = None # Inisialisasi variabel untuk objek video

try:
    # Tulis file yang diunggah ke path kita
    with open(temp_video_path, "wb") as f:
        f.write(uploaded.getbuffer())
    logging.info(f"Video diunggah dan disimpan sementara di: {temp_video_path}")

    # Tampilkan video player dari path yang stabil
    st.video(temp_video_path)

    # --- STRATEGI OBJEK VIDEO TUNGGAL ---
    # Muat video ke objek MoviePy HANYA SATU KALI
    try:
        video_clip_object = VideoFileClip(temp_video_path)
        logging.info("Objek VideoFileClip berhasil dibuat.")
    except Exception as e:
        st.error(f"Gagal memuat video dengan MoviePy. Error: {e}")
        st.stop()

    # ─── ATUR KLIP ───
    st.markdown("---")
    st.markdown("### Atur Klip")

    # Dapatkan durasi dari objek yang sudah ada
    duration = video_clip_object.duration

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
            output_clip_path = os.path.join(TEMP_DIR, f"clip_{uuid.uuid4()}.mp4")
            
            # Gunakan objek video yang SUDAH ADA, jangan buat baru
            logging.info(f"Memulai subclip dari {start_time} hingga {end_time}")
            sub_clip = video_clip_object.subclip(start_time, end_time)
            
            logging.info(f"Menulis klip ke: {output_clip_path}")
            sub_clip.write_videofile(output_clip_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            sub_clip.close() # Tutup sub-klip setelah selesai

        st.success(f"✅ Klip berhasil dibuat!")
        
        st.video(output_clip_path)
        with open(output_clip_path, "rb") as f:
            st.download_button(
                "⬇️ Unduh Klip",
                data=f.read(),
                file_name=f"clip_{start_time:.1f}s-{end_time:.1f}s_{uploaded.name}",
                mime="video/mp4"
            )

        with st.spinner("Mentranskrip audio dari klip..."):
            transcript_data = transcribe_video(output_clip_path)
            transcript_text = transcript_data.get("text", "")

        if transcript_text:
            st.markdown("---")
            st.markdown("#### 📝 Transkrip Klip")
            st.markdown(f"> _{transcript_text}_")

            score = estimate_virality(transcript_text)
            st.markdown(f"#### 📈 Prediksi Skor Viralitas")
            st.progress(int(score), text=f"**{score}/100**")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    logging.error("Terjadi exception utama:", exc_info=True)

finally:
    # --- PEMBERSIHAN ---
    # Pastikan semua objek dan file ditutup/dihapus
    if video_clip_object:
        video_clip_object.close()
        logging.info("Objek VideoFileClip utama ditutup.")
    
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)
        logging.info(f"File sementara dihapus: {temp_video_path}")
        
    if output_clip_path and os.path.exists(output_clip_path):
        os.remove(output_clip_path)
        logging.info(f"File klip output dihapus: {output_clip_path}")