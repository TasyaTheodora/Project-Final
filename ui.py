import os
import tempfile
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import transcribe_video, estimate_virality

# ─── CONFIG HALAMAN ───
st.set_page_config(page_title="Video Trimmer AI", layout="wide")
st.title("✂️ AI Video Trimmer & Scorer")
st.write("Unggah video, potong bagian terbaik, lalu dapatkan transkrip dan skor viralitasnya.")

# ─── PATH FFMPEG (PENTING) ───
# Pastikan path ini benar sesuai dengan lokasi di komputer Anda.
# Cara terbaik adalah menggunakan path absolut untuk menghindari kebingungan.
try:
    ffmpeg_path = os.path.abspath("ffmpeg/ffmpeg-2025-06-28-git-cfd1f81e7d-full_build/bin/ffmpeg.exe")
    if not os.path.exists(ffmpeg_path):
        st.error(f"FFMPEG tidak ditemukan di path: {ffmpeg_path}. Pastikan path sudah benar.")
        st.stop()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
except Exception as e:
    st.error(f"Terjadi masalah saat mengatur path FFMPEG: {e}")
    st.info("Pastikan Anda sudah mengunduh FFMPEG dan meletakkannya di folder yang benar sesuai petunjuk di kode.")
    st.stop()


# ─── UPLOADER ───
uploaded = st.file_uploader("Pilih file video:", type=["mp4", "mov", "avi", "mkv"])
if not uploaded:
    st.info("Silakan unggah file video untuk memulai.")
    st.stop()

# Buat file sementara dengan aman
# Kita menggunakan delete=False agar bisa mendapatkan namanya, lalu akan kita hapus manual di blok finally
suffix = os.path.splitext(uploaded.name)[1]
tfile = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

# Gunakan blok try...finally untuk memastikan file sementara selalu dihapus
try:
    # Tulis data dari file yang diunggah ke file sementara
    tfile.write(uploaded.getbuffer())
    
    # --- KUNCI PERBAIKAN ---
    # Tutup file agar tidak terkunci. Sekarang file aman untuk dibaca oleh proses lain (ffmpeg).
    tfile.close()

    # Tampilkan video player
    st.video(tfile.name)

    # ─── ATUR KLIP ───
    st.markdown("---")
    st.markdown("### Atur Klip")

    # Dapatkan durasi video dengan cara yang aman menggunakan 'with'
    try:
        with VideoFileClip(tfile.name) as video:
            duration = video.duration
    except Exception as e:
        st.error(f"Gagal membaca durasi video. File mungkin rusak atau format tidak didukung. Error: {e}")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.number_input("Mulai dari (detik):", min_value=0.0, max_value=duration, value=0.0, step=0.5)
    with col2:
        # Maksimum durasi slider adalah sisa durasi dari start_time
        max_clip_duration = duration - start_time
        default_duration = min(30.0, max_clip_duration) # Default 30 detik atau sisa durasi
        clip_duration = st.slider("Durasi klip (detik):", 
                                  min_value=1.0, 
                                  max_value=max_clip_duration, 
                                  value=default_duration,
                                  step=1.0)

    end_time = start_time + clip_duration
    st.info(f"Klip akan dipotong dari **{start_time:.1f} detik** hingga **{end_time:.1f} detik**.")

    if st.button("🚀 Potong, Transkrip, dan Analisa!", type="primary"):
        with st.spinner("Memotong video..."):
            try:
                # Potong klip menggunakan 'with' agar sumber daya terbebas otomatis
                with VideoFileClip(tfile.name) as video:
                    clip = video.subclip(start_time, end_time)
                
                # Simpan klip yang sudah dipotong ke file sementara lainnya
                out_tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                clip.write_videofile(out_tmp.name, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                clip.close()
                out_tmp.close() # Tutup file setelah selesai menulis

            except Exception as e:
                st.error(f"Gagal memotong klip: {e}")
                st.stop()

        st.success(f"✅ Klip berhasil dibuat: {start_time:.1f}s → {end_time:.1f}s")
        
        # Tampilkan hasil klip dan tombol download
        st.video(out_tmp.name)
        with open(out_tmp.name, "rb") as f:
            st.download_button(
                "⬇️ Unduh Klip",
                data=f.read(),
                file_name=f"clip_{start_time:.1f}s-{end_time:.1f}s_{uploaded.name}",
                mime="video/mp4"
            )

        # Transkripsi & Viral Score
        with st.spinner("Mentranskrip audio dari klip..."):
            try:
                transcription_data = transcribe_video(out_tmp.name)
                transcript_text = transcription_data["text"]
            except Exception as e:
                st.error(f"Gagal mentranskrip video: {e}")
                transcript_text = "" # Kosongkan jika gagal

        if transcript_text:
            st.markdown("---")
            st.markdown("#### 📝 Transkrip Klip")
            st.markdown(f"> _{transcript_text}_")

            score = estimate_virality(transcript_text)
            st.markdown(f"#### 📈 Prediksi Skor Viralitas")
            st.progress(int(score), text=f"**{score}/100**")
        
        # Hapus file klip sementara setelah selesai
        os.remove(out_tmp.name)


except Exception as e:
    st.error(f"Terjadi kesalahan tak terduga: {e}")

finally:
    # Pastikan file sementara dari video asli selalu dihapus
    if os.path.exists(tfile.name):
        os.remove(tfile.name)