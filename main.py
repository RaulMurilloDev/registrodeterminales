import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import cv2
from PIL import Image, ImageTk
import os
import datetime
import threading
import time
import platform

# Importar el servicio de cámara corregido
from camera_service import CameraService

# --- Main Application ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Captura de Troquelados - Raspberry Pi/Linux")
        self.root.geometry("1100x750")
        
        # Servicio de cámara
        self.camera = CameraService()
        
        # Variables
        self.storage_path = os.path.join(os.getcwd(), "capturas")
        os.makedirs(self.storage_path, exist_ok=True)
        self.current_frame = None
        self.preview_image = None
        self.streaming = False
        self.selected_camera = None
        self.camera_list = []
        
        # Para evitar bloqueos de GUI
        self.preview_lock = threading.Lock()
        
        self._build_ui()
        self.refresh_cameras()
        
        # Configurar cierre limpio
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _build_ui(self):
        style = tb.Style(theme="darkly")

        # --- Frames principales ---
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame superior para controles
        top_frame = ttk.LabelFrame(main_frame, text="Configuración")
        top_frame.pack(fill="x", padx=5, pady=5)

        # Frame para vista previa
        camera_frame = ttk.LabelFrame(main_frame, text="Vista Previa de Cámara")
        camera_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame para captura
        capture_frame = ttk.LabelFrame(main_frame, text="Captura")
        capture_frame.pack(fill="x", padx=5, pady=5)

        # --- Controles superiores (2 columnas) ---
        # Columna izquierda
        left_col = ttk.Frame(top_frame)
        left_col.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ttk.Button(left_col, text="📁 Seleccionar carpeta", 
                  command=self.select_folder, 
                  width=20).pack(pady=5)
        
        self.folder_label = ttk.Label(left_col, text=self.storage_path, 
                                     wraplength=300)
        self.folder_label.pack(pady=5)

        # Columna derecha
        right_col = ttk.Frame(top_frame)
        right_col.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ttk.Label(right_col, text="Cámara:").pack(anchor="w")
        
        camera_select_frame = ttk.Frame(right_col)
        camera_select_frame.pack(fill="x", pady=5)
        
        self.camera_select = ttk.Combobox(camera_select_frame, state="readonly", width=30)
        self.camera_select.pack(side="left", padx=(0, 5))
        
        ttk.Button(camera_select_frame, text="🔄 Refrescar", 
                  command=self.refresh_cameras).pack(side="left", padx=2)
        
        self.camera_btn = ttk.Button(camera_select_frame, text="▶ Iniciar", 
                                    command=self.toggle_camera)
        self.camera_btn.pack(side="left", padx=2)

        # Info de cámara
        self.camera_info_label = ttk.Label(right_col, text="No hay cámara activa")
        self.camera_info_label.pack(pady=5)

        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # --- Vista previa de cámara ---
        self.preview_label = ttk.Label(camera_frame, 
                                      text="🖥️ Vista previa\n\nSelecciona e inicia una cámara", 
                                      anchor="center", 
                                      background="#000", 
                                      foreground="#0f0",
                                      font=("Arial", 12))
        self.preview_label.pack(fill="both", expand=True)

        # --- Controles de captura ---
        capture_controls = ttk.Frame(capture_frame)
        capture_controls.pack(fill="x", padx=10, pady=10)

        ttk.Label(capture_controls, text="Número de parte / Kanban:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.part_entry = ttk.Entry(capture_controls, width=30)
        self.part_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.part_entry.bind("<Return>", lambda e: self.capture())  # Capturar con Enter
        
        ttk.Button(capture_controls, text="📸 CAPTURAR", 
                  command=self.capture, 
                  bootstyle="success",
                  width=15).grid(row=0, column=2, padx=5, pady=5)
        
        # Contador de capturas
        self.counter_label = ttk.Label(capture_controls, text="Capturas: 0")
        self.counter_label.grid(row=1, column=0, columnspan=3, pady=5)
        self.capture_count = 0

        capture_controls.columnconfigure(1, weight=1)

    # --- Funciones de carpeta ---
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.storage_path)
        if folder:
            self.storage_path = folder
            self.folder_label.config(text=folder)
            os.makedirs(folder, exist_ok=True)

    # --- Funciones de cámara ---
    def refresh_cameras(self):
        """Busca cámaras disponibles"""
        self.camera_list = self.camera.find_cameras()
        
        if not self.camera_list:
            self.camera_select['values'] = ["No se encontraron cámaras"]
            self.camera_select.set("No se encontraron cámaras")
            messagebox.showwarning("Advertencia", 
                                  "No se encontraron cámaras conectadas.\n"
                                  "Conecta una cámara USB y vuelve a intentar.")
        else:
            # Mostrar nombres amigables
            camera_names = []
            for cam in self.camera_list:
                if isinstance(cam, str) and cam.startswith("/dev/video"):
                    camera_names.append(f"Cámara USB ({cam})")
                else:
                    camera_names.append(f"Cámara {cam}")
            
            self.camera_select['values'] = camera_names
            self.camera_select.current(0)
            self.selected_camera = self.camera_list[0]

    def toggle_camera(self):
        """Inicia/Detiene la cámara"""
        if not self.streaming:
            self.start_camera()
        else:
            self.stop_camera()

    def start_camera(self):
        """Inicia la transmisión de la cámara"""
        if not self.camera_list:
            messagebox.showerror("Error", "No hay cámaras disponibles")
            return

        try:
            # Obtener índice seleccionado
            selected_idx = self.camera_select.current()
            if selected_idx < 0:
                selected_idx = 0
            self.selected_camera = self.camera_list[selected_idx]
        except:
            messagebox.showerror("Error", "Selecciona una cámara válida")
            return

        # Intentar iniciar cámara
        if not self.camera.start(self.selected_camera):
            messagebox.showerror("Error", 
                                f"No se pudo iniciar la cámara.\n"
                                f"Verifica que esté conectada y no esté en uso por otra aplicación.")
            return

        # Actualizar interfaz
        self.streaming = True
        self.camera_btn.config(text="⏹ Detener", bootstyle="danger")
        self.camera_select.config(state="disabled")
        
        # Mostrar información de la cámara
        info = self.camera.get_camera_info()
        info_text = f"Resolución: {info.get('width', '?')}x{info.get('height', '?')} | FPS: {info.get('fps', '?')}"
        self.camera_info_label.config(text=info_text)
        
        # Iniciar actualización de vista previa
        self.update_preview()

    def stop_camera(self):
        """Detiene la transmisión de la cámara"""
        self.streaming = False
        self.camera.stop()
        self.camera_btn.config(text="▶ Iniciar", bootstyle="default")
        self.camera_select.config(state="readonly")
        self.camera_info_label.config(text="Cámara detenida")
        
        # Limpiar vista previa
        self.preview_label.config(image='', 
                                 text="🖥️ Vista previa\n\nCámara detenida",
                                 foreground="#888")

    def update_preview(self):
        """Actualiza la vista previa de la cámara"""
        if not self.streaming:
            return

        frame = self.camera.get_frame()
        if frame is not None:
            # Redimensionar para vista previa (mantener aspect ratio)
            h, w = frame.shape[:2]
            max_size = (800, 600)
            
            # Calcular nuevo tamaño manteniendo proporción
            ratio = min(max_size[0]/w, max_size[1]/h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            
            if new_w > 0 and new_h > 0:
                frame_resized = cv2.resize(frame, (new_w, new_h))
                
                # Dibujar información en el frame
                part_number = self.part_entry.get().strip() or "N/A"
                now_text = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
                
                # Texto blanco con fondo semitransparente para mejor legibilidad
                text = f"{part_number} | {now_text}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                thickness = 2
                
                # Obtener tamaño del texto
                (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
                
                # Dibujar fondo para el texto
                cv2.rectangle(frame_resized, 
                            (10, 10), 
                            (10 + text_w + 10, 10 + text_h + 10), 
                            (0, 0, 0), 
                            -1)
                
                # Dibujar texto
                cv2.putText(frame_resized, text, (20, 10 + text_h), 
                           font, font_scale, (0, 255, 0), thickness)

                # Convertir a formato para Tkinter
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                self.preview_image = ImageTk.PhotoImage(img)
                
                self.preview_label.config(image=self.preview_image, text="")
        
        # Programar próxima actualización (ajustar FPS)
        self.root.after(30, self.update_preview)  # ~33 FPS

    # --- Captura de imágenes ---
    def capture(self):
        """Captura una imagen"""
        if not self.streaming or self.camera.cap is None:
            messagebox.showerror("Error", "Inicia la cámara primero")
            return

        frame = self.camera.get_frame()
        if frame is None:
            messagebox.showerror("Error", "No se pudo obtener imagen de la cámara")
            return

        part_number = self.part_entry.get().strip()

        # Uncomment for regular app.
        # if not part_number:
        #     messagebox.showerror("Error", "Ingresa un número de parte / Kanban")
        #     self.part_entry.focus()
        #     return
        

        # Crear nombre de archivo
        now = datetime.datetime.now()
        filename = f"{part_number}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.storage_path, filename)

        try:
            # Añadir texto a la imagen guardada
            now_text = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Para la imagen guardada, texto más grande
            cv2.putText(frame, f"Parte: {part_number}", (20, 40),
                       font, 1.2, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Fecha: {now_text}", (20, 80),
                       font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

            # Guardar imagen
            cv2.imwrite(filepath, frame)
            
            # Actualizar contador
            self.capture_count += 1
            self.counter_label.config(text=f"Capturas: {self.capture_count}")
            
            # Mostrar confirmación 
            # Uncomment for regular app
            # messagebox.showinfo("✅ Captura exitosa", 
            #                   f"Imagen guardada en:\n{filepath}")
            
            # Limpiar campo y preparar para siguiente captura
            self.part_entry.delete(0, "end")
            self.part_entry.focus()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{str(e)}")

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.stop_camera()
        self.root.destroy()

# --- Ejecutar aplicación ---
if __name__ == "__main__":
    print("🚀 Iniciando aplicación de captura...")
    print(f"Sistema: {platform.system()}")
    
    root = tb.Window(themename="darkly")
    app = App(root)
    root.mainloop()