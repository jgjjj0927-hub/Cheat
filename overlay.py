# language: python, file: overlay.py — прозрачный оверлей + меню
import tkinter as tk
import cheat


class Overlay:
    def __init__(self, root):
        self.root = root
        self.visible = False
        self.menu_visible = False

        # оверлей — прозрачный по чёрному
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", "black")
        self.win.configure(bg="black")
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{sw}x{sh}+0+0")
        self.canvas = tk.Canvas(self.win, width=sw, height=sh, bg="black",
                                highlightthickness=0)
        self.canvas.pack()
        self.win.withdraw()

        # меню — обычное окно (без overrideredirect, чтобы чекбоксы кликались)
        self.menu = tk.Toplevel(root)
        self.menu.title("CS&SOFT")
        self.menu.attributes("-topmost", True)
        self.menu.configure(bg="#1e1e1e")
        self.menu.geometry("360x600+20+20")
        self.menu.withdraw()

        self.checks = {}
        self._build_menu()

    def _build_menu(self):
        header = tk.Label(self.menu, text="CS&SOFT", fg="#00ff88", bg="#1e1e1e",
                          font=("Segoe UI", 14, "bold"))
        header.pack(pady=(10, 2))

        self.status = tk.Label(self.menu, text="waiting for cs2.exe",
                               fg="#ff8800", bg="#1e1e1e", font=("Segoe UI", 9))
        self.status.pack(pady=(0, 8))

        def add_check(parent, key, text, default):
            var = tk.BooleanVar(value=cheat.CFG.get(key, default))
            cb = tk.Checkbutton(parent, text=text, variable=var,
                                fg="#ffffff", bg="#1e1e1e",
                                selectcolor="#333333",
                                activebackground="#1e1e1e",
                                activeforeground="#00ff88",
                                font=("Segoe UI", 9),
                                command=lambda k=key, v=var: self._on_toggle(k, v))
            cb.pack(anchor="w", padx=10)
            self.checks[key] = var

        esp = tk.LabelFrame(self.menu, text="ESP", fg="#00ff88", bg="#1e1e1e",
                            font=("Segoe UI", 9, "bold"))
        esp.pack(fill="x", padx=8, pady=4)
        for k, t, d in [
            ("esp_enabled", "Enable ESP", True),
            ("esp_box", "Box", True),
            ("esp_name", "Name", True),
            ("esp_distance", "Distance", True),
            ("esp_health", "Health", True),
            ("esp_team", "Show teammates", False),
        ]:
            add_check(esp, k, t, d)

        radar = tk.LabelFrame(self.menu, text="Radar", fg="#00ff88", bg="#1e1e1e",
                              font=("Segoe UI", 9, "bold"))
        radar.pack(fill="x", padx=8, pady=4)
        add_check(radar, "radar_enabled", "Enable Radar", True)

        trig = tk.LabelFrame(self.menu, text="Triggerbot", fg="#00ff88", bg="#1e1e1e",
                             font=("Segoe UI", 9, "bold"))
        trig.pack(fill="x", padx=8, pady=4)
        add_check(trig, "trigger_enabled", "Enable Trigger", False)

        move = tk.LabelFrame(self.menu, text="Movement", fg="#00ff88", bg="#1e1e1e",
                             font=("Segoe UI", 9, "bold"))
        move.pack(fill="x", padx=8, pady=4)
        add_check(move, "bhop_enabled", "Bunnyhop", False)
        add_check(move, "no_recoil", "No recoil", False)

        tip = tk.Label(self.menu, text="Insert — toggle menu", fg="#888888",
                       bg="#1e1e1e", font=("Segoe UI", 8))
        tip.pack(side="bottom", pady=8)

    def _on_toggle(self, key, var):
        cheat.CFG[key] = var.get()
        cheat.save_config()

    def toggle_menu(self):
        self.menu_visible = not self.menu_visible
        if self.menu_visible:
            self.menu.deiconify()
            self.menu.lift()
            self.menu.focus_force()
        else:
            self.menu.withdraw()

    def show(self):
        if not self.visible:
            self.win.deiconify()
            self.visible = True

    def hide(self):
        if self.visible:
            self.win.withdraw()
            self.visible = False

    def update(self):
        try:
            with cheat.overlay_lock:
                data = {
                    "boxes": list(cheat.overlay_data["boxes"]),
                    "texts": list(cheat.overlay_data["texts"]),
                    "radar": list(cheat.overlay_data["radar"]),
                    "ready": cheat.overlay_data["ready"],
                    "pid": cheat.overlay_data["pid"],
                }
            if data["ready"]:
                self.status.config(text=f"attached: pid {data['pid']}", fg="#00ff88")
                if not self.visible:
                    self.show()
            else:
                self.status.config(text="waiting for cs2.exe", fg="#ff8800")
                if self.visible:
                    self.hide()

            self.canvas.delete("all")
            if self.visible and data["ready"]:
                if cheat.CFG.get("esp_enabled", True):
                    for (x1, y1, x2, y2, hp) in data["boxes"]:
                        self.canvas.create_rectangle(x1, y1, x2, y2,
                                                     outline="#ff3333", width=2)
                        if cheat.CFG.get("esp_health", True):
                            frac = max(0.0, min(1.0, hp / 100.0))
                            bar_h = (y2 - y1) * frac
                            self.canvas.create_rectangle(
                                x1 - 6, y2 - bar_h, x1 - 3, y2,
                                fill="#ff3333", outline="")
                for (x, y, txt) in data["texts"]:
                    self.canvas.create_text(x, y, text=txt, fill="#ff6666",
                                            font=("Consolas", 10), anchor="nw")
                if cheat.CFG.get("radar_enabled", True):
                    cx, cy, r = 70, 70, 55
                    self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                            outline="#00ff88", width=1)
                    self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2,
                                            fill="#00ff88")
                    for (rx, ry, friendly) in data["radar"]:
                        color = "#00ff00" if friendly else "#ff3333"
                        self.canvas.create_oval(cx + rx - 2, cy + ry - 2,
                                                cx + rx + 2, cy + ry + 2,
                                                fill=color, outline="")
        except Exception:
            pass

        self.root.after(50, self.update)
