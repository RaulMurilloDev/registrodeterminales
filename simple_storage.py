import os
import datetime
from tkinter import filedialog

class SimpleStorage:
    """Gestor de almacenamiento simple sin dependencias extra"""
    
    def __init__(self, base_folder=None):
        self.folder = base_folder or os.path.join(os.getcwd(), "capturas")
        os.makedirs(self.folder, exist_ok=True)
    
    def get_path(self):
        return self.folder
    
    def select_folder(self):
        """Permite al usuario seleccionar una carpeta"""
        folder = filedialog.askdirectory(initialdir=self.folder)
        if folder:
            self.folder = folder
            os.makedirs(folder, exist_ok=True)
        return self.folder
    
    def save_image(self, image_array, part_number):
        """Guarda una imagen con número de parte"""
        now = datetime.datetime.now()
        filename = f"{part_number}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.folder, filename)
        
        try:
            import cv2
            cv2.imwrite(filepath, image_array)
            return filepath
        except Exception as e:
            print(f"Error al guardar con OpenCV: {e}")
            
            # Intentar con PIL
            try:
                from PIL import Image
                if isinstance(image_array, Image.Image):
                    image_array.save(filepath)
                else:
                    # Convertir numpy array a PIL
                    image_pil = Image.fromarray(image_array)
                    image_pil.save(filepath)
                return filepath
            except Exception as e2:
                print(f"Error al guardar con PIL: {e2}")
                return None
    
    def get_image_count(self):
        """Cuenta cuántas imágenes hay en la carpeta"""
        if not os.path.exists(self.folder):
            return 0
        
        count = 0
        for file in os.listdir(self.folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                count += 1
        
        return count
    
    def list_images(self):
        """Lista todas las imágenes disponibles"""
        images = []
        if not os.path.exists(self.folder):
            return images
        
        for file in os.listdir(self.folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                images.append({
                    'filename': file,
                    'path': os.path.join(self.folder, file),
                    'size': os.path.getsize(os.path.join(self.folder, file))
                })
        
        return images