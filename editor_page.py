import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, Canvas, messagebox
import threading
import os
import time
import subprocess
from PIL import Image, ImageTk

class FrameEditor(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(fg_color="transparent")

        # --- DEĞİŞKENLER ---
        self.video_list = [] # Birleştirilecek videolar
        self.layer_list = [] # {type: 'text'/'image', content: path/str, start: 0, end: 10, x: 0, y: 0}
        self.selected_layer_index = None
        self.preview_image_tk = None
        self.base_folder = os.path.dirname(os.path.abspath(__file__))
        
        # --- ANA YERLEŞİM ---
        self.grid_columnconfigure(0, weight=0) # Sol Panel
        self.grid_columnconfigure(1, weight=1) # Sağ Panel
        self.grid_rowconfigure(0, weight=1)

        # ================= SOL PANEL (Kontroller) =================
        self.frame_left = ctk.CTkFrame(self, width=350, corner_radius=20, fg_color=("#EBEBEB", "#242424"))
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.frame_left.grid_propagate(False)

        ctk.CTkLabel(self.frame_left, text="KURGU MASASI", font=("Roboto", 20, "bold"), text_color="#E91E63").pack(pady=(20, 10))

        # --- TABVIEW (Sekmeli Yapı) ---
        self.tabview = ctk.CTkTabview(self.frame_left, height=400, corner_radius=15)
        self.tabview.pack(fill="x", padx=10, pady=5)
        self.tab_videos = self.tabview.add("Videolar")
        self.tab_layers = self.tabview.add("Katmanlar")

        # 1. SEKME: VİDEO BİRLEŞTİRME
        self.listbox_videos = tk.Listbox(self.tab_videos, bg="#333", fg="white", selectbackground="#E91E63", height=10, bd=0)
        self.listbox_videos.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame_vid = ctk.CTkFrame(self.tab_videos, fg_color="transparent")
        btn_frame_vid.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame_vid, text="+ Ekle", width=60, command=self.add_video, fg_color="#3B8ED0").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_vid, text="- Sil", width=60, command=self.remove_video, fg_color="#D32F2F").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_vid, text="▲", width=30, command=self.move_up).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_vid, text="▼", width=30, command=self.move_down).pack(side="left", padx=2)

        # Geçiş Ayarı
        self.transition_var = ctk.StringVar(value="cut")
        ctk.CTkRadioButton(self.tab_videos, text="Keskin Geçiş (Hızlı)", variable=self.transition_var, value="cut").pack(pady=5, anchor="w")
        ctk.CTkRadioButton(self.tab_videos, text="Fade (Yumuşak)", variable=self.transition_var, value="fade").pack(pady=5, anchor="w")


        # 2. SEKME: KATMANLAR (Yazı/Resim)
        self.listbox_layers = tk.Listbox(self.tab_layers, bg="#333", fg="white", selectbackground="#E91E63", height=8, bd=0)
        self.listbox_layers.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox_layers.bind('<<ListboxSelect>>', self.on_layer_select)

        btn_frame_layer = ctk.CTkFrame(self.tab_layers, fg_color="transparent")
        btn_frame_layer.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame_layer, text="+ Resim", width=70, command=self.add_image_layer, fg_color="#555").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_layer, text="+ Yazı", width=70, command=self.add_text_layer, fg_color="#555").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame_layer, text="- Sil", width=50, command=self.remove_layer, fg_color="#D32F2F").pack(side="left", padx=2)

        # Katman Ayarları
        self.frame_layer_settings = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.frame_layer_settings.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.frame_layer_settings, text="Seçili Katman Ayarları", font=("Roboto", 12, "bold")).pack()
        
        # Zamanlama
        time_frame = ctk.CTkFrame(self.frame_layer_settings, fg_color="transparent")
        time_frame.pack(pady=2)
        self.entry_start = ctk.CTkEntry(time_frame, width=60, placeholder_text="Başla")
        self.entry_start.pack(side="left", padx=2)
        ctk.CTkLabel(time_frame, text="-").pack(side="left")
        self.entry_end = ctk.CTkEntry(time_frame, width=60, placeholder_text="Bitiş")
        self.entry_end.pack(side="left", padx=2)
        ctk.CTkLabel(time_frame, text="sn").pack(side="left")
        
        # Yazı İçeriği (Sadece yazı ise aktif olur)
        self.entry_text_content = ctk.CTkEntry(self.frame_layer_settings, placeholder_text="Yazı içeriği...")
        self.entry_text_content.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.frame_layer_settings, text="💾 Ayarları Kaydet", command=self.save_layer_settings, height=25, fg_color="#2CC985").pack(pady=5)


        # --- ALT KISIM (Render) ---
        self.progress_bar = ctk.CTkProgressBar(self.frame_left, progress_color="#E91E63")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="bottom", fill="x", padx=20, pady=(0, 20))
        
        self.btn_render = ctk.CTkButton(self.frame_left, text="🎬 BİRLEŞTİR VE KAYDET", command=self.start_render_thread, 
                                        height=50, font=("Roboto", 14, "bold"), fg_color="#E91E63", hover_color="#C2185B")
        self.btn_render.pack(side="bottom", fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.frame_left, text="Hazır", text_color="gray")
        self.status_label.pack(side="bottom", pady=5)


        # ================= SAĞ PANEL (Önizleme) =================
        self.frame_right = ctk.CTkFrame(self, fg_color="#101010", corner_radius=20)
        self.frame_right.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        
        ctk.CTkLabel(self.frame_right, text="GÖRSEL YERLEŞTİRME EKRANI", text_color="#888").pack(pady=10)

        self.cv_w = 640
        self.cv_h = 360
        self.canvas = Canvas(self.frame_right, width=self.cv_w, height=self.cv_h, bg="black", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        self.canvas.create_text(self.cv_w/2, self.cv_h/2, text="ÖNİZLEME ALANI\n(İlk videodan kare alınır)", fill="#444", justify="center")

        # Drag & Drop
        self.canvas.tag_bind("drag", "<Button-1>", self.on_drag_start)
        self.canvas.tag_bind("drag", "<B1-Motion>", self.on_drag_motion)
        self.canvas.tag_bind("drag", "<ButtonRelease-1>", self.on_drag_stop)
        self._drag_data = {"x": 0, "y": 0}

    # --- VİDEO İŞLEMLERİ ---
    def add_video(self):
        files = filedialog.askopenfilenames(title="Video Seç", filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        for f in files:
            self.video_list.append(f)
            self.listbox_videos.insert("end", os.path.basename(f))
        
        # İlk videonun ekran görüntüsünü alıp canvas'a koy (Konumlandırma için referans)
        if len(self.video_list) == 1:
            self.update_preview_bg(self.video_list[0])

    def remove_video(self):
        sel = self.listbox_videos.curselection()
        if sel:
            idx = sel[0]
            self.listbox_videos.delete(idx)
            self.video_list.pop(idx)

    def move_up(self):
        sel = self.listbox_videos.curselection()
        if not sel or sel[0] == 0: return
        idx = sel[0]
        text = self.listbox_videos.get(idx)
        self.listbox_videos.delete(idx)
        self.listbox_videos.insert(idx-1, text)
        self.listbox_videos.selection_set(idx-1)
        # Listeyi güncelle
        self.video_list[idx], self.video_list[idx-1] = self.video_list[idx-1], self.video_list[idx]

    def move_down(self):
        sel = self.listbox_videos.curselection()
        if not sel or sel[0] == self.listbox_videos.size()-1: return
        idx = sel[0]
        text = self.listbox_videos.get(idx)
        self.listbox_videos.delete(idx)
        self.listbox_videos.insert(idx+1, text)
        self.listbox_videos.selection_set(idx+1)
        # Listeyi güncelle
        self.video_list[idx], self.video_list[idx+1] = self.video_list[idx+1], self.video_list[idx]

    # --- KATMAN İŞLEMLERİ ---
    def add_image_layer(self):
        path = filedialog.askopenfilename(filetypes=[("Resim", "*.png *.jpg")])
        if path:
            self.layer_list.append({
                "type": "image", "content": path, 
                "start": "0", "end": "5", "x": 50, "y": 50
            })
            self.listbox_layers.insert("end", f"[RESİM] {os.path.basename(path)}")
            self.draw_layers_on_canvas()

    def add_text_layer(self):
        self.layer_list.append({
            "type": "text", "content": "Yeni Yazi", 
            "start": "0", "end": "5", "x": 100, "y": 100
        })
        self.listbox_layers.insert("end", f"[YAZI] Yeni Yazi")
        self.draw_layers_on_canvas()

    def remove_layer(self):
        sel = self.listbox_layers.curselection()
        if sel:
            idx = sel[0]
            self.listbox_layers.delete(idx)
            self.layer_list.pop(idx)
            self.canvas.delete("drag")
            self.draw_layers_on_canvas()

    def on_layer_select(self, event):
        sel = self.listbox_layers.curselection()
        if not sel: return
        idx = sel[0]
        self.selected_layer_index = idx
        data = self.layer_list[idx]
        
        # Formu doldur
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, data["start"])
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, data["end"])
        
        if data["type"] == "text":
            self.entry_text_content.configure(state="normal")
            self.entry_text_content.delete(0, "end")
            self.entry_text_content.insert(0, data["content"])
        else:
            self.entry_text_content.configure(state="disabled")

    def save_layer_settings(self):
        if self.selected_layer_index is not None:
            idx = self.selected_layer_index
            self.layer_list[idx]["start"] = self.entry_start.get()
            self.layer_list[idx]["end"] = self.entry_end.get()
            if self.layer_list[idx]["type"] == "text":
                new_text = self.entry_text_content.get()
                self.layer_list[idx]["content"] = new_text
                # Listbox güncelle
                self.listbox_layers.delete(idx)
                self.listbox_layers.insert(idx, f"[YAZI] {new_text}")
                self.listbox_layers.selection_set(idx)
            
            self.draw_layers_on_canvas()

    # --- CANVAS & PREVIEW ---
    def update_preview_bg(self, video_path):
        try:
            # FFmpeg ile ilk kareyi al
            thumb = os.path.join(self.base_folder, "editor_preview.jpg")
            subprocess.run(['ffmpeg', '-y', '-i', video_path, '-frames:v', '1', '-q:v', '2', thumb], 
                           stderr=subprocess.DEVNULL)
            
            img = Image.open(thumb)
            img = img.resize((self.cv_w, self.cv_h), Image.Resampling.LANCZOS)
            self.preview_image_tk = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, image=self.preview_image_tk, anchor="nw", tags="bg")
            self.canvas.tag_lower("bg")
        except: pass

    def draw_layers_on_canvas(self):
        self.canvas.delete("drag")
        for i, layer in enumerate(self.layer_list):
            x, y = layer["x"], layer["y"]
            tag = f"layer_{i}"
            
            if layer["type"] == "text":
                self.canvas.create_text(x, y, text=layer["content"], fill="white", font=("Arial", 20, "bold"), tags=("drag", tag))
            elif layer["type"] == "image":
                # Basit bir kutu olarak gösterelim (Görseli resize etmekle uğraşmamak için)
                self.canvas.create_rectangle(x, y, x+100, y+60, outline="cyan", width=2, tags=("drag", tag))
                self.canvas.create_text(x+50, y+30, text="RESİM", fill="cyan", tags=("drag", tag))

    # --- DRAG & DROP MANTIĞI ---
    def on_drag_start(self, event):
        # En yakın nesneyi bul
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        for tag in tags:
            if tag.startswith("layer_"):
                self.selected_layer_index = int(tag.split("_")[1])
                self.listbox_layers.selection_clear(0, "end")
                self.listbox_layers.selection_set(self.selected_layer_index)
                self.on_layer_select(None) # Ayarları yükle
                break
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        if self.selected_layer_index is None: return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        
        # Sadece seçili layer'ın tag'ine sahip objeleri hareket ettir
        tag = f"layer_{self.selected_layer_index}"
        self.canvas.move(tag, dx, dy)
        
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_stop(self, event):
        if self.selected_layer_index is not None:
            # Yeni koordinatları kaydet
            tag = f"layer_{self.selected_layer_index}"
            coords = self.canvas.coords(tag) # Text ise [x, y], Rect ise [x1, y1, x2, y2]
            
            self.layer_list[self.selected_layer_index]["x"] = int(coords[0])
            self.layer_list[self.selected_layer_index]["y"] = int(coords[1])

    # --- RENDER (FFmpeg Büyüsü) ---
    def start_render_thread(self):
        if not self.video_list: return
        self.btn_render.configure(state="disabled", text="İşleniyor...")
        self.progress_bar.set(0)
        threading.Thread(target=self.run_render).start()

    def run_render(self):
        try:
            output_file = os.path.join(self.base_folder, f"MONTAJ_{int(time.time())}.mp4")
            list_file = os.path.join(self.base_folder, "files.txt")
            
            # 1. ADIM: Dosya Listesi Oluştur (Concat için)
            with open(list_file, "w", encoding="utf-8") as f:
                for vid in self.video_list:
                    # Linux/Windows path düzeltmesi
                    safe_path = vid.replace("'", "'\\''") 
                    f.write(f"file '{safe_path}'\n")

            # 2. ADIM: Filtre Zinciri Oluştur (Overlays)
            # Koordinat Çevirimi: Canvas (640x360) -> Video (1920x1080)
            scale_x = 1920 / 640
            scale_y = 1080 / 360
            
            filter_complex = ""
            
            # Katmanlar varsa filtre hazırla
            if self.layer_list:
                # [0:v] videonun kendisi. Overlayler zincirleme eklenecek.
                filter_complex = "[0:v]" 
                
                # Önce resim inputlarını ekle
                img_inputs = []
                input_idx = 1 # 0 video, 1'den itibaren resimler
                
                # Resim dosyaları için -i komutları
                cmd_inputs = []
                
                # Overlay metni oluştur
                last_tag = "[0:v]"
                
                for i, layer in enumerate(self.layer_list):
                    real_x = int(layer["x"] * scale_x)
                    real_y = int(layer["y"] * scale_y)
                    start = layer["start"]
                    end = layer["end"]
                    
                    if layer["type"] == "text":
                        # Yazı için drawtext (Linux'ta font sorunu olmaması için fontfile belirtmiyoruz, default kullanır)
                        # escape text
                        txt = layer["content"].replace(":", "\\:").replace("'", "")
                        filter_complex += f"drawtext=text='{txt}':x={real_x}:y={real_y}:fontsize=50:fontcolor=white:enable='between(t,{start},{end})',"
                    
                    elif layer["type"] == "image":
                        cmd_inputs.extend(['-i', layer["content"]])
                        # Resmi boyutlandır (örn: 200px)
                        current_input = f"[{input_idx}:v]"
                        input_idx += 1
                        
                        # Overlay ekle
                        # NOT: Çoklu overlay zinciri karmaşıktır, basitleştirilmiş hali:
                        # Resim overlay'i şu anlık TEXT öncesi yapılmalı veya filter_complex dikkatli kurulmalı.
                        # Bu örnekte basitlik adına sadece Text çalışır, Resim için daha kompleks yapı gerekir.
                        # Ama biz yine de deneyelim:
                        pass # Resim overlay mantığı biraz daha karışıktır, şimdilik text odaklı gidelim.

                # Sondaki virgülü sil
                if filter_complex.endswith(","): filter_complex = filter_complex[:-1]

            # 3. ADIM: FFmpeg Komutu
            # Concat (Birleştirme) + Filtre
            # Cut (Keskin) modundaysak concat demuxer kullanırız ama filtre varsa re-encode şarttır.
            
            cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file]
            
            if filter_complex:
                cmd.extend(['-vf', filter_complex])
            
            cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', output_file])

            self.after(0, lambda: self.status_label.configure(text="Render Başladı (Bu işlem sürebilir)..."))
            
            subprocess.run(cmd, check=True)
            
            self.after(0, lambda: self.status_label.configure(text=f"✅ Kaydedildi: {os.path.basename(output_file)}"))
            self.after(0, lambda: self.progress_bar.set(1))
            self.after(0, lambda: subprocess.run(['xdg-open', self.base_folder]))

        except Exception as e:
            print(e)
            self.after(0, lambda: self.status_label.configure(text=f"Hata: {str(e)}"))
        finally:
            self.after(0, lambda: self.btn_render.configure(state="normal", text="🎬 BİRLEŞTİR VE KAYDET"))
            if os.path.exists(list_file): os.remove(list_file)