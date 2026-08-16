# Aina VRoid Helper

Helper lokal terawasi untuk memandu navigasi VRoid Studio dan Blender. Helper ini
bukan remote desktop agent: ia hanya menyorot target. Semua klik tetap dilakukan user.

## Setup

1. Jalankan `setup.cmd`.
2. Buka `Launch VRoid Helper.vbs`.
3. Klik `Launch VRoid`.
4. Buka project `..\2. Aina Venara Model\Vroid Project\Aina_Venara.vroid`.
5. Aktifkan `Authoring: ON`.
6. Hover elemen VRoid yang ingin direkam lalu tekan `Ctrl+Alt+C`.
7. Isi label singkat target. Ulangi untuk urutan guide.
8. Klik `Start overlay`. Controller mengecil dan highlight tampil di atas VRoid.
9. Klik target secara manual. Helper menyimpan checkpoint lalu maju ke target berikutnya.
10. Tekan `Esc` kapan saja untuk menutup overlay.

## Batas Aman

- Helper tidak menggerakkan mouse atau melakukan klik.
- Helper tidak mengetik, tidak membaca clipboard, tidak upload jaringan, dan tidak menyimpan credential.
- Export, overwrite, penyimpanan project, dan penutupan aplikasi selalu manual.
- Overlay mengikuti posisi dan ukuran window target.
- Screenshot dan log hanya disimpan di `runtime/`, yang diabaikan Git.

## Hotkey

- `Ctrl+Alt+C`: rekam target dari posisi cursor saat authoring aktif.
- `Ctrl+Alt+N`: maju manual.
- `Ctrl+Alt+B`: kembali satu target.
- `Ctrl+Alt+G`: buka galeri checkpoint.
- `Esc`: stop overlay.

## Workflow Aina

Gunakan reference:
`..\2. Aina Venara Model\Reff 3D\Aina_Venara_3D_Turnaround.png`.

Bangun base wajah, rambut, dan outfit di VRoid. Export draft VRM secara manual. Gunakan
Blender untuk jepit rambut angka `3`, koreksi hoodie, dan detail mesh sebelum export
final.
