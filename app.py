import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="HypeBot AI - Pro", page_icon="⚡", layout="wide")

# --- 2. API CONFIG ---
GOOGLE_API_KEY = "AIzaSyA9D5Cj5RQpNXqMsdB-LWGT_1HiSBdTPKc"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# --- 3. FUNGSI DATABASE LOKAL (JSON) ---
DB_FILE = "chat_history_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_to_db(session_id, messages):
    db = load_db()
    db[session_id] = {
        "title": messages[0]["content"][:25] + "..." if messages else "Obrolan Baru",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chats": messages
    }
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# --- 4. STYLE CSS (Tetap Modern & Ga Kaku) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [data-testid="stSidebar"], .stMarkdown { font-family: 'Poppins', sans-serif; }
    .stApp { background: #0E1117; }
    [data-testid="stSidebar"] { background-color: #161920; border-right: 1px solid #262730; }
    .stChatInputContainer { border-radius: 30px !important; background-color: #161920 !important; }
    [data-testid="stChatMessage"] { background-color: transparent; margin-bottom: 20px; }
    [data-testid="stChatMessageContent"] { border-radius: 20px; padding: 15px 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    /* User: Biru, Bot: Abu */
    [data-testid="stChatMessage"]:has(div[aria-label="avatar of user"]) div[data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #007BFF 0%, #00C8FF 100%); color: white; margin-left: auto;
    }
    [data-testid="stChatMessage"]:has(div[aria-label="avatar of assistant"]) div[data-testid="stChatMessageContent"] {
        background-color: #262730; color: #E0E0E0; border: 1px solid #363740;
    }
    /* Sidebar Item */
    .chat-history-item {
        padding: 10px; border-radius: 10px; background: #262730; margin-bottom: 5px; font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. INITIALIZATION (VERSI FIX REFRESH) ---
db_data = load_db()

if "current_session" not in st.session_state:
    if db_data:
        # Ambil session ID terbaru (yang paling terakhir di-save)
        last_session_id = list(db_data.keys())[-1]
        st.session_state.current_session = last_session_id
        st.session_state.messages = db_data[last_session_id]['chats']
    else:
        # Kalau benar-benar baru pertama kali buka dan gak ada history
        st.session_state.current_session = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []

# Pastikan pesan selalu sinkron dengan database saat session dipilih
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 6. SIDEBAR (RIWAYAT CHAT) ---
with st.sidebar:
    st.markdown("# ⚡ HypeBot AI")
    if st.button("+ Obrolan Baru", use_container_width=True):
        st.session_state.current_session = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📜 Percakapan")
    
    # Menampilkan daftar chat dari JSON
    for sid, info in reversed(list(db_data.items())):
        if st.button(f"📄 {info['title']}", key=sid, use_container_width=True):
            st.session_state.current_session = sid
            st.session_state.messages = info['chats']
            st.rerun()

    st.markdown("---")
    if st.button("Hapus Semua Data 🗑️", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.messages = []
        st.rerun()

# --- 7. MAIN UI ---
st.markdown(f"## Ngobrol Yuk! ✨")
st.caption(f"Session ID: {st.session_state.current_session}")
st.markdown("---")

# Tampilkan chat yang sedang aktif
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# Input & Logic
if prompt := st.chat_input("Tanya materi sekolah atau coding, bro..."):
    # Simpan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Respon Gemini
    with st.chat_message("assistant", avatar="🤖"):
        res_place = st.empty()
        res_place.markdown("*(Mikir sebentar...)*")
        try:
            # Kita buat chat session baru tiap kirim pesan biar simple tapi tetep konteks
            chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
            response = chat.send_message(prompt)
            res_place.markdown(response.text)
            st.session_state.messages.append({"role": "model", "content": response.text})
            
            # SIMPAN KE DATABASE JSON
            save_to_db(st.session_state.current_session, st.session_state.messages)
        except Exception as e:
            res_place.error(f"Error: {e}")