import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, Canvas
import threading
import os
import time
import m3u8
import subprocess
from PIL import Image, ImageTk
from playwright.sync_api import sync_playwright

class FrameKickStudio(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # --- GENEL AYARLAR ---
        self.configure(fg_color="transparent") 

        # Değişkenler
        self.watermark_path = None
        self.original_image = None
        self.preview_image = None
        self.bg_image_tk = None
        
        self.wm_x = 0
        self.wm_y = 0
        self.opacity = 1.0
        self.scale = 0.5
        
        self.base_folder = os.path.dirname(os.path.abspath(__file__))
        self.total_duration_sec = 0
        self.video_real_width = 1920
        self.video_real_height = 1080

        # --- ANA YERLEŞİM ---
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= SOL PANEL =================
        self.frame_left = ctk.CTkFrame(self, width=320, corner_radius=20, fg_color=("#EBEBEB", "#242424"))
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.frame_left.grid_propagate(False)

        # Başlık
        ctk.CTkLabel(self.frame_left, text="KICK STUDIO V37", font=("Roboto", 22, "bold"), text_color="#2CC985").pack(pady=(25, 15))

        # URL
        self.entry_url = ctk.CTkEntry(self.frame_left, placeholder_text="Kick Video Linki (Örn: kick.com/...)", width=280, height=35, corner_radius=10)
        self.entry_url.pack(pady=5)

        # Zaman
        self.frame_time = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_time.pack(pady=5)

        self.entry_start = ctk.CTkEntry(self.frame_time, placeholder_text="00:00:00", width=135, height=35, corner_radius=10)
        self.entry_start.pack(side="left", padx=5)
        self.entry_start.bind("<KeyRelease>", lambda event: self.format_time_input(event, self.entry_start))
        
        self.entry_end = ctk.CTkEntry(self.frame_time, placeholder_text="00:00:00", width=135, height=35, corner_radius=10)
        self.entry_end.pack(side="left", padx=5)
        self.entry_end.bind("<KeyRelease>", lambda event: self.format_time_input(event, self.entry_end))

        self.label_calc = ctk.CTkLabel(self.frame_left, text="Süre: -- | Tahmini: -- MB", font=("Roboto", 12), text_color="gray")
        self.label_calc.pack(pady=5)

        # Önizleme Butonu
        self.btn_preview_bg = ctk.CTkButton(self.frame_left, text="🎬 Video Önizlemesini Getir", command=self.fetch_preview_bg, 
                                            width=280, height=40, corner_radius=20,
                                            fg_color="#3B8ED0", hover_color="#36719F", font=("Roboto", 13, "bold"))
        self.btn_preview_bg.pack(pady=15)

        # Görsel Seç
        self.btn_img = ctk.CTkButton(self.frame_left, text="🖼️ Logo / Görsel Seç", command=self.select_image, 
                                     width=280, height=35, corner_radius=20,
                                     fg_color="#555555", hover_color="#444444")
        self.btn_img.pack(pady=5)

        # Sliderlar
        ctk.CTkLabel(self.frame_left, text="Logo Boyutu").pack(pady=(5,0))
        self.slider_scale = ctk.CTkSlider(self.frame_left, from_=0.1, to=1.5, number_of_steps=50, command=self.update_image_visuals, width=240, progress_color="#2CC985")
        self.slider_scale.set(0.5)
        self.slider_scale.pack(pady=5)

        ctk.CTkLabel(self.frame_left, text="Saydamlık").pack(pady=(5,0))
        self.slider_opacity = ctk.CTkSlider(self.frame_left, from_=0.0, to=1.0, number_of_steps=50, command=self.update_image_visuals, width=240, progress_color="#2CC985")
        self.slider_opacity.set(1.0)
        self.slider_opacity.pack(pady=5)

        # Log
        self.textbox_log = ctk.CTkTextbox(self.frame_left, width=280, height=80, font=("Consolas", 10), corner_radius=15)
        self.textbox_log.pack(pady=10)
        self.textbox_log.configure(state="disabled")

        # İndirme Alanı
        self.frame_bottom = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_bottom.pack(side="bottom", fill="x", padx=10, pady=20)

        self.label_progress_perc = ctk.CTkLabel(self.frame_bottom, text="%0 - Kalan: --:--", font=("Roboto", 12, "bold"))
        self.label_progress_perc.pack(pady=2)

        self.progress_bar = ctk.CTkProgressBar(self.frame_bottom, width=280, height=10, progress_color="#E91E63")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.btn_download = ctk.CTkButton(self.frame_bottom, text="🚀 TURBO RENDER & İNDİR", command=self.start_download_thread, 
                                          width=280, height=50, corner_radius=25, 
                                          font=("Roboto", 15, "bold"), fg_color="#E91E63", hover_color="#C2185B")
        self.btn_download.pack(pady=5)


        # ================= SAĞ PANEL =================
        self.frame_right = ctk.CTkFrame(self, fg_color="#101010", corner_radius=20)
        self.frame_right.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        
        ctk.CTkLabel(self.frame_right, text="EDİTÖR EKRANI (İpucu: Logo taşımak için sürükle)", font=("Roboto", 14), text_color="#888").pack(pady=15)

        self.frame_canvas_container = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        self.frame_canvas_container.pack(expand=True)

        self.cv_w = 640
        self.cv_h = 360
        self.canvas = Canvas(self.frame_canvas_container, width=self.cv_w, height=self.cv_h, bg="black", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        self.line_v = self.canvas.create_line(self.cv_w/2, 0, self.cv_w/2, self.cv_h, fill="#00FF00", dash=(4, 4), width=1, state="hidden")
        self.line_h = self.canvas.create_line(0, self.cv_h/2, self.cv_w, self.cv_h/2, fill="#00FF00", dash=(4, 4), width=1, state="hidden")
        self.center_cross = self.canvas.create_text(self.cv_w/2, self.cv_h/2, text="🎯", fill="#00FF00", font=("Arial", 24), state="hidden")
        
        self.info_text = self.canvas.create_text(self.cv_w/2, self.cv_h/2, text="VİDEO ALANI", fill="#444", font=("Arial", 16, "bold"))

        self.canvas.tag_bind("drag", "<Button-1>", self.on_drag_start)
        self.canvas.tag_bind("drag", "<B1-Motion>", self.on_drag_motion)
        self.canvas.tag_bind("drag", "<ButtonRelease-1>", self.on_drag_stop)

        self._drag_data = {"x": 0, "y": 0}

    # --- THREAD SAFE LOG FONKSİYONU ---
    def log(self, message):
        self.after(0, lambda: self._log_impl(message))

    def _log_impl(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", f"> {message}\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    # --- DİĞER FONKSİYONLAR ---
    def format_time_input(self, event, entry_widget):
        if event.keysym == "BackSpace":
            self.calculate_info()
            return
        text = entry_widget.get()
        digits = "".join(filter(str.isdigit, text))
        if len(digits) > 6: digits = digits[:6]
        formatted = ""
        if len(digits) > 0: formatted += digits[:2]
        if len(digits) > 2: formatted += ":" + digits[2:4]
        if len(digits) > 4: formatted += ":" + digits[4:6]
        if text != formatted:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, formatted)
        self.calculate_info()

    def time_to_seconds(self, t_str):
        try:
            parts = list(map(int, t_str.split(':')))
            if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
            if len(parts) == 2: return parts[0]*60 + parts[1]
            return 0
        except: return 0

    def calculate_info(self, event=None):
        start = self.entry_start.get()
        end = self.entry_end.get()
        s_sec = self.time_to_seconds(start)
        e_sec = self.time_to_seconds(end)
        
        if e_sec > s_sec:
            duration = e_sec - s_sec
            self.total_duration_sec = duration
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            size_mb = duration * 0.75 
            self.label_calc.configure(text=f"Süre: {h}sa {m}dk {s}sn | ~{int(size_mb)} MB", text_color="#2CC985")
        else:
            self.label_calc.configure(text="Süre: -- | Tahmini: -- MB", text_color="gray")

    # --- ÖNİZLEME İNDİRME (GÜNCELLENDİ: TIMEOUT FIX) ---
    def fetch_preview_bg(self):
        url = self.entry_url.get()
        start = self.entry_start.get()
        if not url or not start:
            self.log("HATA: Link ve saat giriniz.")
            return
        threading.Thread(target=self._download_thumbnail, args=(url, start)).start()

    def _download_thumbnail(self, url, start_time):
        self.after(0, lambda: self.btn_preview_bg.configure(state="disabled", text="Görüntü İndiriliyor..."))
        try:
            final_url = None
            self.log("Önizleme için link aranıyor...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
                page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
                found = None
                
                def handle_request(r):
                    nonlocal found
                    if ".m3u8" in r.url and "master" in r.url: 
                        found = r.url
                
                page.on("request", handle_request)

                # DÜZELTME: Timeout 90sn ve DOM yüklenmesini bekle
                page.goto(url, timeout=90000, wait_until="domcontentloaded")
                
                for i in range(25):
                    if found: break
                    if i > 2 and i % 5 == 0:
                        try: page.evaluate("document.querySelector('video').play()")
                        except: pass
                    time.sleep(1)
                
                if found:
                    try:
                        m_obj = m3u8.load(found)
                        if m_obj.is_variant:
                            best = max(m_obj.playlists, key=lambda p: p.stream_info.bandwidth)
                            uri = best.uri
                            final_url = f"{found.rsplit('/', 1)[0]}/{uri}" if not uri.startswith('http') else uri
                            if best.stream_info.resolution:
                                self.video_real_width, self.video_real_height = best.stream_info.resolution
                        else: final_url = found
                    except: final_url = found
                browser.close()

            if not final_url:
                self.log("❌ Link alınamadı (veya süre doldu).")
                self.after(0, lambda: self.btn_preview_bg.configure(state="normal", text="🎬 Video Önizlemesini Getir"))
                return

            thumb_path = os.path.join(self.base_folder, "preview.jpg")
            cmd = ['ffmpeg', '-y', '-analyzeduration', '20M', '-probesize', '20M', '-ss', start_time, '-i', final_url, '-frames:v', '1', '-q:v', '2', thumb_path]
            subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
            
            img = Image.open(thumb_path)
            img = img.resize((self.cv_w, self.cv_h), Image.Resampling.LANCZOS)
            self.bg_image_tk = ImageTk.PhotoImage(img)
            
            def update_canvas():
                self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor="nw", tags="bg")
                self.canvas.tag_lower("bg")
                self.canvas.delete(self.info_text)
            
            self.after(0, update_canvas)
            self.log("✅ Önizleme yüklendi.")

        except Exception as e:
            self.log(f"Hata: {e}")
        finally:
            self.after(0, lambda: self.btn_preview_bg.configure(state="normal", text="🎬 Video Önizlemesini Getir"))

    # --- GÖRSEL İŞLEMLERİ ---
    def select_image(self):
        file_path = filedialog.askopenfilename(title="Görsel Seç", filetypes=[("Resimler", "*.png *.jpg *.jpeg *.webp")])
        if file_path:
            self.watermark_path = file_path
            self.original_image = Image.open(file_path).convert("RGBA")
            self.update_image_visuals()
            self.log(f"Görsel: {os.path.basename(file_path)}")

    def update_image_visuals(self, event=None):
        if not self.original_image: return
        self.scale = self.slider_scale.get()
        self.opacity = self.slider_opacity.get()

        orig_w, orig_h = self.original_image.size
        new_w = int(orig_w * self.scale)
        new_h = int(orig_h * self.scale)
        
        preview_ratio = self.cv_w / self.video_real_width 
        display_w = int(new_w * preview_ratio)
        display_h = int(new_h * preview_ratio)
        if display_w < 1: display_w = 1
        if display_h < 1: display_h = 1

        img_resized = self.original_image.resize((display_w, display_h), Image.Resampling.LANCZOS)
        r, g, b, alpha = img_resized.split()
        alpha = alpha.point(lambda p: int(p * self.opacity))
        img_final = Image.merge("RGBA", (r, g, b, alpha))

        self.preview_image = ImageTk.PhotoImage(img_final)
        
        if self.canvas.find_withtag("drag"):
            self.canvas.itemconfig("drag", image=self.preview_image)
        else:
            self.canvas.create_image(self.cv_w/2, self.cv_h/2, image=self.preview_image, tags="drag")
            self.wm_x = self.cv_w/2
            self.wm_y = self.cv_h/2

    # --- DRAG & DROP ---
    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        mouse_dx = event.x - self._drag_data["x"]
        mouse_dy = event.y - self._drag_data["y"]
        bbox = self.canvas.bbox("drag")
        if not bbox: return
        
        future_x1 = bbox[0] + mouse_dx
        future_x2 = bbox[2] + mouse_dx
        future_y1 = bbox[1] + mouse_dy
        future_y2 = bbox[3] + mouse_dy
        future_center_x = (future_x1 + future_x2) / 2
        future_center_y = (future_y1 + future_y2) / 2
        canvas_center_x = self.cv_w / 2
        canvas_center_y = self.cv_h / 2
        
        is_ctrl_pressed = (event.state & 0x4) != 0 
        snap_zone = 8
        final_dx = mouse_dx
        final_dy = mouse_dy
        snapped_x = False
        snapped_y = False

        if not is_ctrl_pressed:
            if abs(future_center_x - canvas_center_x) < snap_zone:
                obj_w = bbox[2] - bbox[0]
                target_x = canvas_center_x - (obj_w / 2)
                final_dx = target_x - bbox[0]
                snapped_x = True
            if abs(future_center_y - canvas_center_y) < snap_zone:
                obj_h = bbox[3] - bbox[1]
                target_y = canvas_center_y - (obj_h / 2)
                final_dy = target_y - bbox[1]
                snapped_y = True

        check_x1 = bbox[0] + final_dx
        check_x2 = bbox[2] + final_dx
        check_y1 = bbox[1] + final_dy
        check_y2 = bbox[3] + final_dy

        if check_x1 < 0: final_dx = 0 - bbox[0]
        elif check_x2 > self.cv_w: final_dx = self.cv_w - bbox[2]
        if check_y1 < 0: final_dy = 0 - bbox[1]
        elif check_y2 > self.cv_h: final_dy = self.cv_h - bbox[3]

        self.canvas.move("drag", final_dx, final_dy)
        self._drag_data["x"] = event.x; self._drag_data["y"] = event.y

        if snapped_x: self.canvas.itemconfig(self.line_v, state="normal")
        else: self.canvas.itemconfig(self.line_v, state="hidden")
        if snapped_y: self.canvas.itemconfig(self.line_h, state="normal")
        else: self.canvas.itemconfig(self.line_h, state="hidden")
        if snapped_x and snapped_y: self.canvas.itemconfig(self.center_cross, state="normal")
        else: self.canvas.itemconfig(self.center_cross, state="hidden")

        final_bbox = self.canvas.bbox("drag")
        if final_bbox:
            self.wm_x = final_bbox[0]
            self.wm_y = final_bbox[1]

    def on_drag_stop(self, event):
        self.canvas.itemconfig(self.line_v, state="hidden")
        self.canvas.itemconfig(self.line_h, state="hidden")
        self.canvas.itemconfig(self.center_cross, state="hidden")

    # --- TURBO RENDER (GÜNCELLENDİ: TIMEOUT FIX) ---
    def start_download_thread(self):
        if not self.entry_url.get(): return
        self.btn_download.configure(state="disabled", text="Turbo Render Hazırlanıyor...")
        self.progress_bar.set(0)
        self.label_progress_perc.configure(text="%0 - Kalan: --:--")
        threading.Thread(target=self.run_render).start()

    def run_render(self):
        try:
            url = self.entry_url.get()
            start = self.entry_start.get()
            end = self.entry_end.get()
            
            self.log("Link aranıyor...")
            final_url = None
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
                page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
                found = None
                
                def handle_request(r): 
                    nonlocal found
                    if ".m3u8" in r.url and "master" in r.url: found = r.url
                
                page.on("request", handle_request)

                # DÜZELTME: Timeout 90sn ve DOM yüklenmesini bekle
                page.goto(url, timeout=90000, wait_until="domcontentloaded")
                
                for i in range(25):
                    if found: break
                    if i > 2 and i % 5 == 0:
                        try: page.evaluate("document.querySelector('video').play()")
                        except: pass
                    time.sleep(1)
                
                if found:
                    try:
                        m = m3u8.load(found)
                        if m.is_variant:
                            best = max(m.playlists, key=lambda x: x.stream_info.bandwidth)
                            final_url = best.uri if best.uri.startswith("http") else f"{found.rsplit('/',1)[0]}/{best.uri}"
                            if best.stream_info.resolution:
                                self.video_real_width, self.video_real_height = best.stream_info.resolution
                        else: final_url = found
                    except: final_url = found
                browser.close()

            if not final_url:
                self.log("Link bulunamadı (veya süre doldu)!")
                self.after(0, lambda: self.btn_download.configure(state="normal", text="🚀 TURBO RENDER & İNDİR"))
                return

            ratio = self.video_real_width / self.cv_w 
            real_x = int(self.wm_x * ratio)
            real_y = int(self.wm_y * ratio)
            
            output = os.path.join(self.base_folder, f"STUDIO_RENDER_{int(time.time())}.mp4")
            
            base_cmd = [
                'ffmpeg', '-y', 
                '-fflags', '+genpts', 
                '-analyzeduration', '20M', 
                '-probesize', '20M',
                '-ss', start, 
                '-to', end, 
                '-i', final_url
            ]
            
            if not self.watermark_path:
                cmd = base_cmd + [
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', '-crf', '23', '-threads', '0',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-vsync', 'cfr', '-af', 'aresample=async=1',
                    '-progress', 'pipe:1', '-nostats', output
                ]
            else:
                self.log(f"Turbo Render başlıyor...")
                img_w, img_h = self.original_image.size
                target_w = int(img_w * self.scale)
                target_h = int(img_h * self.scale)
                
                filter_str = (
                    f"[1:v]scale={target_w}:{target_h},format=rgba,"
                    f"colorchannelmixer=aa={self.opacity}[wm];"
                    f"[0:v][wm]overlay={real_x}:{real_y}"
                )

                cmd = base_cmd + [
                    '-i', self.watermark_path,
                    '-filter_complex', filter_str,
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', '-crf', '23', '-threads', '0',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-vsync', 'cfr', '-af', 'aresample=async=1',
                    '-progress', 'pipe:1', '-nostats',
                    output
                ]

            si = None
            if os.name == 'nt':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            start_render_time = time.time()
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, startupinfo=si)
            
            for line in p.stdout:
                if "out_time_us=" in line and self.total_duration_sec > 0:
                    try:
                        us = int(line.split("=")[1])
                        curr = us / 1000000
                        perc = curr / self.total_duration_sec
                        if perc > 1: perc = 1
                        
                        elapsed = time.time() - start_render_time
                        if perc > 0:
                            eta_seconds = (elapsed / perc) - elapsed
                            m, s = divmod(int(eta_seconds), 60)
                            eta_str = f"{m:02d}:{s:02d}"
                        else:
                            eta_str = "--:--"
                        
                        self.after(0, lambda p=perc, e=eta_str: self._update_progress(p, e))
                        
                    except: pass
            
            p.wait()
            if p.returncode == 0:
                self.log("✅ Tamamlandı!")
                self.after(0, lambda: self.progress_bar.set(1))
                self.after(0, lambda: self.label_progress_perc.configure(text="%100 - Hazır"))
                if os.name == 'nt': os.startfile(self.base_folder)
                else: subprocess.run(['xdg-open', self.base_folder])
            else:
                self.log("❌ Hata oluştu.")

        except Exception as e:
            self.log(f"Kritik Hata: {e}")
        finally:
            self.after(0, lambda: self.btn_download.configure(state="normal", text="🚀 TURBO RENDER & İNDİR"))

    def _update_progress(self, perc, eta_str):
        self.progress_bar.set(perc)
        self.label_progress_perc.configure(text=f"İşleniyor: %{int(perc*100)} - Kalan: {eta_str}")