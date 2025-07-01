import streamlit as st

# Optional: atur title browser & layout
st.set_page_config(
    page_title="Project Final",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Judul halaman
st.title("🚀 Project Final Dashboard")

# Sidebar sederhana
st.sidebar.header("📋 Navigasi")
menu = st.sidebar.radio("Pilih halaman:", ["Home", "Data", "Tentang"])

if menu == "Home":
    st.write("Selamat datang di halaman **Home**!")
elif menu == "Data":
    st.write("Ini halaman **Data**. Masukkan tabel/grafik Anda di sini.")
else:
    st.write("Tentang aplikasi ini: ...")
