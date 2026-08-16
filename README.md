# Aina Venara — AI VTuber & Desktop Companion Bot 🎙️✨

**Aina Venara** adalah AI VTuber dan Desktop Companion mandiri berbasis Windows. Proyek ini menggabungkan kecerdasan buatan multi-modal (**Google Gemini 2.5 Flash**), sistem pengenalan & sintesis suara realtime (**STT & TTS**), integrasi **Avatar 3D VRM**, serta renderer transparan desktop berbasis **Unity**.

---

## 🌟 Fitur Utama

- **AI Brain & Persona (Tsundere-Genki)**: Ditenagai oleh Gemini 2.5 Flash dengan structured JSON responses untuk ucapan, subtitle, dan ekspresi emosi (`senyum`, `marah`, `malu`, `kaget`, `sedih`, `biasa`).
- **Real-Time Voice Streaming**:
  - **Speech-To-Text (STT)**: Menangkap ucapan mikrofon user secara realtime.
  - **Text-To-Speech (TTS)**: Menghasilkan suara natural Aina dengan sinkronisasi lipsync RMS instan.
- **Transparent Desktop Avatar (Unity UniVRM)**:
  - Avatar 3D transparan mengapung di atas desktop Windows tanpa latar belakang.
  - Komunikasi WebSocket lokal (`ws://127.0.0.1:8765/avatar`) untuk kontrol ekspresi, status berpikir/berbicara, dan lipsync.
- **Model 3D Aina Venara (VRM Ready)**:
  - Rambut bob cyan-blue dengan ujung blue-violet dan ahoge ikonik.
  - Kacamata pink round-frame tipis dan hairclip perak angka `3`.
  - Pakaian oversized hoodie cyan-mint off-shoulder, tank top putih, dan celana pendek charcoal.
- **Keamanan & Privasi Maksimal**:
  - API key disimpan aman di **Windows Credential Manager** (tidak pernah ditulis ke file repositori).
  - Tidak ada kredensial pribadi atau token yang masuk ke version control.

---

## 📁 Struktur Repositori

```
AinaVenara_bot/
├── 1. Vtuber AI/                 # Aplikasi Companion (Python) & Unity Avatar Renderer
│   ├── aina_companion/           # Core Python backend (Gemini, Audio, Memory, UI)
│   ├── unity/AinaAvatarRenderer/ # Unity project renderer (UniVRM, UniWindowController)
│   ├── scripts/                  # Script build & scanner keamanan
│   ├── tests/                    # Unit tests pytest (55 passed)
│   ├── setup.cmd / setup.ps1     # Setup environment otomatis
│   └── run.cmd / run.ps1         # Launcher aplikasi
│
├── 2. Aina Venara Model/         # Aset 3D Canonical Aina Venara
│   ├── Modular Output/           # Master blend modular, report geometri
│   ├── Reff 3D HD Generated/     # File referensi visual model
│   └── VRM Draft/                # Model base VRM netral
│
├── 3. VRoid Helper/              # Panduan & Preset VRoid Studio
│   └── VROID_GUIDE_AINA.md       # Panduan kustomisasi slider VRoid
│
├── 4. Blender VRM Builder/       # Otomasi Pipeline Blender & VRM Export
│   ├── scripts/                  # Python build scripts (v21 - v28 perfect)
│   └── output/                   # Model final Aina_Venara_v28.vrm
│
├── Aina_OBS_Scene_Collection.json# Template Scene OBS Studio siap pakai
├── STREAMING_GUIDE.md            # Panduan setup Livestream (OBS & VTube Studio)
└── ANTIGRAVITY_HANDOFF.md        # Catatan teknis pengembangan
```

---

## 🚀 Panduan Memulai Cepat

### 1. Prasyarat Sistem
- Windows 10 / 11 (64-bit)
- Python 3.12 (pastikan centang `Add python.exe to PATH`)
- [Unity 2022.3 LTS](https://unity.com/download) (opsional jika ingin me-rebuild renderer)
- [OBS Studio](https://obsproject.com/) (opsional jika ingin streaming)

### 2. Instalasi & Setup Backend Python
1. Buka folder `1. Vtuber AI`.
2. Jalankan `setup.cmd` (atau `setup.ps1` via PowerShell).
3. Jalankan `run.cmd` atau `Launch Aina.vbs` untuk membuka Aina Desktop Companion.
4. Buka menu **Settings > Gemini API**, masukkan Gemini API Key Anda, lalu klik **Test Profile**.

### 3. Memuat Model Avatar 3D
1. Buka **Settings > Avatar 3D**.
2. Pilih file model final `4. Blender VRM Builder/output/Aina_Venara_v28.vrm`.
3. Avatar 3D Aina akan langsung muncul dan siap diajak mengobrol!

---

## 🔒 Privasi dan Keamanan

Repositori ini menerapkan aturan keamanan ketat:
- Seluruh file `.env`, `settings.json`, token lokal, database SQLite `memory.sqlite3`, dan cache audio diabaikan oleh `.gitignore`.
- Jalankan scanner keamanan lokal kapan saja dengan:
  ```powershell
  python "1. Vtuber AI\scripts\secret_scan.py"
  ```

---

## 📜 Lisensi & Atribusi
- Dibuat untuk proyek AI VTuber Aina Venara.
- Menggunakan komponen open-source: UniVRM (MIT), UniWindowController (MIT), NativeWebSocket, google-genai SDK, PySide6.
