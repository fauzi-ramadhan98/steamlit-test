import streamlit as st
import json
import textwrap
from google import genai 
# Menghilangkan: from google.genai.errors import APIError 

# ----------------------------
# Fungsi bantu
# ----------------------------
def build_prompt(bsod_code: str, info: str) -> str:
    """Membangun prompt untuk model Gemini, meminta jawaban dalam Bahasa Indonesia."""
    return textwrap.dedent(f"""
    Anda adalah asisten Dukungan IT yang berpengalaman. Jawablah *sepenuhnya dalam Bahasa Indonesia*.

    Pengguna melaporkan Blue Screen (BSOD) atau error sistem dengan kode: {bsod_code}

    Detail tambahan:
    {info}

    Mohon sediakan analisis berikut:
    1. Kemungkinan penyebab utama (3 poin singkat dan padat)
    2. Langkah-langkah pemecahan masalah (troubleshooting) yang direkomendasikan
    3. Alat atau perintah berguna untuk diagnosis
    4. Tingkat keyakinan (rendah/sedang/tinggi)
    Buatlah jawaban yang singkat, jelas, dan dapat ditindaklanjuti.
    """)

def call_gemini_sdk(prompt: str, api_key: str, model: str = "gemini-2.5-flash"):
    """Memanggil API Gemini menggunakan Google GenAI SDK resmi."""
    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        
        return response.text

    except Exception as e:
        return f"⚠️ Terjadi kesalahan: {e}"

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="AI IT Support - Gemini", layout="centered")

st.title("💻 Asisten Dukungan IT (AI)")
st.caption("Didukung oleh Gemini — analisis otomatis berdasarkan kode BSOD atau error sistem.")

st.divider()

# Input API Key
api_key = st.text_input("Masukkan Kunci API GEMINI", type="password")
bsod_code = st.text_input("Kode BSOD / Error (mis: IRQL_NOT_LESS_OR_EQUAL)")
info = st.text_area("Informasi Tambahan (gejala, waktu kejadian, perubahan terakhir, dll.)", height=120)

if st.button("Diagnosa Sekarang"):
    if not api_key:
        st.error("Masukkan Kunci API Gemini terlebih dahulu.")
    else:
        st.subheader("🤖 Analisis dari Gemini")
        
        prompt = build_prompt(bsod_code or "ERROR_TIDAK_DIKETAHUI", info or "Tidak ada detail yang diberikan.")
        
        with st.spinner("Meminta analisis dari Gemini..."):
            answer = call_gemini_sdk(prompt, api_key) 
        st.markdown(answer)

st.divider()
st.caption("Aplikasi ini tidak menyimpan data apa pun. Semua analisis dilakukan langsung via API Gemini.")