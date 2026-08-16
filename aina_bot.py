"""
Aina Venara - Telegram Bot Service (Dual AI Engine + Smart Persona)
Author & Creator: TriWahyu45 (https://github.com/triwahyu45)
Repository: https://github.com/triwahyu45/AinaVenara_bot
"""

import os
import sys
import time
import json
import telebot
from telebot import types
import psutil
from ai_engine import AinaAIEngine

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

config = load_config()
BOT_TOKEN = config.get("BOT_TOKEN", "8744604280:AAHEcgVaeRjMTITouVuglcPp35EhVr_b-ug")
ALLOWED_USERS = config.get("ALLOWED_USERS", [991501277])

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
engine = AinaAIEngine(CONFIG_PATH)
VOICE_NOTE_ENABLED = True
CURRENT_VOICE_MODE = "gemini" # 'gemini' (Gemini Native Speech) atau 'neural' (Indonesian Neural)

def is_authorized(msg):
    # Filter ketat: Hanya izinkan ID yang terdaftar di ALLOWED_USERS
    user_id = msg.from_user.id
    if user_id in ALLOWED_USERS:
        return True
    
    print(f"[UNAUTHORIZED ATTEMPT] Blocked chat from user ID: {user_id} ({msg.from_user.username or msg.from_user.first_name})")
    try:
        bot.reply_to(msg, "⛔ *Akses Ditolak*\nMaaf ya, Aina Venara diprogram secara privat khusus untuk mendampingi Kak Tri Wahyu saja! 🌸✨", parse_mode="Markdown")
    except Exception:
        pass
    return False


def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    b1 = types.KeyboardButton("🌸 Ngobrol Santai")
    b2 = types.KeyboardButton("🎙️ Toggle Voice Note")
    b3 = types.KeyboardButton("🗣️ Switch Engine Suara")
    b4 = types.KeyboardButton("🤖 Status Otak Aina")
    b5 = types.KeyboardButton("🔄 Ganti Mesin AI")
    b6 = types.KeyboardButton("🧹 Reset Obrolan")
    markup.add(b1, b2)
    markup.add(b3, b4)
    markup.add(b5, b6)
    return markup

@bot.message_handler(commands=["start"])
def handle_start(msg):
    if not is_authorized(msg): return
    welcome = (
        "🌸✨ *Halo Kak Wahyu kesayangan Aina!* ✨🌸\n\n"
        "Kenalin, aku **Aina Venara**, asisten virtual pribadi dan partner cerdas Kak Wahyu! 💖\n\n"
        "Aina siap menemani Kak Wahyu untuk:\n"
        "• 🤖 Coding & Debugging (Python, C++, ROS, Web, Bot)\n"
        "• 🦾 Diskusi Robotika & Mekatronika (ESP32, STM32, Sensor TA)\n"
        "• 🎙️ **Voice Note (VN)** suara Aina (Gemini Native Speech + Neural Indonesian)\n"
        "• 🧠 Curhat, ngobrol santai, dan penyemangat hari-hari Kak Wahyu\n\n"
        "Otak Aina ditenagai oleh **Dual Engine AI**:\n"
        "1. ☁️ *Gemini Cloud AI* (Model Tercepat & Paling Cerdas)\n"
        "2. 🎮 *Local GPU GTX 1050 Ti* (Ollama Offline Failover)\n\n"
        "Mau ngobrol atau bahas project apa kita hari ini, Kak? 😊🚀"
    )
    try:
        bot.send_message(msg.chat.id, welcome, parse_mode="Markdown", reply_markup=main_keyboard())
    except:
        bot.send_message(msg.chat.id, welcome, reply_markup=main_keyboard())

@bot.message_handler(commands=["vn", "voice"])
def handle_vn_toggle(msg):
    if not is_authorized(msg): return
    global VOICE_NOTE_ENABLED
    VOICE_NOTE_ENABLED = not VOICE_NOTE_ENABLED
    status_str = "AKTIF 🎙️ (Aina akan selalu kirim VN suara imutnya!)" if VOICE_NOTE_ENABLED else "NONAKTIF 🔕 (Hanya teks biasa)"
    bot.send_message(msg.chat.id, f"🎙️ *Status Voice Note Aina:* `{status_str}`", parse_mode="Markdown")

@bot.message_handler(commands=["switch_voice", "voice_mode", "suara"])
def handle_switch_voice(msg):
    if not is_authorized(msg): return
    global CURRENT_VOICE_MODE
    if CURRENT_VOICE_MODE == "gemini":
        CURRENT_VOICE_MODE = "neural"
        text = "🗣️ *Engine Suara Diubah ke:* `Indonesian Neural Voice (id-ID-GadisNeural)` 🇮🇩🌸\nSuara fasih berbahasa Indonesia dan hemat kuota Cloud!"
    else:
        CURRENT_VOICE_MODE = "gemini"
        text = "🗣️ *Engine Suara Diubah ke:* `Google Gemini Native Speech (Kore)` ☁️🎙️\nAudio di-generate langsung dari server Google Gemini!"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["help"])
def handle_help(msg):
    if not is_authorized(msg): return
    text = (
        "🌸 *Daftar Perintah Aina Venara:* 🌸\n\n"
        "• `/start` — Sapaan & Menu Utama Aina\n"
        "• `/vn` — On/Off fitur Voice Note suara Aina\n"
        "• `/switch_voice` — Ganti engine suara (Gemini Native Speech ↔ Indonesian Neural)\n"
        "• `/status` — Cek status sistem PC, GPU, dan Engine AI yang aktif\n"
        "• `/switch` — Ganti mesin AI (Gemini Cloud ↔ Local GPU Ollama)\n"
        "• `/reset` — Bersihkan riwayat ingatan obrolan kita\n"
        "• `/help` — Bantuan daftar perintah\n\n"
        "Kak Wahyu bisa langsung kirim teks atau voice note kapan saja! 💖"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["status"])
