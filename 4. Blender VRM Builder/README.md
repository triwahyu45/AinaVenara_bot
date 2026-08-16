# Aina Blender VRM Builder

Builder ini membuat avatar Aina dari base VRoid netral lalu mengekspor `.vrm`
langsung untuk renderer desktop. Seed-san hanya model demo dan sengaja ditolak
sebagai input Aina karena membawa lengan robot, backpack, dan outfit yang salah.

## Export VRoid Sekali

1. Klik `open_vroid_export.cmd`.
2. Di VRoid Studio pilih `Export as VRM`.
3. Gunakan VRM 1.0 bila tersedia.
4. Simpan sebagai:
   `..\2. Aina Venara Model\VRM Draft\Aina_Venara_Base.vrm`

Setelah itu VRoid tidak diperlukan untuk iterasi rutin.

## Build dan Preview

1. Klik `build_aina_v1.cmd`.
2. Builder mengimpor base netral, menolak artifact robot, membangun detail Aina,
   mengekspor VRM, melakukan re-import validation, dan merender contact sheet.
3. Preview kandidat default berada di `output\previews\Aina_Venara_v6_contact_sheet.png`.
4. Klik `open_workbench_v1.cmd` untuk membuka file kerja Blender.

Komponen prosedural awal:

- bob cyan dengan ujung biru-ungu, poni, side locks, dan ahoge;
- kacamata pink dan hairclip angka `3`;
- hoodie cyan-mint off-shoulder, collar dan cuffs charcoal;
- shorts gelap, socks putih, dan sneakers putih.

## Install ke Desktop Companion

Setelah preview disetujui, klik `install_aina_v1.cmd`. Kandidat v6 disalin ke
`%LOCALAPPDATA%\AinaDesktopCompanion\models` dan `model_path` settings lokal
diperbarui. API key tidak disentuh.

## Referensi

Turnaround:

`..\2. Aina Venara Model\Reff 3D\Aina_Venara_3D_Turnaround.png`

Addon:

[VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender)

## HD Overlay Fitting

The non-destructive fitting mode compares v6 against the 45 clean individual
references in `..\2. Aina Venara Model\Reff 3D HD Generated Individual`.

Run `run_fit.cmd` to render locked orthographic views and archive each iteration
under `output\fitting\v6`. Each iteration contains render PNG files, 50 percent
overlays, edge-diff diagnostics, metrics, and a parameter snapshot. Review
`output\fitting\v6\best\overlay_contact_sheet.png` before installing a candidate.
