import customtkinter as ctk
import os

# --- SAYFA İMPORTLARI ---
# Dosyaların aynı klasörde olduğundan emin ol
try:
    from kick_page import FrameKickStudio
except ImportError:
    print("HATA: kick_page.py bulunamadı!")
    FrameKickStudio = None

try:
    from logo_page import FrameLogoRemover
except ImportError:
    # Eğer logo_page yoksa program çökmesin diye boş bir sınıf oluşturuyoruz
    class FrameLogoRemover(ctk.CTkFrame):
        def __init__(self, parent, *args, **kwargs):
            super().__init__(parent, *args, **kwargs)
            ctk.CTkLabel(self, text="Logo Silici Sayfası Bulunamadı (logo_page.py eksik)", font=("Arial", 20)).pack(expand=True)

try:
    from editor_page import FrameEditor
except ImportError:
    print("HATA: editor_page.py bulunamadı!")
    FrameEditor = None

# --- GÜNCELLEYİCİ İMPORTU ---
try:
    from updater import AutoUpdater
except ImportError:
    print("HATA: updater.py bulunamadı!")
    AutoUpdater = None

# --- ARAYÜZ AYARLARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class MainStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # PENCERE AYARLARI
        self.title("KICK STUDIO & TOOLS ULTIMATE")
        self.geometry("1100x750")
        
        # Grid Düzeni (Sol Menü + Sağ İçerik)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= SOL MENÜ (SIDEBAR) =================
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1) # Boşluk bırak

        # Menü Başlığı
        ctk.CTkLabel(self.sidebar, text="KICK TOOLS", font=("Roboto", 20, "bold")).pack(pady=25)

        # --- BUTONLAR ---
        # 1. Kick Stüdyo Butonu
        self.btn_kick = ctk.CTkButton(self.sidebar, text="🚀 Kick Stüdyo", 
                                      height=40, corner_radius=10, 
                                      fg_color="transparent", border_width=2, border_color="#3B8ED0", text_color=("gray10", "#DCE4EE"),
                                      command=lambda: self.show_frame("kick"))
        self.btn_kick.pack(padx=20, pady=10, fill="x")

        # 2. Logo Silici Butonu
        self.btn_logo = ctk.CTkButton(self.sidebar, text="✨ Logo Silici", 
                                      height=40, corner_radius=10, 
                                      fg_color="transparent", border_width=2, border_color="#FFA500", text_color=("gray10", "#DCE4EE"),
                                      command=lambda: self.show_frame("logo"))
        self.btn_logo.pack(padx=20, pady=10, fill="x")

        # 3. Kurgu Masası Butonu
        self.btn_editor = ctk.CTkButton(self.sidebar, text="✂️ Kurgu Masası", 
                                        height=40, corner_radius=10, 
                                        fg_color="transparent", border_width=2, border_color="#E91E63", text_color=("gray10", "#DCE4EE"),
                                        command=lambda: self.show_frame("editor"))
        self.btn_editor.pack(padx=20, pady=10, fill="x")

        # Versiyon Bilgisi (Altta)
        self.lbl_version = ctk.CTkLabel(self.sidebar, text="v1.0", text_color="gray", font=("Arial", 10))
        self.lbl_version.pack(side="bottom", pady=20)


        # ================= İÇERİK ALANI =================
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # --- SAYFALARI YÜKLE ---
        self.frames = {}

        # Kick Sayfası
        if FrameKickStudio:
            self.frames["kick"] = FrameKickStudio(self.content_area)
            self.frames["kick"].grid(row=0, column=0, sticky="nsew")

        # Logo Sayfası
        self.frames["logo"] = FrameLogoRemover(self.content_area)
        self.frames["logo"].grid(row=0, column=0, sticky="nsew")

        # Editör Sayfası
        if FrameEditor:
            self.frames["editor"] = FrameEditor(self.content_area)
            self.frames["editor"].grid(row=0, column=0, sticky="nsew")

        # Varsayılan olarak Kick sayfasını aç
        self.show_frame("kick")

        # --- OTO GÜNCELLEME BAŞLAT ---
        # Program açıldıktan 1 saniye sonra kontrol etsin (Arayüz donmasın diye)
        if AutoUpdater:
            self.after(1000, self.start_update_check)

    def show_frame(self, page_name):
        """İstenen sayfayı öne getirir"""
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.tkraise()
            
            # Buton renklerini güncelle (Aktif olan parlasın)
            self.btn_kick.configure(fg_color="#3B8ED0" if page_name == "kick" else "transparent")
            self.btn_logo.configure(fg_color="#FFA500" if page_name == "logo" else "transparent")
            self.btn_editor.configure(fg_color="#E91E63" if page_name == "editor" else "transparent")

    def start_update_check(self):
        """Güncelleme kontrolünü başlatır"""
        try:
            # Şu anki sürüm: 1.0
            self.updater = AutoUpdater("1.0", self)
            self.updater.check_for_updates()
        except Exception as e:
            print(f"Update hatasi: {e}")

if __name__ == "__main__":
    app = MainStudioApp()
    app.mainloop()