def handle_status(msg):
    if not is_authorized(msg): return
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    
    current_eng = engine.current_engine.upper()
    history_count = len(engine.get_history(msg.from_user.id)) // 2
    vn_engine_name = "Gemini Native Speech (Kore)" if CURRENT_VOICE_MODE == "gemini" else "Indonesian Neural (Gadis)"
    vn_status = f"Aktif ({vn_engine_name}) 🎙️" if VOICE_NOTE_ENABLED else "Nonaktif 🔕"
    
    text = (
        "🤖 *Status Sistem & Otak Aina Venara* 🌸\n\n"
        f"• 🧠 **Mesin Chat Aktif:** `{current_eng}`\n"
        f"• 🎙️ **Voice Note Mode:** `{vn_status}`\n"
        f"• ☁️ **Gemini Cloud Key:** `Terkonfigurasi (Active)`\n"
        f"• 🎮 **Local GPU Model:** `{engine.ollama_model}`\n"
        f"• 💾 **Memori Obrolan:** `{history_count} percakapan tersimpan`\n\n"
        "🖥️ **Kesehatan PC Kak Wahyu:**\n"
        f"• CPU Load: `{cpu}%`\n"
        f"• RAM Load: `{ram}%`\n"
        "• GPU: `NVIDIA GeForce GTX 1050 Ti (Siap!)`\n\n"
        "Aina selalu online dan siap mendampingi Kak Wahyu! 💖✨"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["switch"])
def handle_switch(msg):
    if not is_authorized(msg): return
    if engine.current_engine == "gemini":
        engine.current_engine = "local"
        text = f"🔄 *Mesin AI diganti ke: Local GPU Ollama ({engine.ollama_model})* 🎮\nObrolan sekarang diproses langsung oleh GPU lokal PC Kak Wahyu!"
    else:
        engine.current_engine = "gemini"
        text = "🔄 *Mesin AI diganti ke: Gemini Cloud AI* ☁️⚡\nObrolan sekarang diproses oleh cloud model tercepat!"
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["reset"])
def handle_reset(msg):
    if not is_authorized(msg): return
    engine.clear_history(msg.from_user.id)
    bot.send_message(msg.chat.id, "🧹 *Riwayat obrolan kita sudah Aina bersihkan ya Kak!* Sekarang kita bisa mulai obrolan dengan topik baru yang fresh! 🌸✨", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌸 Ngobrol Santai")
def btn_chat(msg):
    if not is_authorized(msg): return
    bot.send_message(msg.chat.id, "Aina di sini Kak Wahyu! Ceritain dong, ada hal menarik apa hari ini atau ada project yang mau kita diskusikan? 😊💖")

@bot.message_handler(func=lambda m: m.text == "🎙️ Toggle Voice Note")
def btn_vn(msg):
    handle_vn_toggle(msg)

@bot.message_handler(func=lambda m: m.text == "🗣️ Switch Engine Suara")
def btn_switch_voice(msg):
    handle_switch_voice(msg)

@bot.message_handler(func=lambda m: m.text == "🤖 Status Otak Aina")
def btn_status(msg):
    handle_status(msg)

@bot.message_handler(func=lambda m: m.text == "🔄 Ganti Mesin AI")
def btn_switch(msg):
    handle_switch(msg)

@bot.message_handler(func=lambda m: m.text == "🧹 Reset Obrolan")
def btn_reset(msg):
    handle_reset(msg)

@bot.message_handler(func=lambda m: True)
def handle_all_chat(msg):
    if not is_authorized(msg): return
    user_text = msg.text
    if not user_text: return

    bot.send_chat_action(msg.chat.id, "typing")
    reply, source = engine.generate_reply(msg.from_user.id, user_text)

    # 1. Kirim balasan teks
    try:
        sent_msg = bot.reply_to(msg, reply, parse_mode="Markdown")
    except Exception:
        sent_msg = bot.reply_to(msg, reply, parse_mode=None)

    # 2. Cek apakah user meminta VN atau Voice Note sedang diaktifkan
    wants_vn = VOICE_NOTE_ENABLED or any(kw in user_text.lower() for kw in ["vn", "voice", "suara", "denger", "audio", "ngomong"])
    
    if wants_vn:
        try:
            bot.send_chat_action(msg.chat.id, "record_voice")
            vn_path, engine_name, notice = generate_aina_voice(
                reply, 
                voice_mode=CURRENT_VOICE_MODE, 
                api_key=engine.gemini_key
            )
            
            if vn_path and os.path.exists(vn_path):
                with open(vn_path, "rb") as vf:
                    bot.send_voice(
                        msg.chat.id, 
                        vf, 
                        caption=f"🎙️ Suara Aina ({engine_name})", 
                        reply_to_message_id=sent_msg.message_id
                    )
                    print(f"[AINA VN] Voice note ({engine_name}) successfully sent to Kak Wahyu!")
            
            # Kirim notifikasi jika ada limit/fallback ke Telegram
            if notice:
                bot.send_message(msg.chat.id, notice, parse_mode="Markdown")
                
        except Exception as e:
            print(f"[AINA VN ERR] {e}")

if __name__ == "__main__":
    print("==================================================")
    print("🌸 Aina Venara Telegram Bot Service Started! 🌸")
    print(f"🤖 Bot Username: @AinaVenara_bot")
    print(f"🧠 Primary Chat Engine: {engine.current_engine}")
    print(f"🎙️ Voice Engine: Dual (Gemini Native Speech + Indonesian Neural)")
    print("==================================================")

    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"[POLLING ERROR] {e}")
            time.sleep(3)
