import os
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality
import uuid
import yt_dlp 
import logging

# ─── SETUP ───
st.set_page_config(page_title="Video Trimmer AI", layout="wide")
st.title("✂️ AI Video Clipper & Scorer")
st.write("Unggah video atau masukkan link YouTube untuk menemukan momen viral secara otomatis.")

TEMP_DIR = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# Inisialisasi session state yang lebih lengkap
for key in ['temp_video_path', 'output_clip_path', 'duration', 'video_ready']:
    if key not in st.session_state:
        st.session_state[key] = None if 'path' in key else 0 if key == 'duration' else False

def cleanup_files():
    # Fungsi untuk membersihkan file-file lama
    if st.session_state.temp_video_path and os.path.exists(st.session_state.temp_video_path):
        try: os.remove(st.session_state.temp_video_path)
        except: pass
    st.session_state.temp_video_path = None
    st.session_state.video_ready = False
    st.session_state.duration = 0

# ─── INPUT VIDEO: DENGAN OPSI TAB ───
input_tab1, input_tab2 = st.tabs(["Unggah File", "🔗 Dari Link YouTube"])

with input_tab1:
    uploaded_file = st.file_uploader("Pilih file video lokal:", type=["mp4", "mov", "avi", "mkv"])
    if uploaded_file:
        cleanup_files()
        suffix = os.path.splitext(uploaded_file.name)[1]
        temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{suffix}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.temp_video_path = temp_path
        st.session_state.video_ready = True
        st.rerun()

with input_tab2:
    youtube_url = st.text_input("Masukkan URL video YouTube:", key="youtube_url_input")
    if st.button("Proses Link YouTube"):
        if youtube_url:
            cleanup_files()
            with st.spinner("Menganalisis dan mengunduh video..."):
                try:
                    # --- LANGKAH 1: AMBIL INFORMASI VIDEO (TERMASUK DURASI) TANPA DOWNLOAD ---
                    ydl_opts_info = {'noplaylist': True, 'quiet': True}
                    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                        info_dict = ydl.extract_info(youtube_url, download=False)
                        st.session_state.duration = info_dict.get('duration', 0)

                    # --- LANGKAH 2: DOWNLOAD VIDEO DENGAN KUALITAS YANG DIOPTIMALKAN (720p) ---
                    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp4")
                    ydl_opts_download = {
                        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': temp_path,
                        'noplaylist': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                        ydl.download([youtube_url])
                    
                    st.session_state.temp_video_path = temp_path
                    st.session_state.video_ready = True
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses link YouTube. Pastikan link valid. Error: {e}")
        else:
            st.warning("Harap masukkan URL YouTube.")


# ─── BAGIAN UTAMA APLIKASI (HANYA JALAN JIKA VIDEO SIAP) ───
if not st.session_state.video_ready:
    st.info("Silakan unggah file atau proses link YouTube untuk memulai.")
    st.stop()

st.success("✅ Video siap diproses!")
st.video(st.session_state.temp_video_path)

try:
    # --- PERUBAHAN KUNCI: GUNAKAN DURASI DARI SESSION STATE ---
    # Ini menghindari pembukaan file video yang berat setelah download
    duration = st.session_state.duration
    if duration == 0: # Fallback jika durasi gagal didapat dari yt-dlp
        with VideoFileClip(st.session_state.temp_video_path) as v:
            duration = v.duration
    
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

