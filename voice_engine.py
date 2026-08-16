"""
Aina Venara - Voice Note (TTS) Synthesizer Engine
Dual Mode: Gemini Native Speech API (Cloud) + Indonesian Neural Voice (Edge) + Auto-Fallback
Author & Creator: TriWahyu45 (https://github.com/triwahyu45)
"""

import os
import re
import json
import base64
import asyncio
import edge_tts
import time
import urllib.request
import urllib.error

VOICE_DIR = os.path.join(os.path.dirname(__file__), "Voices")
os.makedirs(VOICE_DIR, exist_ok=True)

# Default Mode: "gemini" atau "neural"
DEFAULT_VOICE_MODE = "gemini"

# Config Gemini TTS
GEMINI_TTS_MODEL = "gemini-3.1-flash-tts-preview"
GEMINI_VOICE_NAME = "Kore" # Suara wanita ekspresif / ramah di Gemini Speech

# Config Edge Neural
NEURAL_VOICE_NAME = "id-ID-GadisNeural"

def clean_text_for_speech(text):
    """Membersihkan emoji, markdown asterisk, dan format chat agar ucapan TTS terdengar fasih."""
    if not text: return ""
    cleaned = re.sub(r'[*_`#~]', '', text)
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    cleaned = re.sub(r'[^\w\s.,?!\'"\-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def generate_gemini_speech(text, api_key):
    """Menghasilkan audio langsung via Google Gemini Interactions Speech API."""
    if not api_key: return None, None
    clean_txt = clean_text_for_speech(text)
    if not clean_txt or len(clean_txt) < 2: return None, None

    if len(clean_txt) > 350:
        clean_txt = clean_txt[:350] + "..."

    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}"
    payload = {
        "model": GEMINI_TTS_MODEL,
        "input": f"Say warmly and cheerfully in Indonesian: {clean_txt}",
        "response_format": {
            "type": "audio"
        },
        "generation_config": {
            "speech_config": [
                {"voice": GEMINI_VOICE_NAME}
            ]
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key}
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            data = json.loads(res.read().decode("utf-8"))
            for step in data.get("steps", []):
                for item in step.get("content", []):
                    if item.get("type") == "audio" and "data" in item:
                        raw_bytes = base64.b64decode(item["data"])
                        filename = f"aina_gemini_vn_{int(time.time()*1000)}.wav"
                        out_path = os.path.join(VOICE_DIR, filename)
                        with open(out_path, "wb") as f:
                            f.write(raw_bytes)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                            return out_path, None
    except urllib.error.HTTPError as he:
        err_msg = f"HTTP Error {he.code}: {he.reason}"
        print(f"[GEMINI SPEECH HTTP ERR] {err_msg}")
        return None, err_msg
    except Exception as e:
        print(f"[GEMINI SPEECH ERR] {e}")
        return None, str(e)
    return None, "No audio generated"

async def _synthesize_neural_async(text, out_path):
    tts = edge_tts.Communicate(
        text=text,
        voice=NEURAL_VOICE_NAME,
        rate="+8%",
        pitch="+4Hz"
    )
    await tts.save(out_path)

def generate_neural_speech(text):
    """Menghasilkan audio via Indonesian Neural TTS Engine."""
    clean_txt = clean_text_for_speech(text)
    if not clean_txt or len(clean_txt) < 2: return None

    if len(clean_txt) > 400:
        clean_txt = clean_txt[:400] + "..."

    filename = f"aina_neural_vn_{int(time.time()*1000)}.ogg"
    out_path = os.path.join(VOICE_DIR, filename)

    try:
        asyncio.run(_synthesize_neural_async(clean_txt, out_path))
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception as e:
        print(f"[NEURAL SPEECH ERR] {e}")
    return None

def generate_aina_voice(text, voice_mode="gemini", api_key=None):
    """
    Fungsi utama generator suara Aina Venara dengan auto-fallback:
    - Mode 'gemini': Coba Gemini Speech API duluan, jika limit/error fallback otomatis ke Neural.
    - Mode 'neural': Langsung menggunakan Indonesian Neural Engine.
    Mengembalikan (file_path, engine_used, error_notice_if_fallback)
    """
    if voice_mode == "gemini" and api_key:
        path, err = generate_gemini_speech(text, api_key)
        if path:
            return path, "Gemini Native Speech (Kore)", None
        else:
            # Fallback ke Neural Engine jika Gemini TTS limit/error
            print(f"[VOICE FALLBACK] Gemini TTS limit ({err}), falling back to Indonesian Neural TTS...")
            path_fb = generate_neural_speech(text)
            notice = f"⚠️ *Info Kuota Audio:* Gemini TTS sedang limit ({err}). Aina otomatis alihkan suara ke *Indonesian Neural Voice* agar VN tetap terkirim lancar!"
            return path_fb, "Indonesian Neural Voice (Failover)", notice
    else:
        path = generate_neural_speech(text)
        return path, "Indonesian Neural Voice", None
