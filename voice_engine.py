"""
Aina Venara - Voice Note (TTS) Synthesizer Engine
Author & Creator: TriWahyu45 (https://github.com/triwahyu45)
"""

import os
import re
import asyncio
import edge_tts
import time

VOICE_DIR = os.path.join(os.path.dirname(__file__), "Voices")
os.makedirs(VOICE_DIR, exist_ok=True)

# Suara AI Gadis Indonesia Jernih & Imut (Aina Persona)
AINA_VOICE = "id-ID-GadisNeural"

def clean_text_for_speech(text):
    """Membersihkan emoji, markdown asterisk, dan simbol agar ucapan TTS terdengar fasih."""
    if not text: return ""
    # Hapus markdown formatting
    cleaned = re.sub(r'[*_`#~]', '', text)
    # Hapus URL
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Hapus emoji dan simbol khusus
    cleaned = re.sub(r'[^\w\s.,?!\'"\-]', ' ', cleaned)
    # Rapikan spasi
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

async def _synthesize_async(text, out_path):
    tts = edge_tts.Communicate(
        text=text,
        voice=AINA_VOICE,
        rate="+12%",   # Sedikit lebih lincah dan bersemangat (Genki)
        pitch="+6Hz"   # Pitch nada gadis anime manis
    )
    await tts.save(out_path)

def generate_aina_voice(text):
    """Menghasilkan file OGG voice note Telegram untuk Aina Venara."""
    try:
        clean_txt = clean_text_for_speech(text)
        if not clean_txt or len(clean_txt) < 2:
            return None
        
        # Batasi panjang TTS maksimal 400 karakter per VN agar tidak terlalu panjang
        if len(clean_txt) > 400:
            clean_txt = clean_txt[:400] + "..."

        filename = f"aina_vn_{int(time.time()*1000)}.ogg"
        out_path = os.path.join(VOICE_DIR, filename)

        asyncio.run(_synthesize_async(clean_txt, out_path))

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception as e:
        print(f"[TTS SYNTH ERR] {e}")
    return None
