# Aina Desktop Companion

Aina adalah AI companion Windows dengan avatar 3D VRM mandiri. Python menangani
Gemini, STT, TTS, memory lokal, serta API failover. Unity menampilkan avatar transparan
di desktop tanpa VTube Studio, Live2D, webcam, atau tracker wajah.

## Setup Python

1. Install Python 3.12 x64 dan aktifkan `Add python.exe to PATH`.
2. Jalankan `setup.cmd`.
3. Jalankan `Launch Aina.vbs` agar Aina terbuka tanpa jendela CMD.
4. Aktifkan `Advanced settings`, buka `Gemini API`, tambah replacement key baru, lalu test profile.

API key disimpan melalui Windows Credential Manager. `.env` hanya didukung sebagai
jalur impor migrasi satu kali. Jika Python pernah dipindahkan, `setup.cmd` akan
membangun ulang `.venv` yang rusak.

## Setup Google Cloud STT

Mic realtime memakai Google Cloud Speech-to-Text streaming, bukan key Gemini dan bukan
endpoint speech gratis. Aktifkan Speech-to-Text API pada project Google Cloud, buat
service account dengan izin minimum untuk STT, lalu simpan credential JSON di luar
folder proyek. Pilih file tersebut melalui `Settings > Audio`.

Credential JSON tidak boleh dimasukkan ke Git. Jika environment sudah memakai
Application Default Credentials, field credential boleh dikosongkan.

## Setup Unity Renderer

1. Install [Unity Hub](https://unity.com/download).
2. Dari Hub, install Unity `2022.3 LTS` dan modul Windows Build Support.
3. Jalankan `scripts\build_unity_renderer.cmd`.
4. Jalankan `run.cmd`, lalu buka `Settings > Avatar 3D`.
5. Gunakan tombol download model demo Seed-san atau pilih `.vrm` hasil VRoid Studio.

Renderer memakai [UniVRM v0.131.0](https://github.com/vrm-c/UniVRM/releases/tag/v0.131.0),
[UniWindowController](https://github.com/kirurobo/UniWindowController), dan
[NativeWebSocket](https://github.com/endel/NativeWebSocket). Hasil build lokal, model
VRM, database, cache audio, dan key tidak masuk Git.

Model demo Seed-san diunduh ke `%LOCALAPPDATA%\AinaDesktopCompanion\models` dari
[mirror sample VRM](https://github.com/madjin/vrm-samples/tree/master/Seed-san) setelah
konfirmasi notice [VRM Public License 1.0](https://vrm.dev/en/licenses/1.0/).

## Avatar 3D

Python membuka WebSocket lokal `ws://127.0.0.1:8765/avatar`. Unity reconnect otomatis
dan menerima event state, emosi, lipsync RMS, subtitle bubble, konfigurasi window, serta
path model VRM. Default performa memakai 30 FPS, shadow minimal, dan satu directional
light agar ringan untuk integrated GPU.

Tampilan harian hanya berupa avatar pop-out dan chat mini. Ikon mikrofon berwarna hijau
saat listening dan merah saat mute. Settings lanjutan, API health, path model, memory,
serta diagnostics disembunyikan di balik toggle `Advanced settings`.

Melalui `Settings > General`, Aina dapat dibuat berjalan otomatis saat login Windows
atau dibuatkan shortcut Desktop. Keduanya memakai `pythonw.exe`, sehingga tidak membuka
jendela CMD.

Ekspresi dasar: idle, speaking, thinking, senyum, sedih, marah dengan moshing ringan,
kaget, dan malu. Folder `%LOCALAPPDATA%\AinaDesktopCompanion\animations` disiapkan
untuk template `.vrma` tahap lanjut.

## Test dan Privasi

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\secret_scan.py
```

Unity EditMode tests tersedia dalam project renderer. Jalankan melalui Unity Test
Runner setelah Unity Editor `2022.3 LTS` terpasang. Key plaintext lama tetap harus
di-revoke dan diganti; aplikasi tidak memulihkan key lama dari file proyek.
