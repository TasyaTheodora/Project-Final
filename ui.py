import os
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality
import uuid

# ─── SETUP ───
st.set_page_config(page_title="Video Trimmer AI", layout="wide")
st.title("✂️ AI Video Trimmer & Scorer")
st.write("Unggah video, potong bagian terbaik, lalu dapatkan transkrip dan skor viralitasnya.")

TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# --- BLOK PATH FFMPEG DIHAPUS ---
# Kita tidak lagi memerlukan path FFMPEG lokal. 
# Server akan menemukannya secara otomatis berkat packages.txt.

if 'temp_video_path' not in st.session_state:
    st.session_state.temp_video_path = None
if 'output_clip_path' not in st.session_state:
    st.session_state.output_clip_path = None

uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi", "mkv"])

if uploaded:
    suffix = os.path.splitext(uploaded.name)[1]
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{suffix}")
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.session_state.temp_video_path = temp_path
    st.session_state.output_clip_path = None

if not st.session_state.temp_video_path or not os.path.exists(st.session_state.temp_video_path):
    st.info("Silakan unggah file video untuk memulai.")
    st.stop()

st.video(st.session_state.temp_video_path)

try:
    with VideoFileClip(st.session_state.temp_video_path) as video_for_duration:
        duration = video_for_duration.duration
    
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
            video_to_clip, sub_clip = None, None
            try:
                video_to_clip = VideoFileClip(st.session_state.temp_video_path)
                sub_clip = video_to_clip.subclip(start_time, end_time)
                output_path = os.path.join(TEMP_DIR, f"clip_{uuid.uuid4()}.mp4")
                sub_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                st.session_state.output_clip_path = output_path
            finally:
                if sub_clip: sub_clip.close()
                if video_to_clip: video_to_clip.close()

except Exception as e:
    st.error(f"Gagal memproses video. Error: {e}")
    st.stop()

if st.session_state.output_clip_path and os.path.exists(st.session_state.output_clip_path):
    st.success("✅ Klip berhasil dibuat!")
    st.video(st.session_state.output_clip_path)
    
    with open(st.session_state.output_clip_path, "rb") as f:
        st.download_button("⬇️ Unduh Klip", data=f.read(), file_name=f"clip.mp4", mime="video/mp4")
    
    with st.spinner("Menganalisis potensi viral..."):
        transcription_data = transcribe_video(st.session_state.output_clip_path)
        
        if transcription_data and transcription_data["text"]:
            analysis_result = estimate_virality(transcription_data)
            score = analysis_result["total_score"]
            details = analysis_result["details"]

            st.markdown(f"#### 📈 Prediksi Skor Viralitas")
            st.progress(score, text=f"**{score}/100**")

            with st.expander("Lihat Detail Analisis Skor"):
                for key, value in details.items():
                    st.markdown(f"**{key}**: {value}")

            st.markdown("---")
            st.markdown("#### 📝 Transkrip Klip")
            st.markdown(f"> _{transcription_data['text']}_")
        else:
            st.warning("Tidak dapat menganalisis video karena tidak ada teks yang terdeteksi.")
