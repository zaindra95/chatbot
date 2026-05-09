import google.generativeai as genai
import os

# Masukkan API Key dari Google AI Studio
# Link: https://aistudio.google.com/app/apikey
os.environ["GEMINI_API_KEY"] = "AIzaSyA9D5Cj5RQpNXqMsdB-LWGT_1HiSBdTPKc"

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Inisialisasi model (Gemini 2.5 Flash lebih ringan & gratisannya banyak)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Memulai sesi chat agar bot punya "ingatan"
chat = model.start_chat(history=[])

print("--- CHATBOT GEMINI AKTIF ---")
print("Ketik 'exit' untuk berhenti.\n")

while True:
    user_input = input("Kamu: ")
    
    if user_input.lower() in ['exit', 'keluar', 'stop']:
        print("Bot: Sampai jumpa lagi, bro!")
        break
        
    try:
        # Kirim pesan ke Gemini
        response = chat.send_message(user_input)
        print(f"Bot: {response.text}\n")
    except Exception as e:
        print(f"Aduh, ada error nih: {e}")  