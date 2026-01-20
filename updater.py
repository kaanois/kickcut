import customtkinter as ctk
import requests
import sys
import subprocess
import threading
import time
import os

class AutoUpdater:
    def __init__(self, current_version, parent_window):
        self.current_version = current_version
        self.parent_window = parent_window
        
        # --- SENİN GITHUB LİNKİN ---
        self.version_url = "https://raw.githubusercontent.com/kaanois/kickcut/main/version.txt"
        
        # İndirilecek dosyanın adı (Kuzenin bilgisayarında bu isimle inecek)
        self.app_name = "KickStudioUltimate.exe" 
        
        # Bu linki daha sonra (EXE'yi oluşturup GitHub'a yükleyince) dolduracağız.
        # Şimdilik boş kalması normal.
        self.exe_download_url = "" 

    def check_for_updates(self):
        # Program açılışını yavaşlatmamak için kontrolü arka planda yapıyoruz
        threading.Thread(target=self._check_thread, daemon=True).start()

    def _check_thread(self):
        try:
            # GitHub'daki version.txt dosyasını oku
            response = requests.get(self.version_url, timeout=5)
            if response.status_code == 200:
                remote_ver = response.text.strip()
                # Eğer internetteki sürüm (örn 1.1), bizden (1.0) büyükse:
                if float(remote_ver) > float(self.current_version):
                    self.parent_window.after(0, lambda: self._ask_to_update(remote_ver))
        except Exception:
            pass # İnternet yoksa sessizce devam et

    def _ask_to_update(self, new_ver):
        # Kullanıcıya soran pencere
        msg = ctk.CTkToplevel(self.parent_window)
        msg.title("Güncelleme")
        msg.geometry("400x200")
        msg.resizable(False, False)
        msg.attributes("-topmost", True)
        
        ctk.CTkLabel(msg, text=f"Yeni Sürüm Bulundu: v{new_ver}", font=("Arial", 16, "bold")).pack(pady=20)
        ctk.CTkLabel(msg, text="Otomatik indirip kurmak ister misin?", text_color="gray").pack(pady=5)
        
        btn_frame = ctk.CTkFrame(msg, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Evet, Güncelle", fg_color="#2CC985", 
                      command=lambda: [msg.destroy(), self._start_download_gui()]).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Hayır", fg_color="#D32F2F", 
                      command=msg.destroy).pack(side="left", padx=10)

    def _start_download_gui(self):
        # İndirme çubuğu penceresi
        self.dl_win = ctk.CTkToplevel(self.parent_window)
        self.dl_win.title("İndiriliyor...")
        self.dl_win.geometry("400x150")
        self.dl_win.resizable(False, False)
        self.dl_win.attributes("-topmost", True)
        
        self.lbl_status = ctk.CTkLabel(self.dl_win, text="Yeni sürüm indiriliyor...", font=("Arial", 14))
        self.lbl_status.pack(pady=20)
        
        self.progress = ctk.CTkProgressBar(self.dl_win, width=300, progress_color="#2CC985")
        self.progress.set(0)
        self.progress.pack(pady=10)
        
        threading.Thread(target=self._download_and_install, daemon=True).start()

    def _download_and_install(self):
        try:
            # Eğer indirme linki boşsa hata verme, uyarı ver
            if not self.exe_download_url:
                self.parent_window.after(0, lambda: self.lbl_status.configure(text="HATA: İndirme linki ayarlanmamış!"))
                return

            save_path = "update_temp.exe"
            response = requests.get(self.exe_download_url, stream=True, timeout=15)
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            with open(save_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    size = file.write(data)
                    downloaded += size
                    if total_size > 0:
                        perc = downloaded / total_size
                        self.parent_window.after(0, lambda p=perc: self.progress.set(p))
            
            self.parent_window.after(0, lambda: self.lbl_status.configure(text="Tamamlandı! Program yeniden başlatılıyor..."))
            time.sleep(2)
            
            # Windows için güncelleme betiği
            self._create_bat_and_restart()
            
        except Exception as e:
            self.parent_window.after(0, lambda: self.lbl_status.configure(text=f"Hata: {str(e)}"))

    def _create_bat_and_restart(self):
        # Bu kısım sadece Windows'ta çalışır
        if os.name != 'nt':
            return 

        bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{self.app_name}"
rename "update_temp.exe" "{self.app_name}"
start "" "{self.app_name}"
del "%~f0"
"""
        with open("updater.bat", "w") as f:
            f.write(bat_script)
            
        subprocess.Popen("updater.bat", shell=True)
        self.parent_window.after(0, self.parent_window.destroy)
        sys.exit()