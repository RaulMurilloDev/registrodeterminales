import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import cv2
from PIL import Image, ImageTk
import os
import datetime
import base64

# --- Camera Service ---
class CameraService:
    def __init__(self):
        self.cap = None
        self.index = None

    def find_cameras(self):
        """Retorna una lista de índices de cámaras disponibles"""
        cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cameras.append(i)
                cap.release()
        return cameras

    def start(self, index):
        self.stop()
        self.index = index
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = None
            return False
        return True

    def get_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None

# --- Main Application ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Captura de Troquelados")
        self.root.geometry("1000x700")
        self.camera = CameraService()
        self.storage_path = os.getcwd()
        self.current_frame = None
        self.preview_image = None
        self.streaming = False
        self.selected_camera_index = None

        self._build_ui()
        self.refresh_cameras()

    def _build_ui(self):
        style = tb.Style(theme="darkly")

        # --- Frames ---
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        camera_frame = ttk.LabelFrame(self.root, text="Cámara / Video")
        camera_frame.pack(fill="both", expand=True, padx=10, pady=10)

        part_frame = ttk.LabelFrame(self.root, text="Captura de Número de Parte / Kanban")
        part_frame.pack(fill="x", padx=10, pady=10)

        # --- Top controls ---
        ttk.Button(top_frame, text="Seleccionar carpeta", command=self.select_folder).grid(row=0, column=0, padx=5, pady=5)
        self.folder_label = ttk.Label(top_frame, text=self.storage_path)
        self.folder_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(top_frame, text="Cámara:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.camera_select = ttk.Combobox(top_frame, state="readonly")
        self.camera_select.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(top_frame, text="Refrescar cámaras", command=self.refresh_cameras).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(top_frame, text="Iniciar Cámara", command=self.start_camera).grid(row=1, column=3, padx=5, pady=5)

        # --- Camera preview ---
        self.preview_label = ttk.Label(camera_frame, text="No hay preview", anchor="center", background="#000", foreground="#0f0")
        self.preview_label.pack(fill="both", expand=True)

        # --- Part capture ---
        ttk.Label(part_frame, text="Número de parte / Kanban:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.part_entry = ttk.Entry(part_frame)
        self.part_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(part_frame, text="📸 Capturar", command=self.capture).grid(row=0, column=2, padx=5, pady=5)
        part_frame.columnconfigure(1, weight=1)

    # --- Folder selection ---
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.storage_path = folder
            self.folder_label.config(text=folder)

    # --- Camera functions ---
    def refresh_cameras(self):
        cameras = self.camera.find_cameras()
        self.camera_select['values'] = cameras
        if cameras:
            self.camera_select.current(0)
            self.selected_camera_index = cameras[0]

    def start_camera(self):
        try:
            self.selected_camera_index = int(self.camera_select.get())
        except:
            messagebox.showerror("Error", "Selecciona una cámara válida")
            return

        if not self.camera.start(self.selected_camera_index):
            messagebox.showerror("Error", f"No se pudo iniciar la cámara {self.selected_camera_index}")
            return
        self.streaming = True
        self.update_preview()

    def update_preview(self):
        if not self.streaming:
            return
        frame = self.camera.get_frame()
        if frame is not None:
            # Dibujar número de parte y hora en verde fosforescente
            part_number = self.part_entry.get().strip() or "N/A"
            now_text = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
            cv2.putText(frame, f"{part_number} {now_text}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)

            # Convertir a PIL Image y luego ImageTk
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            # Escalar un 30% más grande (manteniendo ratio)
            w, h = img.size
            img = img.resize((int(w*1.3), int(h*1.3)), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image, text="")
        self.root.after(30, self.update_preview)

    # --- Capture function ---
    def capture(self):
        frame = self.camera.get_frame()
        if frame is None:
            messagebox.showerror("Error", "No hay frame para capturar")
            return

        part_number = self.part_entry.get().strip()
        if not part_number:
            messagebox.showerror("Error", "Ingresa un número de parte / Kanban")
            return

        now = datetime.datetime.now()
        filename = f"{part_number}_{now.strftime('%m_%d_%Y_%H_%M_%S')}.png"
        filepath = os.path.join(self.storage_path, filename)

        # Dibujar en la imagen antes de guardar
        now_text = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")  # hora + fecha
        cv2.putText(frame, f"{part_number} {now_text}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)

        cv2.imwrite(filepath, frame)

        messagebox.showinfo("Captura", f"Imagen guardada:\n{filepath}")

        # --- Limpiar campo y volver a poner foco ---
        self.part_entry.delete(0, "end")  # limpia el Entry
        self.part_entry.focus()            # pone el cursor listo para el siguiente

# --- Run app ---
if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = App(root)
    root.mainloop()
