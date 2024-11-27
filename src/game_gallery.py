import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import pyudev
import threading
import time
import shutil


class GameCarouselApp:
    def __init__(self, master, roms_directory, images_directory, logo_path):
        self.master = master
        self.roms_directory = roms_directory
        self.images_directory = images_directory
        self.logo_path = logo_path
        self.usb_mount_point = "/media/usb"
        self.current_game_process = None

        self.master.title("Carrusel de Juegos")
        self.master.attributes("-fullscreen", True)

        self.start_usb_monitoring()
        
        self.roms = self.get_roms()
        self.current_index = 0

        self.create_widgets()

        self.master.bind("<Left>", self.move_left)
        self.master.bind("<Right>", self.move_right)
        self.master.bind("<Return>", self.play_game)
        self.master.bind("<Escape>", self.return_to_gallery)

        self.update_carousel()
        self.update_progress_bar()

    def start_usb_monitoring(self):
        self.usb_thread = threading.Thread(target=self.monitor_usb, daemon=True)
        self.usb_thread.start()

    def get_roms(self):
        return sorted([
            rom for rom in os.listdir(self.roms_directory)
            if rom.endswith('.gba') or rom.endswith('.sfc')
        ])

    def get_image_path(self, rom_name):
        base_name = os.path.splitext(rom_name)[0]
        for ext in ['.png', '.jpg', '.jpeg']:
            image_path = os.path.join(self.images_directory, f"{base_name}{ext}")
            if os.path.exists(image_path):
                return image_path
        return None

    def monitor_usb(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='block', device_type='disk')

        observer = pyudev.MonitorObserver(monitor, self.handle_device_event)
        observer.start()

    def handle_device_event(self, action, device):
        if action == "add" and device.get("ID_BUS") == "usb":
            time.sleep(2)
            mount_point = self.get_mount_point(device)
            if mount_point:
                threading.Thread(target=self.handle_usb_inserted, args=(mount_point,), daemon=True).start()

    def get_mount_point(self, device):
        device_name = device.device_node
        try:
            mount_output = subprocess.check_output(f"lsblk -o MOUNTPOINT -nr {device_name}", shell=True).decode().strip()
            return mount_output if mount_output else None
        except subprocess.CalledProcessError:
            return None

    def handle_usb_inserted(self, mount_point):
        if self.current_game_process and self.current_game_process.poll() is None:
            self.current_game_process.terminate()
            self.current_game_process.wait()

        valid_extensions = (".gba", ".sfc")
        new_games = [
            file for file in os.listdir(mount_point)
            if file.endswith(valid_extensions) and not os.path.exists(os.path.join(self.roms_directory, file))
        ]

        if not new_games:
            self.show_notification("No se encontraron nuevos juegos en la USB.", duration=5000)
            subprocess.run(["sudo", "umount", mount_point])
            self.start_usb_monitoring()
            return

        self.show_notification("Copiando juegos desde la USB...")

        for game in new_games:
            source_path = os.path.join(mount_point, game)
            destination_path = os.path.join(self.roms_directory, game)
            try:
                shutil.copy2(source_path, destination_path)
            except Exception as e:
                print(f"Error al copiar {game}: {e}")

        self.show_notification(f"Se copiaron {len(new_games)} nuevo(s) juego(s) desde la USB. Ahora puedes retirar la USB de forma segura.", duration=5000)
        subprocess.run(["sudo", "umount", mount_point])
        time.sleep(8)
        self.roms.extend(new_games)
        self.roms = sorted(self.roms)
        self.update_carousel()

        self.show_notification("¡Bienvenido!\n\nSelecciona un juego:\n", persistent=True)
        self.start_usb_monitoring()

    def return_to_gallery(self, event=None):
        if self.current_game_process and self.current_game_process.poll() is None:
            try:
                self.current_game_process.terminate()
                self.current_game_process.wait()
                self.master.focus()
                self.show_notification("Juego cerrado y regreso a la galería.")
            except Exception as e:
                self.show_notification("No se pudo cerrar el juego.")
        else:
            print("No hay juegos en ejecución para cerrar.")

    def show_notification(self, message, duration=3000, persistent=False):
        self.message_label.config(text=message)
        self.master.update_idletasks()
        if not persistent:
            self.master.after(duration, lambda: self.message_label.config(text="¡Bienvenido!\n\nSelecciona un juego:\n"))

    def create_widgets(self):
        self.main_frame = tk.Frame(self.master, bg="#1E1940")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.header_frame = tk.Frame(self.main_frame, bg="#1E1940")
        self.header_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)

        self.logo_label = tk.Label(self.header_frame, bg="#1E1940")
        self.logo_label.pack(side=tk.LEFT)
        if self.logo_path and os.path.exists(self.logo_path):
            logo_img = Image.open(self.logo_path)
            logo_img = logo_img.resize((350, 200), Image.ANTIALIAS)
            tk_logo_img = ImageTk.PhotoImage(logo_img)
            self.logo_label.config(image=tk_logo_img)
            self.logo_label.image = tk_logo_img

        self.controls_label = tk.Label(self.header_frame, text="Amarillo 1- Sal del juego\nAmarillo 2- Selecciona un juego\nBlanco - Configuración de controles",
                                       bg="#1E1940", fg="#F2AEE0", font=("Fifties Movies", 14), justify=tk.RIGHT)
        self.controls_label.pack(side=tk.RIGHT)
        
        self.message_label = tk.Label(self.main_frame, text="¡Bienvenido!\n\nSelecciona un juego:\n",
                                      bg="#1E1940", fg="#F2AEE0", font=("Fifties Movies", 24))
        self.message_label.pack(side=tk.TOP, pady=(10, 0))

        self.carousel_frame = tk.Frame(self.main_frame, bg="#1E1940")
        self.carousel_frame.pack(fill=tk.BOTH, expand=True)

        self.game_labels = {
            "left": tk.Label(self.carousel_frame, bg="#1E1940"),
            "center": tk.Label(self.carousel_frame, bg="#1E1940"),
            "right": tk.Label(self.carousel_frame, bg="#1E1940"),
        }

        self.game_labels["left"].pack(side=tk.LEFT, expand=True, padx=10)
        self.game_labels["center"].pack(side=tk.LEFT, expand=True, padx=10)
        self.game_labels["right"].pack(side=tk.LEFT, expand=True, padx=10)

        self.progress_frame = tk.Frame(self.main_frame, bg="#1E1940")
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=20)

    def update_carousel(self):
        left_index = (self.current_index - 1) % len(self.roms)
        right_index = (self.current_index + 1) % len(self.roms)

        self.update_game_window(self.game_labels["left"], self.roms[left_index], size=(250, 250))
        self.update_game_window(self.game_labels["center"], self.roms[self.current_index], size=(400, 400), is_selected=True)
        self.update_game_window(self.game_labels["right"], self.roms[right_index], size=(250, 250))

    def update_game_window(self, label, rom_name, size, is_selected=False):
        image_path = self.get_image_path(rom_name)
        if not image_path:
            image_path = self.get_image_path("logo")
        img = Image.open(image_path).resize(size, Image.ANTIALIAS)
        tk_img = ImageTk.PhotoImage(img)
        label.config(image=tk_img)
        label.image = tk_img

        title = os.path.splitext(rom_name)[0]
        if len(title) > 23:
            title = title[:20] + "..."
        label.config(
            text=title + "\n",
            compound=tk.BOTTOM,
            fg="white" if not is_selected else "#44F2E1",
            font=("Fifties Movies", 16 if not is_selected else 22, "bold"),
        )

    def move_left(self, event=None):
        self.current_index = (self.current_index - 1) % len(self.roms)
        self.update_carousel()
        self.update_progress_bar()

    def move_right(self, event=None):
        self.current_index = (self.current_index + 1) % len(self.roms)
        self.update_carousel()
        self.update_progress_bar()

    def play_game(self, event=None):
        selected_game = self.roms[self.current_index]
        rom_path = os.path.join(self.roms_directory, selected_game)

        if self.current_game_process and self.current_game_process.poll() is None:
            self.show_notification("Ya hay un juego en ejecución. Ciérralo antes de abrir otro.")
            return

        self.current_game_process = subprocess.Popen(["mednafen", "-fs", "1", rom_path])

    def update_progress_bar(self):
        total_games = len(self.roms)
        self.progress_bar["maximum"] = total_games
        self.progress_bar["value"] = self.current_index + 1

# Directorios
roms_directory = "/home/admin/Games"
images_directory = "/home/admin/Games/images"
logo_path = "/home/admin/proyecto_final/Logo2.png"

# Iniciar aplicación
root = tk.Tk()
app = GameCarouselApp(root, roms_directory, images_directory, logo_path)
root.mainloop()
