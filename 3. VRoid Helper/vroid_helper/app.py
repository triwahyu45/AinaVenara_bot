from __future__ import annotations

import ctypes
import threading
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from pynput import keyboard, mouse

from .core import (
    CHECKPOINT_DIR,
    AuditLog,
    GuideItem,
    SafetyError,
    WindowInfo,
    WindowLocator,
    capture_window,
    checkpoint_path,
    contains_click,
    launch_target,
    load_guides,
    open_folder,
    record_guide,
    save_guides,
)

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000


class OverlayWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="black")
        self.attributes("-transparentcolor", "black")
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def show_item(self, window: WindowInfo, item: GuideItem, index: int, total: int) -> None:
        self.geometry(f"{window.width}x{window.height}+{window.left}+{window.top}")
        self.canvas.configure(width=window.width, height=window.height)
        self.canvas.delete("all")
        x, y = round(item.x * window.width), round(item.y * window.height)
        radius = item.radius
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="#ff3b81", width=5)
        self.canvas.create_line(x - 130, y - 85, x - 30, y - 22, fill="#ff3b81", width=5, arrow=tk.LAST)
        self.canvas.create_text(
            max(180, x - 150),
            max(36, y - 112),
            text=f"{index + 1}/{total}  {item.label}",
            fill="white",
            font=("Segoe UI", 15, "bold"),
            anchor=tk.CENTER,
        )
        self.deiconify()
        self.update_idletasks()
        hwnd = self.winfo_id()
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        )

    def hide_overlay(self) -> None:
        self.withdraw()


class GalleryWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Aina checkpoint gallery")
        self.geometry("760x560")
        self.files: list[Path] = []
        self.photo: tk.PhotoImage | None = None
        controls = ttk.Frame(self, padding=8)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="Refresh", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(controls, text="Open folder", command=lambda: open_folder(CHECKPOINT_DIR)).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Delete selected", command=self.delete_selected).pack(side=tk.LEFT)
        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)
        self.listbox = tk.Listbox(left, exportselection=False)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self.show_selected())
        self.preview = ttk.Label(right, text="Pilih checkpoint.", anchor=tk.CENTER)
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.refresh()

    def refresh(self) -> None:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        self.files = sorted(CHECKPOINT_DIR.glob("*.png"), reverse=True)
        self.listbox.delete(0, tk.END)
        for path in self.files:
            self.listbox.insert(tk.END, path.name)
        if self.files:
            self.listbox.selection_set(0)
            self.show_selected()

    def selected(self) -> Path | None:
        rows = self.listbox.curselection()
        return self.files[rows[0]] if rows else None

    def show_selected(self) -> None:
        selected = self.selected()
        if selected:
            self.photo = tk.PhotoImage(file=str(selected))
            self.preview.configure(image=self.photo, text="")

    def delete_selected(self) -> None:
        selected = self.selected()
        if selected and messagebox.askyesno("Delete checkpoint", f"Hapus {selected.name}?"):
            selected.unlink()
            self.refresh()


class HelperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aina VRoid Guide")
        self.geometry("500x520")
        self.locator = WindowLocator()
        self.log = AuditLog()
        self.guides = load_guides()
        self.index = 0
        self.running = False
        self.authoring = False
        self.expected_window: WindowInfo | None = None
        self.overlay = OverlayWindow(self)
        self.gallery: GalleryWindow | None = None
        self.status = tk.StringVar(value="Rekam target dengan Ctrl+Alt+C atau mulai guide.")
        self._build()
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.mouse_listener.start()
        self.hotkeys = keyboard.GlobalHotKeys(
            {
                "<ctrl>+<alt>+c": self._schedule_record,
                "<ctrl>+<alt>+n": lambda: self.after(0, self.next_item),
                "<ctrl>+<alt>+b": lambda: self.after(0, self.previous_item),
                "<ctrl>+<alt>+g": lambda: self.after(0, self.open_gallery),
                "<esc>": lambda: self.after(0, self.stop),
            }
        )
        self.hotkeys.start()
        self.after(250, self._refresh_overlay)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self) -> None:
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Launch VRoid", command=lambda: launch_target("vroid")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Launch Blender", command=lambda: launch_target("blender")).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Gallery", command=self.open_gallery).pack(side=tk.RIGHT)
        settings = ttk.LabelFrame(self, text="Target authoring", padding=8)
        settings.pack(fill=tk.X, padx=8)
        self.target = tk.StringVar(value="vroid")
        ttk.Radiobutton(settings, text="VRoid", variable=self.target, value="vroid").pack(side=tk.LEFT)
        ttk.Radiobutton(settings, text="Blender", variable=self.target, value="blender").pack(side=tk.LEFT)
        self.authoring_button = ttk.Button(settings, text="Authoring: OFF", command=self.toggle_authoring)
        self.authoring_button.pack(side=tk.RIGHT)
        ttk.Label(self, text="Hover target lalu tekan Ctrl+Alt+C untuk merekam highlight.", padding=8).pack(fill=tk.X)
        self.listbox = tk.Listbox(self, exportselection=False, height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=8)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self.select_index())
        controls = ttk.Frame(self, padding=8)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="Start overlay", command=self.start).pack(side=tk.LEFT)
        ttk.Button(controls, text="Pause", command=self.stop).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Back", command=self.previous_item).pack(side=tk.LEFT)
        ttk.Button(controls, text="Next", command=self.next_item).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Delete target", command=self.delete_item).pack(side=tk.RIGHT)
        ttk.Label(self, textvariable=self.status, wraplength=470, padding=(8, 0, 8, 8)).pack(fill=tk.X)
        self.refresh_list()

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for index, item in enumerate(self.guides):
            marker = ">> " if self.running and index == self.index else ""
            self.listbox.insert(tk.END, f"{marker}{index + 1}. [{item.target}] {item.label}")

    def toggle_authoring(self) -> None:
        self.authoring = not self.authoring
        self.authoring_button.configure(text=f"Authoring: {'ON' if self.authoring else 'OFF'}")
        self.status.set("Authoring ON: hover elemen target lalu tekan Ctrl+Alt+C." if self.authoring else "Authoring OFF.")

    def _schedule_record(self) -> None:
        self.after(0, self.record_hover_target)

    def record_hover_target(self) -> None:
        if not self.authoring:
            self.status.set("Aktifkan Authoring sebelum merekam target.")
            return
        window = self.locator.find(self.target.get())
        if not window:
            messagebox.showwarning("Window belum ada", "Window target belum ditemukan.")
            return
        cursor = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor))
        label = simpledialog.askstring("Label target", "Instruksi singkat untuk target ini:", parent=self)
        if not label:
            return
        try:
            item = record_guide(label=label, target=self.target.get(), cursor_x=cursor.x, cursor_y=cursor.y, window=window)
            self.guides.append(item)
            save_guides(self.guides)
            self.refresh_list()
            self.status.set(f"Target tersimpan: {item.label}")
        except Exception as error:
            messagebox.showerror("Target tidak tersimpan", str(error))

    def start(self) -> None:
        if not self.guides:
            messagebox.showinfo("Guide kosong", "Rekam target pertama dengan Ctrl+Alt+C.")
            return
        self.running = True
        self.index = min(self.index, len(self.guides) - 1)
        self.show_current()
        self.iconify()

    def stop(self) -> None:
        self.running = False
        self.expected_window = None
        self.overlay.hide_overlay()
        self.refresh_list()
        self.status.set("Overlay dihentikan.")

    def show_current(self) -> None:
        if not self.running or not self.guides:
            return
        item = self.guides[self.index]
        window = self.locator.find(item.target)
        if not window:
            self.stop()
            messagebox.showwarning("Window hilang", f"Window {item.target} tidak ditemukan.")
            return
        self.expected_window = window
        self.overlay.show_item(window, item, self.index, len(self.guides))
        self.log.write("highlight", index=self.index, item=item.id, target=item.target)
        self.refresh_list()

    def _refresh_overlay(self) -> None:
        if self.running and self.expected_window:
            item = self.guides[self.index]
            window = self.locator.find(item.target)
            if not window:
                self.stop()
            elif window.signature != self.expected_window.signature:
                self.expected_window = window
                self.overlay.show_item(window, item, self.index, len(self.guides))
        self.after(250, self._refresh_overlay)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not pressed or button != mouse.Button.left or not self.running or not self.expected_window:
            return
        item = self.guides[self.index]
        if contains_click(item, self.expected_window, x, y):
            self.log.write("target_clicked", index=self.index, item=item.id, x=x, y=y)
            self.after(item.capture_delay_ms, lambda: self.capture_and_next(item))

    def capture_and_next(self, item: GuideItem) -> None:
        window = self.locator.find(item.target)
        if not self.running or not window:
            return
        destination = checkpoint_path(item, self.index)
        capture_window(window, destination)
        self.log.write("checkpoint", index=self.index, item=item.id, path=str(destination))
        self.next_item()

    def next_item(self) -> None:
        if not self.guides:
            return
        if self.index + 1 >= len(self.guides):
            self.stop()
            self.deiconify()
            self.status.set("Guide selesai. Buka Gallery untuk melihat checkpoint.")
            return
        self.index += 1
        if self.running:
            self.show_current()
        self.refresh_list()

    def previous_item(self) -> None:
        if self.guides:
            self.index = max(0, self.index - 1)
            if self.running:
                self.show_current()
            self.refresh_list()

    def select_index(self) -> None:
        rows = self.listbox.curselection()
        if rows:
            self.index = rows[0]
            if self.running:
                self.show_current()

    def delete_item(self) -> None:
        rows = self.listbox.curselection()
        if rows and messagebox.askyesno("Delete target", "Hapus target guide terpilih?"):
            self.guides.pop(rows[0])
            save_guides(self.guides)
            self.index = min(self.index, max(0, len(self.guides) - 1))
            self.refresh_list()

    def open_gallery(self) -> None:
        if self.gallery and self.gallery.winfo_exists():
            self.gallery.lift()
        else:
            self.gallery = GalleryWindow(self)

    def close(self) -> None:
        self.stop()
        self.mouse_listener.stop()
        self.hotkeys.stop()
        self.destroy()


def main() -> None:
    HelperApp().mainloop()


if __name__ == "__main__":
    main()
