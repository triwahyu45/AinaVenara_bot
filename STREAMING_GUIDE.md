# 📡 Setup Streaming Pipeline — Aina Venara

---

## 🖥️ Gambaran Pipeline

```
Python Aina App  →  Suara TTS + Emosi
                          ↓
VTube Studio  ←  VRM Aina (avatar)
(avatar renderer)         ↓
                     OBS Studio
                    /          \
             Rekam video    Livestream
                  ↓               ↓
            Edit & Upload      TikTok/YouTube
            TikTok/YT/IG       langsung live
```

---

## LANGKAH 1 — Import VRM ke VTube Studio

**VTube Studio ada di:**
`C:\Program Files (x86)\Steam\steamapps\common\VTube Studio\VTube Studio.exe`

### Import VRM Aina:
1. Buka VTube Studio
2. Klik icon **Settings** (gear icon) di kanan
3. Pilih **Model** → **Select Model**
4. Klik **"+"** → browse ke:
   ```
   %LOCALAPPDATA%\AinaDesktopCompanion\models\Aina_Venara_v28.vrm
   ```
5. Klik model → **Load Model**

### Setup Avatar di VTube Studio:
- **Background**: Set ke **transparent/green screen** (untuk OBS chroma key atau transparan)
  - Settings → General → Background → Pilih "Transparent" atau warna hijau solid
- **Physics**: Enable spring physics untuk rambut agar bergerak natural
- **Face Tracking**: Bisa di-enable (pakai webcam) ATAU di-disable jika tidak mau pakai face tracking
- **Window**: Set ke **"Always on Top"**

---

## LANGKAH 2 — Install & Setup OBS Studio

### Download OBS:
> https://obsproject.com/download (gratis, ~130MB)

### Setelah Install, Buat Scene "Aina Stream":

**Sources (dari bawah ke atas):**

```
📋 Scene: "Aina Stream"
├── 🖼️ Background Image       ← background yang bagus
├── 🎮 Game/Window Capture    ← capture VTube Studio window (avatar Aina)
├── 📝 Text (GDI+)            ← nama "Aina Venara ✨" di pojok
└── 🎵 Audio Output Capture   ← suara dari Aina app
```

### Setup Window Capture:
1. Klik **"+"** di Sources → **Game Capture** atau **Window Capture**
2. Window: pilih **VTube Studio**
3. Enable **"Allow Transparency"** ✅
4. Kalau avatar terlihat dengan background hitam → tambahkan **Chroma Key filter**:
   - Klik kanan source → **Filters** → **"+"** → **Chroma Key**
   - Key Color: sesuaikan dengan background VTube Studio (hijau/biru)

### Setup Audio:
1. Sources → **"+"** → **Audio Output Capture**
2. Device: pilih output audio utama atau "Default"
3. Ini akan capture suara TTS Aina

---

## LANGKAH 3 — Background Scene yang Bagus

Untuk konten yang menarik, buat beberapa background:

### Opsi A: Background Statis
- Gambar anime room aesthetic / bedroom virtual
- Bisa generate dengan AI image generator

### Opsi B: Background Animasi
- Video loop (lo-fi room, café, dll.)
- Di OBS: Source → **VLC Video Source** → pilih video loop

### Opsi C: Transparent (Avatar Float)
- Avatar Aina muncul tanpa background
- Bagus untuk content yang di-overlay di footage lain

---

## LANGKAH 4 — Stream ke TikTok Live

### Syarat TikTok Live:
- Minimal **1.000 followers** atau verifikasi identitas
- Usia akun minimal beberapa hari

### Setup Stream Key TikTok:
1. Di TikTok → **LIVE** → **Go LIVE** → **Cast**
2. Copy **Server URL** dan **Stream Key**
3. Di OBS: **Settings → Stream**
   - Service: **Custom**
   - Server: `rtmp://push.tiktokv.com/live/` (atau dari TikTok)
   - Stream Key: dari TikTok
4. Klik **Start Streaming** di OBS

---

## LANGKAH 5 — Stream/Upload ke YouTube

### Untuk Upload Video:
1. Di OBS: **Start Recording** (simpan sebagai `.mkv` atau `.mp4`)
2. Edit video di editor (CapCut, DaVinci Resolve, dll.)
3. Upload ke YouTube

### Untuk YouTube Livestream:
1. YouTube Studio → **Go Live**
2. Copy Stream Key
3. Di OBS: **Settings → Stream → YouTube - RTMPS**
4. Paste Stream Key → **Start Streaming**

---

## LANGKAH 6 — Koneksi Aina App + VTube Studio

Saat ini, **Aina Python app** berkomunikasi dengan Unity renderer via WebSocket.
Untuk versi dengan VTube Studio, ada beberapa opsi:

### Opsi A: Jalankan Keduanya (Paling Mudah)
- Jalankan **Aina Python app** (untuk AI, TTS, suara)
- Jalankan **VTube Studio** secara terpisah (hanya untuk tampilan avatar)
- Suara Aina tetap keluar dari Python app → OBS capture audio
- Avatar di VTube Studio bisa di-set auto-react ke audio (lipsync by audio level)

### Opsi B: VTube Studio API Integration (Lebih Advanced)
VTube Studio punya API yang bisa diakses dari Python.
Saya bisa tambahkan module `vtube_bridge.py` yang:
- Kirim perintah ekspresi ke VTube Studio via API
- Trigger hotkey expression saat Aina berbicara
- Sync lipsync dengan audio level dari TTS

---

## 🎬 Template Konten

### Konten TikTok/Shorts (15-60 detik):
1. **"Aina React"** — Aina komentar sesuatu yang lucu/trending
2. **"Tanya Aina"** — Q&A singkat satu pertanyaan
3. **"Aina Daily"** — Aina ngobrol santai tentang hari-harinya

### Konten YouTube (5-15 menit):
1. **"Debut Stream"** — Perkenalan Aina pertama kali
2. **"Ngobrol Bareng Aina"** — Live chat session
3. **"Aina Gaming"** — Screen share + komentar Aina

---

## ⚡ Quick Start Checklist

- [ ] VRM Aina v8 sudah selesai dibuat di VRoid Studio
- [ ] VRM berhasil diimport di VTube Studio
- [ ] OBS Studio terinstall dan scene "Aina Stream" sudah dibuat
- [ ] Test: jalankan Aina Python app + VTube Studio + OBS bersamaan
- [ ] Test recording singkat untuk cek kualitas audio/video
- [ ] Upload konten pertama ke TikTok/YouTube!
