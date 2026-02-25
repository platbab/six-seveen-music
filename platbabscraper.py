import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
import os
import re
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MusicDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Platbab Music Scraper")
        self.geometry("900x850")

        if os.name == 'nt':
            self.default_config = os.path.join(os.getenv('APPDATA'), "streamrip", "config.toml")
        else:
            self.default_config = os.path.expanduser("~/.config/streamrip/config.toml")

        self.config_path_var = tk.StringVar(value=self.default_config)
        self.status_var = tk.StringVar(value="Status: Ready")
        self.dl_path_var = tk.StringVar(value="Loading...")
        self.thread_count_var = tk.IntVar(value=4)
        self.source_var = ctk.StringVar(value="qobuz")

        self.ui_lock = threading.Lock()
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Platbab Ripper", font=ctk.CTkFont(size=32, weight="bold"))
        self.title_label.pack(pady=(30, 5))
        self.desc_label = ctk.CTkLabel(self, text="True Lossless Extraction", text_color="gray60")
        self.desc_label.pack(pady=(0, 20))

        self.card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=20, border_width=1, border_color="#333333")
        self.card.pack(pady=10, padx=30, fill="x")

        ctk.CTkLabel(self.card, text="Streamrip Config:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.cfg_entry = ctk.CTkEntry(self.card, textvariable=self.config_path_var, width=450)
        self.cfg_entry.grid(row=0, column=1, pady=(20, 10), padx=5)
        self.cfg_btn = ctk.CTkButton(self.card, text="Locate", width=80, command=self.browse_config, fg_color="#3d3d3d")
        self.cfg_btn.grid(row=0, column=2, padx=20, pady=(20, 10))

        ctk.CTkLabel(self.card, text="Download Path:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.dl_entry = ctk.CTkEntry(self.card, textvariable=self.dl_path_var, width=450)
        self.dl_entry.grid(row=1, column=1, pady=10, padx=5)
        self.dl_btn = ctk.CTkButton(self.card, text="Browse", width=80, command=self.browse_dl, fg_color="#3d3d3d")
        self.dl_btn.grid(row=1, column=2, padx=20, pady=10)

        self.sub_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.sub_frame.grid(row=2, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")

        ctk.CTkLabel(self.sub_frame, text="Parallel Threads:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        self.t_entry = ctk.CTkEntry(self.sub_frame, textvariable=self.thread_count_var, width=50)
        self.t_entry.pack(side="left", padx=10)

        ctk.CTkLabel(self.sub_frame, text="Source:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(30, 5))
        self.src_opt = ctk.CTkOptionMenu(self.sub_frame, values=["qobuz", "tidal"], variable=self.source_var, width=100)
        self.src_opt.pack(side="left", padx=10)

        self.auto_switch = ctk.CTkSwitch(self.sub_frame, text="Auto-Select Result", onvalue=True, offvalue=False)
        self.auto_switch.select()
        self.auto_switch.pack(side="left", padx=30)

        self.save_btn = ctk.CTkButton(self.sub_frame, text="APPLY SETTINGS", fg_color="#27ae60", hover_color="#1e8449", command=self.save_settings, width=150, font=ctk.CTkFont(weight="bold"))
        self.save_btn.pack(side="right", padx=5)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste Link (Spotify / Apple / YouTube)...", width=700, height=50, font=ctk.CTkFont(size=14))
        self.url_entry.pack(pady=30)

        self.rip_btn = ctk.CTkButton(self, text="INITIALIZE RIP ENGINE", command=self.start_thread, font=ctk.CTkFont(size=18, weight="bold"), height=65, fg_color="#C70039", hover_color="#900C3F", corner_radius=10)
        self.rip_btn.pack(pady=10)

        self.console = ctk.CTkTextbox(self, width=840, height=220, font=ctk.CTkFont(family="Consolas", size=12), border_width=1, border_color="#333333")
        self.console.pack(pady=20, padx=30)

        self.status_lbl = ctk.CTkLabel(self, textvariable=self.status_var, text_color="#3498db", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(pady=10)

    def log(self, msg):
        with self.ui_lock:
            self.console.insert("end", f"> {msg}\n")
            self.console.see("end")

    def browse_config(self):
        path = filedialog.askopenfilename(filetypes=[("TOML files", "*.toml")])
        if path: self.config_path_var.set(path); self.load_config_values()

    def browse_dl(self):
        path = filedialog.askdirectory()
        if path: self.dl_path_var.set(path)

    def load_config_values(self):
        p = self.config_path_var.get()
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    content = f.read()
                    m = re.search(r'folder\s*=\s*"(.*?)"', content)
                    if m: self.dl_path_var.set(m.group(1))
            except: pass

    def save_settings(self):
        p = self.config_path_var.get()
        new_dl = self.dl_path_var.get()
        if not os.path.exists(p): return
        try:
            with open(p, "r") as f: lines = f.readlines()
            with open(p, "w") as f:
                for line in lines:
                    if line.strip().startswith("folder ="): f.write(f'folder = "{new_dl}"\n')
                    else: f.write(line)
            self.log("Settings synchronized.")
            messagebox.showinfo("Success", "Settings Applied.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def start_thread(self):
        url = self.url_entry.get()
        if not url: return
        self.rip_btn.configure(state="disabled")
        threading.Thread(target=self.run_engine, args=(url,), daemon=True).start()

    def run_engine(self, url):
        try:
            auto = self.auto_switch.get()
            tracks = []
            if "youtube.com" in url or "youtu.be" in url:
                tracks = self.parse_yt(url)
            elif "spotify.com" in url:
                tracks = self.parse_sp(url)
            elif "apple.com" in url:
                tracks = self.parse_ap(url)
            else:
                self.exec_direct(url)
                return

            if not tracks:
                self.log("Metadata extraction failed.")
                return

            workers = self.thread_count_var.get()
            if auto:
                with ThreadPoolExecutor(max_workers=workers) as exe:
                    exe.map(self.dl_auto, tracks)
            else:
                for t in tracks: self.dl_manual(t)

        except Exception as e: self.log(f"ERROR: {e}")
        finally:
            self.rip_btn.configure(state="normal")
            self.status_var.set("Status: Job Finished")

    def parse_yt(self, url):
        from ytmusicapi import YTMusic
        try:
            yt = YTMusic(); m = re.search(r"list=([^&]+)", url)
            if m:
                d = yt.get_playlist(m.group(1))
                return [f"{t['artists'][0]['name']} - {t['title']}" for t in d['tracks']]
        except: return []
        return []

    def parse_sp(self, url):
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            matches = re.findall(r'\"name\":\"(.*?)\"', r.text)
            tracks = list(dict.fromkeys([m for m in matches if m not in ["Spotify", "Single", "Album"]]))
            if not tracks:
                og_title = re.search(r'<title>(.*?)</title>', r.text)
                if og_title: tracks = [og_title.group(1).split('|')[0].strip()]
            return tracks
        except: return []

    def parse_ap(self, url):
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            matches = re.findall(r'\"name\":\"(.*?)\"', r.text)
            tracks = [m for m in matches if m and len(m) > 1 and m != "Apple Music"]
            if not tracks:
                og_title = re.search(r'<meta property="og:title" content="(.*?)"', r.text)
                if og_title:
                    clean = og_title.group(1).replace('on Apple Music', '').replace('\u200e', '').strip()
                    tracks = [clean]
            return list(dict.fromkeys(tracks))
        except: return []

    def dl_auto(self, name):
        src = self.source_var.get()
        cmd = f'echo 1 | rip --config-path "{self.config_path_var.get()}" search -f {src} track "{name}"'
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = p.communicate()
            if "Downloading" in stdout: self.log(f"DOWNLOADING: {name}")
            elif "already exists" in stdout or "Skipping" in stdout: self.log(f"EXISTS: {name}")
            elif "Complete" in stdout: self.log(f"COMPLETE: {name}")
            elif "No results" in stdout: self.log(f"NOT FOUND: {name}")
            else: self.log(f"FAILED: {name}")
        except: self.log(f"PROCESS ERROR: {name}")

    def dl_manual(self, name):
        src = self.source_var.get()
        cmd = f'rip --config-path "{self.config_path_var.get()}" search {src} track "{name}"'
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'start', 'cmd', '/k', cmd])
        else:
            term = "konsole" if shutil.which("konsole") else "x-terminal-emulator"
            subprocess.run([term, "-e", cmd])

    def exec_direct(self, url):
        try:
            subprocess.run(['rip', '--config-path', self.config_path_var.get(), '--no-progress', 'url', url])
        except: pass

if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()
