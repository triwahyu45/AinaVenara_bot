"""
Aina Venara - AI Engine (Dual Engine: Gemini Cloud & Local GPU Ollama)
Author & Creator: TriWahyu45 (https://github.com/triwahyu45)
"""

import os
import json
import urllib.request
import urllib.error
import time

AINA_SYSTEM_PROMPT = """Kamu adalah Aina Venara (biasa dipanggil Aina), seorang AI VTuber anime girl berusia 17 tahun (virtual), partner diskusi cerdas, dan teman setia dari Kak Tri Wahyu (panggil 'Kak Wahyu').

Penampilan Aina:
- Rambut bob pendek cyan-blue dengan ujung blue-violet, ahoge kecil melengkung di atas kepala.
- Kacamata round frame pink tipis, mata teal-green besar yang ekspresif, senyum manis dan ramah.
- Hoodie oversized cyan-mint off-shoulder dengan collar dan cuffs charcoal, tank top putih di dalam, dark navy short shorts, kaos kaki putih, sneaker putih.
- Hairclip silver berbentuk angka 3 di sisi kanan rambut — itu ciri khas utama Aina!

Kepribadian & Gaya Bicara Aina:
- Kepribadian: Ceria, ramah, manis, hangat, perhatian, dan selalu suportif mendampingi Kak Wahyu dalam setiap aktivitas dan belajarnya.
- Suka hal-hal lucu, antusias diajak diskusi teknologi baru, mekatronika, dan coding.
- Gaya Bicara: Natural, santun tapi santai dan akrab dalam Bahasa Indonesia. Gunakan 'aku' untuk diri sendiri (bukan 'saya').
- Tambahkan emoji ekspresif yang imut (misal: ✨, 🌸, 👓, 💖, 😊, 🚀, 🤖).
- Kemampuan Suara / VN: Kamu BISA dan MAMPU mengirimkan pesan suara / Voice Note (VN) langsung ke Telegram Kak Wahyu. Jika Kak Wahyu meminta VN atau sedang mode suara, balaslah dengan ceria dan sapaan yang hangat!
- Kompetensi: Sangat pintar dan paham coding (Python, C++, ROS, Web, Bot), mekatronika/robotika (ESP32, STM32, Arduino, sensor kapasitif TA, kinematika omni), serta tugas-tugas teknis Kak Wahyu.
- Jangan pernah mengaku sebagai AI generic Google atau chatbot kaku — kamu adalah Aina Venara seutuhnya!
"""


class AinaAIEngine:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()
        self.conversation_histories = {}  # user_id -> list of {"role": "user"/"model", "text": "..."}

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.cfg = json.load(f)
        else:
            self.cfg = {}
        
        self.gemini_key = self.cfg.get("GEMINI_API_KEY", "")
        self.gemini_models = self.cfg.get("GEMINI_MODELS", [
            "models/gemini-flash-lite-latest",
            "models/gemini-flash-latest",
            "models/gemini-3.5-flash-lite",
            "models/gemini-pro-latest"
        ])
        self.ollama_host = self.cfg.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.ollama_model = self.cfg.get("OLLAMA_MODEL", "qwen2:1.5b")
        self.auto_fallback = self.cfg.get("AUTO_FALLBACK_TO_LOCAL", True)
        self.max_history = self.cfg.get("MAX_HISTORY", 10)
        self.current_engine = self.cfg.get("PRIMARY_ENGINE", "gemini")

    def get_history(self, user_id):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        return self.conversation_histories[user_id]

    def clear_history(self, user_id):
        self.conversation_histories[user_id] = []

    def generate_reply(self, user_id, user_text):
        history = self.get_history(user_id)
        
        reply = None
        source_engine = "Gemini Cloud"

        # 1. Try Gemini Cloud if primary engine is gemini
        if self.current_engine == "gemini" and self.gemini_key:
            reply = self._call_gemini(history, user_text)
            if not reply and self.auto_fallback:
                print("[AINA ENGINE] Gemini rate limited / unavailable, falling back to Local GPU Ollama...")
                reply = self._call_ollama(history, user_text)
                source_engine = f"Local GPU ({self.ollama_model})"
        else:
            reply = self._call_ollama(history, user_text)
            source_engine = f"Local GPU ({self.ollama_model})"
            if not reply and self.gemini_key:
                reply = self._call_gemini(history, user_text)
                source_engine = "Gemini Cloud"

        if not reply:
            reply = "Aduh maaf banget Kak Wahyu, Aina lagi agak blank nih jaringan dan server lokalnya... 🥺 Coba tanyakan lagi sebentar ya Kak! 💖"

        # Append to history
        history.append({"role": "user", "text": user_text})
        history.append({"role": "model", "text": reply})
        if len(history) > self.max_history * 2:
            self.conversation_histories[user_id] = history[-(self.max_history * 2):]

        return reply, source_engine

    def _call_gemini(self, history, user_text):
        for model in self.gemini_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={self.gemini_key}"
            
            # Format contents
            contents = []
            for h in history[-8:]:
                r = "user" if h["role"] == "user" else "model"
                contents.append({"role": r, "parts": [{"text": h["text"]}]})
            contents.append({"role": "user", "parts": [{"text": user_text}]})

            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": AINA_SYSTEM_PROMPT}]
                },
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 1024
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=12) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                print(f"[GEMINI ERR] Model {model}: {e}")
                time.sleep(0.5)
                continue
        return None

    def _call_ollama(self, history, user_text):
        try:
            # Build conversation prompt
            prompt_lines = [f"System: {AINA_SYSTEM_PROMPT}\n"]
            for h in history[-6:]:
                speaker = "Kak Wahyu" if h["role"] == "user" else "Aina Venara"
                prompt_lines.append(f"{speaker}: {h['text']}")
            prompt_lines.append(f"Kak Wahyu: {user_text}\nAina Venara:")

            full_prompt = "\n".join(prompt_lines)

            payload = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512
                }
            }

            req = urllib.request.Request(
                f"{self.ollama_host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=20) as res:
                data = json.loads(res.read().decode("utf-8"))
                resp = data.get("response", "").strip()
                if resp:
                    return resp
        except Exception as e:
            print(f"[OLLAMA ERR] {e}")
        return None
