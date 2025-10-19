import streamlit as st
import textwrap
import pandas as pd
import io
import datetime
from google import genai
from typing import List, Dict, Any

st.set_page_config(page_title="AI IT Support Chatbot - Gemini", layout="centered")

# Inisialisasi Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_log" not in st.session_state:
    st.session_state.session_log = []
if "diagnosis_complete" not in st.session_state:
    st.session_state.diagnosis_complete = False
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None

MODEL = "gemini-2.5-flash"

def build_initial_prompt(bsod_code: str, info: str) -> str:
    """Membangun prompt awal untuk diagnosis."""
    return textwrap.dedent(f"""
    Anda adalah asisten Dukungan IT yang berpengalaman. Jawablah *sepenuhnya dalam Bahasa Indonesia*.

    Tugas Anda adalah melakukan diagnosis awal. Pengguna melaporkan Blue Screen (BSOD) atau error sistem dengan kode: {bsod_code}

    Detail tambahan:
    {info}

    Mohon sediakan analisis berikut:
    1. Kemungkinan penyebab utama (3 poin singkat dan padat)
    2. Langkah-langkah pemecahan masalah (troubleshooting) yang direkomendasikan
    3. Alat atau perintah berguna untuk diagnosis
    4. Tingkat keyakinan (rendah/sedang/tinggi)
    
    Setelah memberikan diagnosis awal ini, berikan respons yang mengundang pengguna untuk bertanya lebih lanjut atau mendiskusikan langkah berikutnya.
    """)

def log_to_csv(log_data: List[Dict[str, str]]):
    """Menyimpan log percakapan ke Session State untuk diunduh."""
    # Menambahkan data baru ke log global
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.session_log.append({
        "timestamp": timestamp,
        "conversation": log_data
    })

def create_download_file(log_data: List[Dict[str, Any]]) -> io.BytesIO:
    """Mengubah log percakapan menjadi file CSV yang siap diunduh."""
    
    flattened_data = []
    
    for session in log_data:
        timestamp = session['timestamp']
        conversation = session['conversation']
        
        # Ekstrak detail BSOD awal
        bsod_code = ""
        initial_info = ""
        if conversation and conversation[0]['role'] == 'user' and 'BSOD_CODE' in conversation[0]:
            bsod_code = conversation[0]['BSOD_CODE']
            initial_info = conversation[0]['INITIAL_INFO']

        for i, turn in enumerate(conversation):
            is_initial = (i == 0) and (turn['role'] == 'user')
            
            flattened_data.append({
                "Timestamp_Sesi": timestamp,
                "Kode_BSOD_Awal": bsod_code if is_initial else "",
                "Info_Tambahan_Awal": initial_info if is_initial else "",
                "No_Giliran": i + 1,
                "Role": turn['role'],
                "Pesan": turn['text']
            })

    df = pd.DataFrame(flattened_data)
    
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    return buffer

def start_new_session(api_key: str, bsod_code: str, info: str):
    """Memulai diagnosis awal dan inisialisasi sesi chat Gemini."""
    if not api_key:
        st.error("Masukkan Kunci API Gemini terlebih dahulu.")
        return

    try:
        client = genai.Client(api_key=api_key)
        st.session_state.gemini_client = client
        st.session_state.chat_session = client.chats.create(model=MODEL)
        st.session_state.chat_history = []
        st.session_state.diagnosis_complete = True
        initial_prompt = build_initial_prompt(bsod_code or "ERROR_TIDAK_DIKETAHUI", info or "Tidak ada detail yang diberikan.")
        
        st.session_state.chat_history.append({
            "role": "user", 
            "text": initial_prompt,
            "BSOD_CODE": bsod_code or "ERROR_TIDAK_DIKETAHUI",
            "INITIAL_INFO": info or "Tidak ada detail yang diberikan."
        })
        
        with st.spinner("Memproses diagnosis awal dari Gemini..."):
            response = st.session_state.chat_session.send_message(initial_prompt)
            
        st.session_state.chat_history.append({"role": "model", "text": response.text})
        log_to_csv(st.session_state.chat_history)
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Terjadi kesalahan saat memulai sesi: {e}")
        st.session_state.diagnosis_complete = False

def send_follow_up_message(prompt: str):
    """Mengirim pesan tindak lanjut dan memperbarui riwayat."""
    if st.session_state.chat_session is None:
        st.error("Sesi chat tidak aktif. Mohon mulai diagnosis baru.")
        return
    st.session_state.chat_history.append({"role": "user", "text": prompt})
    try:
        response = st.session_state.chat_session.send_message(prompt)
        st.session_state.chat_history.append({"role": "model", "text": response.text})
        log_to_csv(st.session_state.chat_history)

    except Exception as e:
        error_message = f"⚠️ Error saat mengirim pesan: {e}"
        st.session_state.chat_history.append({"role": "model", "text": error_message})
        st.error(error_message)


# ----------------------------
# UI
# ----------------------------

st.title("💻 Asisten Dukungan IT (AI)")
st.caption("Didukung oleh Gemini — Sesi Chat Interaktif untuk Diagnosis Error Sistem.")

st.divider()

if not st.session_state.diagnosis_complete:
    with st.container(border=True):
        st.subheader("🛠️ Input Diagnosis Awal")
        api_key = st.text_input("Masukkan Kunci API GEMINI", type="password", key="api_key_initial")
        bsod_code = st.text_input("Kode BSOD / Error (mis: IRQL_NOT_LESS_OR_EQUAL)", key="bsod_code_initial")
        info = st.text_area("Informasi Tambahan (gejala, waktu kejadian, perubahan terakhir, dll.)", height=100, key="info_initial")
        
        if st.button("Mulai Diagnosis Interaktif"):
            if api_key and bsod_code:
                start_new_session(api_key, bsod_code, info)
            elif not api_key:
                st.error("Kunci API harus diisi.")
            else:
                st.error("Kode BSOD/Error harus diisi.")

else:
    st.subheader("💬 Sesi Diskusi Diagnosis")
    for message in st.session_state.chat_history:
        if not ("BSOD_CODE" in message):
            with st.chat_message(message["role"]):
                st.markdown(message["text"])
    
    if prompt := st.chat_input("Tanyakan lebih lanjut tentang langkah selanjutnya atau detail error..."):
        send_follow_up_message(prompt)
        st.rerun()

    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("Sesi Diagnosis Baru", type="primary"):
            st.session_state.diagnosis_complete = False
            st.session_state.chat_history = []
            st.session_state.chat_session = None
            st.rerun()
            
    with col2:
        if st.session_state.session_log:
            csv_file = create_download_file(st.session_state.session_log)
            st.download_button(
                label="📥 Unduh Log Percakapan (CSV)",
                data=csv_file,
                file_name=f"log_diagnosis_gemini_{datetime.date.today()}.csv",
                mime="text/csv"
            )

st.divider()
st.caption("Aplikasi ini menggunakan Session State Streamlit untuk menyimpan riwayat. Log diunduh dalam format CSV.")