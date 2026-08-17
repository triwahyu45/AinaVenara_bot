"""
Aina Venara - Long-Term Memory & Chat Persistence Storage
Author & Creator: TriWahyu45 (https://github.com/triwahyu45)
"""

import os
import json
import time

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "Memory_Data")
os.makedirs(MEMORY_DIR, exist_ok=True)

class AinaMemoryStore:
    def __init__(self):
        self.memory_dir = MEMORY_DIR

    def _get_user_file(self, user_id):
        return os.path.join(self.memory_dir, f"user_{user_id}.json")

    def load_user_data(self, user_id):
        """Memuat seluruh arsip obrolan dan profil kepribadian dinamis user."""
        fpath = self._get_user_file(user_id)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MEMORY LOAD ERR] {e}")
        
        # Default data struktur jika user baru
        return {
            "user_id": user_id,
            "created_at": time.time(),
            "last_updated": time.time(),
            "learned_facts": [], # Fakta & preferensi Kak Wahyu yang dipelajari Aina
            "chat_history": []   # Riwayat lengkap percakapan dari awal sampai sekarang
        }

    def save_user_data(self, user_id, data):
        """Menyimpan data percakapan & memori ke disk secara permanen."""
        fpath = self._get_user_file(user_id)
        data["last_updated"] = time.time()
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MEMORY SAVE ERR] {e}")

    def append_message(self, user_id, user_text, model_reply):
        """Menambahkan pesan baru ke riwayat obrolan permanen."""
        data = self.load_user_data(user_id)
        data["chat_history"].append({
            "timestamp": time.time(),
            "user": user_text,
            "aina": model_reply
        })
        self.save_user_data(user_id, data)

    def get_recent_history(self, user_id, max_turns=20):
        """Mengambil N percakapan terakhir untuk context window AI."""
        data = self.load_user_data(user_id)
        chats = data.get("chat_history", [])
        return chats[-max_turns:]

    def get_all_history_summary(self, user_id):
        """Mengambil rangkuman atau daftar seluruh topik yang pernah dibahas."""
        data = self.load_user_data(user_id)
        return data.get("chat_history", [])

    def clear_history(self, user_id):
        """Mereset riwayat tapi tetap mempertahankan memory facts jika ada."""
        data = self.load_user_data(user_id)
        data["chat_history"] = []
        self.save_user_data(user_id, data)

    def update_learned_fact(self, user_id, fact_text):
        """Menambahkan fakta memori baru tentang Kak Wahyu."""
        data = self.load_user_data(user_id)
        if fact_text not in data["learned_facts"]:
            data["learned_facts"].append(fact_text)
            self.save_user_data(user_id, data)
