import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import cv2
import subprocess
from PIL import Image

# --- BACKEND (Değişmedi) ---
class ImageProcessorBackend:
    @staticmethod
    def process_image(image_path):
        if not os.path.exists(image_path):
            return None, "Dosya bulunamadı", 0, 0, 0

        original_size = os.path.getsize(image_path) / (1024 * 1024)
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        
        # Logo Silme (Sağ Alt)
        h_x1, h_y1 = w - 160, h - 160
        h_x2, h_y2 = h_x1 + 150, h_y1 + 150
        k_x1, k_y1 = h_x1 - 160, h_y1 
        k_x2, k_y2 = k_x1 + 150, k_y1 + 150

        try:
            img[h_y1:h_y2, h_x1:h_x2] = img[k_y1:k_y2, k_x1:k_x2]
            roi = img[h_y1:h_y2, h_x1:h_x2]
            img[h_y1:h_y2, h_x1:h_x2] = cv2.GaussianBlur(roi, (3, 3), 0)
        except: pass

        # Sıkıştırma
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        cikti_adi = f"HAZIR_{name}.jpg"
        hedef_byte = 1.95 * 1024 * 1024
        suanki_img = img.copy()
        kalite = 99; scale_percent = 100
        
        while True:
            basari, tampon = cv2.imencode('.jpg', suanki_img, [cv2.IMWRITE_JPEG_QUALITY, kalite])
            if not basari: return None, "Hata", 0, 0, 0
            boyut = len(tampon)
            mb = boyut / (1024 * 1024)
            if boyut <= hedef_byte:
                with open(cikti_adi, "wb") as f: f.write(tampon)
                return cikti_adi, original_size, mb, scale_percent, kalite
            else:
                scale_percent -= 5
                width = int(img.shape[1] * scale_percent / 100)
                height = int(img.shape[0] * scale_percent / 100)
                suanki_img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
                if scale_percent < 50:
                    kalite -= 2
                    if kalite < 85:
                         with open(cikti_adi, "wb") as f: f.write(tampon)
                         return cikti_adi, original_size, mb, scale_percent, kalite

# --- GUI (MODERN TASARIM) ---
class FrameLogoRemover(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Üst Başlık
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(20, 10))
        ctk.CTkLabel(self.top_frame, text="✨ THUMBNAIL SİHİRBAZI", font=("Roboto", 26, "bold"), text_color="#2CC985").pack(side="left")
        ctk.CTkLabel(self.top_frame, text="|  Tek Tıkla Logo Sil & Sıkıştır", font=("Roboto", 14), text_color="gray").pack(side="left", padx=10, pady=5)

        # Orta Panel (Resim Alanları)
        # Sol
        self.frame_orig = ctk.CTkFrame(self, fg_color="#181818", corner_radius=20, border_width=1, border_color="#333")
        self.frame_orig.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self.frame_orig, text="ORİJİNAL GÖRSEL", font=("Roboto", 12, "bold"), text_color="#666").pack(pady=10)
        self.lbl_orig_img = ctk.CTkLabel(self.frame_orig, text="📂 Lütfen Görsel Seçin", font=("Roboto", 14))
        self.lbl_orig_img.pack(expand=True)
        self.lbl_orig_info = ctk.CTkLabel(self.frame_orig, text="", font=("Consolas", 12), text_color="#AAA")
        self.lbl_orig_info.pack(pady=10)

        # Sağ
        self.frame_res = ctk.CTkFrame(self, fg_color="#181818", corner_radius=20, border_width=1, border_color="#333")
        self.frame_res.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        ctk.CTkLabel(self.frame_res, text="YOUTUBE HAZIR HALİ", font=("Roboto", 12, "bold"), text_color="#2CC985").pack(pady=10)
        self.lbl_res_img = ctk.CTkLabel(self.frame_res, text="İşlem Bekleniyor...", font=("Roboto", 14))
        self.lbl_res_img.pack(expand=True)
        self.lbl_res_info = ctk.CTkLabel(self.frame_res, text="", font=("Consolas", 12), text_color="#2CC985")
        self.lbl_res_info.pack(pady=10)

        # Alt Kontrol Paneli
        self.bot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bot_frame.grid(row=2, column=0, columnspan=2, pady=30)

        # MODERN BUTONLAR (Yuvarlak - Pill Shape)
        self.btn_select = ctk.CTkButton(
            self.bot_frame, text="📂 Görsel Seç", command=self.select_file, 
            width=160, height=50, corner_radius=32, 
            font=("Roboto", 15, "bold"), fg_color="#3A3A3A", hover_color="#505050"
        )
        self.btn_select.pack(side="left", padx=15)

        self.btn_process = ctk.CTkButton(
            self.bot_frame, text="⚡ SİHİRLİ DOKUNUŞ", command=self.run_process, 
            width=240, height=55, corner_radius=32, 
            font=("Roboto", 18, "bold"), fg_color="#E91E63", hover_color="#C2185B", state="disabled"
        )
        self.btn_process.pack(side="left", padx=15)
        
        self.btn_open_folder = ctk.CTkButton(
            self.bot_frame, text="📂 Klasörü Aç", command=self.open_folder, 
            width=160, height=50, corner_radius=32, 
            font=("Roboto", 15, "bold"), fg_color="#222", border_width=2, border_color="#444", hover_color="#333", state="disabled"
        )
        self.btn_open_folder.pack(side="left", padx=15)

        self.selected_path = None

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Resimler", "*.png *.jpg *.jpeg")])
        if path:
            self.selected_path = path
            self.show_preview(path, self.lbl_orig_img)
            size_mb = os.path.getsize(path) / (1024*1024)
            self.lbl_orig_info.configure(text=f"Boyut: {size_mb:.2f} MB")
            self.btn_process.configure(state="normal")
            self.lbl_res_img.configure(image=None, text="Hazır")

    def show_preview(self, path, label_widget):
        try:
            pil_img = Image.open(path)
            pil_img.thumbnail((450, 380)) 
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            label_widget.configure(image=ctk_img, text="")
        except: pass

    def run_process(self):
        if not self.selected_path: return
        self.btn_process.configure(state="disabled", text="⏳ İşleniyor...")
        
        def thread_task():
            res = ImageProcessorBackend.process_image(self.selected_path)
            self.after(0, lambda: self.process_done(*res))
        threading.Thread(target=thread_task).start()

    def process_done(self, path, old_s, new_s, scale, qual):
        if path:
            self.show_preview(path, self.lbl_res_img)
            self.lbl_res_info.configure(text=f"✅ {new_s:.2f} MB  |  %{scale} Ölçek  |  Kalite: %{qual}")
            self.btn_process.configure(state="normal", text="⚡ SİHİRLİ DOKUNUŞ")
            self.btn_open_folder.configure(state="normal")

    def open_folder(self):
        folder = os.getcwd()
        if os.name == 'nt': os.startfile(folder)
        else: subprocess.run(['xdg-open', folder])