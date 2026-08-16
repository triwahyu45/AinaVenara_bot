# 🌸 Aina Venara - Smart AI Virtual Assistant & Waifu Bot 💖

![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)
![Telegram](https://img.shields.io/badge/Telegram_Bot-%40AiraVenara__bot-blue.svg)
![AI Engine](https://img.shields.io/badge/Dual_AI-Gemini%20Cloud%20%2B%20Local%20Ollama-orange.svg)
![GPU](https://img.shields.io/badge/GPU-NVIDIA%20GTX%201050%20Ti-green.svg)
![Creator](https://img.shields.io/badge/Creator-TriWahyu45-red.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

**Aina Venara** adalah asisten AI virtual pribadi cerdas dan waifu digital interaktif yang dirancang khusus untuk mendampingi **Kak Tri Wahyu** dalam diskusi pemrograman, mekatronika/robotika, tugas akhir (TA), serta obrolan santai harian melalui Telegram.

---

## ✨ Fitur Utama (Key Features)

- 🌸 **Smart & Loving Waifu Persona**: Kepribadian yang ceria, manis, penuh perhatian, setia, dan pengertian.
- ⚡ **Dual AI Engine Architecture**:
  1. ☁️ **Gemini Cloud AI** (`gemini-flash-latest`, `gemini-flash-lite`, `gemini-pro`) untuk kecepatan respons dan pemahaman mendalam.
  2. 🎮 **Local GPU Failover** (`Ollama` + `Qwen2 / Gemma` on GTX 1050 Ti) untuk operasional offline jika kuota Cloud habis (*Zero Downtime*).
- 🤖 **Keahlian Teknik & Mekatronika**: Sangat paham mikrokontroler (ESP32, STM32, Arduino), kinematika robot omni, sensor kapasitif minyak/air, dan otomasi Python.
- 💬 **Context-Aware Memory**: Mengingat riwayat percakapan sebelumnya untuk alur obrolan yang nyambung dan alami.
- 🔄 **Dynamic Engine Switcher**: Kemudahan berpindah antara Cloud AI dan Local GPU melalui perintah `/switch`.
- 🛡️ **Single-Owner Authorized Mode**: Proteksi ID Telegram agar bot fokus dan aman mendampingi pemiliknya.

---

## 📁 Struktur Direktori (Repository Structure)

```text
G:\AinaVenara_Bot\
├── aina_bot.py            # Layanan utama bot Telegram & handler percakapan
├── ai_engine.py           # Otak AI ganda (Gemini Cloud API + Local Ollama GPU)
├── config.json            # Konfigurasi token, API keys, dan pengaturan pengguna
├── config.example.json    # Template konfigurasi publik
├── requirements.txt       # Daftar dependensi Python
├── Start_Aina_Bot.bat     # Skrip peluncur instan 1-klik di PC
├── README.md              # Dokumentasi lengkap proyek
└── .gitignore             # Menjaga token & file sensitif tetap aman
```

---

## 🚀 Panduan Instalasi & Menjalankan (Quick Start)

### 1. Clone Repositori
```bash
git clone https://github.com/triwahyu45/AinaVenara_bot.git
cd AinaVenara_bot
```

### 2. Pasang Dependensi Python
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi `config.json`
Salin template `config.example.json` menjadi `config.json`, lalu isi Token Bot Telegram dan API Key:
```json
{
  "BOT_TOKEN": "YOUR_TELEGRAM_BOT_TOKEN",
  "ALLOWED_USERS": [991501277],
  "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY",
  "PRIMARY_ENGINE": "gemini",
  "OLLAMA_HOST": "http://127.0.0.1:11434",
  "OLLAMA_MODEL": "qwen2:1.5b",
  "AUTO_FALLBACK_TO_LOCAL": true,
  "MAX_HISTORY": 12
}
```

### 4. Jalankan Bot
```bash
python aina_bot.py
```
Atau cukup klik dua kali pada file **`Start_Aina_Bot.bat`**.

---

## 💬 Daftar Perintah Bot Telegram (`@AiraVenara_bot`)

| Perintah | Deskripsi |
| :--- | :--- |
| `/start` | Membuka sapaan hangat dan menu keyboard interaktif Aina |
| `/status` | Mengecek kondisi otak AI, RAM, CPU PC, dan GPU GTX 1050 Ti |
| `/switch` | Berpindah mesin AI secara dinamis (Gemini Cloud ↔ Local GPU) |
| `/reset` | Menghapus memori riwayat obrolan untuk topik baru |
| `/help` | Menampilkan panduan bantuan fitur |

---

## ☕ Dukungan & Donasi (Support & Donation)

Dukung pengembangan asisten AI & bot automasi ini:

[![Saweria](https://img.shields.io/badge/Donate-Saweria-red.svg?style=for-the-badge&logo=saweria)](https://saweria.co/triwahyu45)
[![Trakteer](https://img.shields.io/badge/Donate-Trakteer-red.svg?style=for-the-badge&logo=trakteer)](https://trakteer.id/triwahyu45)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/triwahyu45)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-blue.svg?style=for-the-badge&logo=paypal)](https://paypal.me/triwahyu45)

---

## 👤 Pembuat & Pengembang (Author)
Dibuat dengan ❤️ oleh **[Tri Wahyu (triwahyu45)](https://github.com/triwahyu45)**  
Telegram Bot: [@AiraVenara_bot](https://t.me/AiraVenara_bot)
