import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
from PIL import Image

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="HypeBot AI Multi-Agent", page_icon="🤖", layout="wide")

# --- 2. API CONFIG ---
# Masukkan API Key kamu di sini
GOOGLE_API_KEY = "AIzaSyA9D5Cj5RQpNXqMsdB-LWGT_1HiSBdTPKc"
genai.configure(api_key=GOOGLE_API_KEY)

# --- 3. DATABASE LOKAL (JSON) ---
DB_FILE = "chat_history_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_to_db(session_id, messages, agent_name):
    db = load_db()
    # Filter agar hanya teks yang disimpan di JSON (gambar tidak bisa masuk JSON langsung)
    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    db[session_id] = {
        "title": f"[{agent_name}] " + (clean_messages[0]["content"][:20] if clean_messages else "New Chat"),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chats": clean_messages,
        "agent": agent_name
    }
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- 4. STYLE CSS (GLASSMORPHISM VIBE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [data-testid="stSidebar"], .stMarkdown { font-family: 'Poppins', sans-serif; }
    .stApp { background: #0E1117; }
    [data-testid="stSidebar"] { background-color: #161920; }
    [data-testid="stChatMessageContent"] { border-radius: 15px; padding: 15px; }
    /* Preview Gambar Kecil */
    .img-preview { border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- 5. INITIALIZATION ---
db_data = load_db()
if "current_session" not in st.session_state:
    st.session_state.current_session = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.messages = []

# --- 6. SIDEBAR (PILIHAN AGENT & UPLOAD) ---
with st.sidebar:
    st.markdown("# 🤖 HypeBot v2.0")
    
    # PILIHAN AGENT SPESIFIK
    st.markdown("### 🎭 Pilih Spesialisasi")
    agent_choice = st.selectbox(
        "Gunakan mode apa?",
        ["Explainer Mode", "Execution Mode"]
    )
    
    if agent_choice == "Explainer Mode":
        sys_instr = "Kamu adalah Tutor Akademik kelas 12. Jelaskan konsep materi sekolah atau programming secara mendalam tapi santai. Gunakan analogi dan ajak user berpikir."
        theme_color = "🟢"
        bot_avatar = "👨‍🏫"
    else:
        sys_instr = "Kamu adalah Senior Pro Builder. Langsung berikan solusi teknis, kode Laravel/PHP 8.4, dan tutorial implementasi fitur project LMS/Inventory secara to-the-point."
        theme_color = "🔵"
        bot_avatar = "🛠️"

    # Load Model dengan System Instruction
    model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite', system_instruction=sys_instr)

    if st.button("+ Obrolan Baru", use_container_width=True):
        st.session_state.current_session = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 🖼️ Analisis Gambar")
    img_file = st.file_uploader("Upload foto tugas/error...", type=["jpg", "png", "jpeg"])
    if img_file:
        st.image(img_file, caption="Gambar terdeteksi", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📜 Riwayat")
    for sid, info in reversed(list(db_data.items())):
        if st.button(f"📄 {info.get('title', 'Chat')}", key=sid, use_container_width=True):
            st.session_state.current_session = sid
            st.session_state.messages = info['chats']
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True) # Kasih jarak biar nggak mepet
    st.markdown("---")
    with st.expander("⚙️ Setelan"):
        # Kita simpan ke session_state supaya nilainya nggak ilang pas ganti mode
        st.text_input("Panggilan Kamu", value="Bro", key="user_nick_val")
        st.slider("Kreativitas (Temperature)", 0.0, 1.0, 0.7, key="api_temp_val")
        st.caption("Pake 0.2 buat debugging kodingan!")

# --- 7. MAIN UI ---
st.markdown(f"## {theme_color} Mode: {agent_choice}")

if agent_choice == "Explainer Mode":
    st.info("💡 **Mentor Mode:** Fokus menjelaskan konsep, teori, dan cara kerja materi secara mendalam.")
else:
    st.info("🛠️ **Execution Mode:** Fokus pada pembuatan kode, debugging, dan solusi teknis project.")

st.markdown("---")

# Container Chat
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role, avatar="👤" if role == "user" else bot_avatar):
            st.markdown(message["content"])

# --- 8. INPUT AREA ---
if prompt := st.chat_input("Minta Gemini..."):
    # Tampilkan & Simpan Pesan User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

    # Respon Assistant
    with chat_container:
        with st.chat_message("assistant", avatar=bot_avatar):
            res_place = st.empty()
            res_place.markdown("*(Sedang memproses...)*")
            
            try:
                if img_file:
                    # Mode Vision (Gambar + Teks)
                    img = Image.open(img_file)
                    response = model.generate_content([prompt, img])
                else:
                    # Mode Chat Biasa (History)
                    history = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                    chat = model.start_chat(history=history)
                    response = chat.send_message(prompt)
                
                res_place.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                save_to_db(st.session_state.current_session, st.session_state.messages, agent_choice)
                
            except Exception as e:
                res_place.error(f"Waduh error bro: {e}")