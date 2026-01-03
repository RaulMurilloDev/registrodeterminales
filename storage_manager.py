import os
import json
import datetime
from tkinter import filedialog
import shutil  # Reemplaza algunas operaciones de archivos

class StorageManager:
    def __init__(self, base_folder=None):
        if base_folder:
            self.folder = base_folder
        else:
            self.folder = os.path.join(os.getcwd(), "capturas")
        
        os.makedirs(self.folder, exist_ok=True)
        
        # Crear estructura de carpetas
        self.subfolders = {
            "images": os.path.join(self.folder, "images"),
            "annotations": os.path.join(self.folder, "annotations"),
            "exports": os.path.join(self.folder, "exports"),
            "yolo": os.path.join(self.folder, "exports", "yolo"),
            "coco": os.path.join(self.folder, "exports", "coco")
        }
        
        for folder in self.subfolders.values():
            os.makedirs(folder, exist_ok=True)

    def get_path(self, subfolder="images"):
        """Retorna la ruta de un subfolder específico"""
        return self.subfolders.get(subfolder, self.folder)

    def ask_folder(self):
        """Pide al usuario seleccionar una carpeta"""
        path = filedialog.askdirectory(initialdir=self.folder)
        if path:
            self.folder = path
            # Recrear estructura en nueva ubicación
            for key in self.subfolders.keys():
                new_sub = os.path.join(path, *key.split('/')) if '/' in key else os.path.join(path, key)
                os.makedirs(new_sub, exist_ok=True)
                self.subfolders[key] = new_sub
        return self.folder

    def save_image(self, image, serial, metadata=None):
        """Guarda una imagen con metadatos"""
        now = datetime.datetime.now()
        
        # Nombre de archivo
        filename = f"{serial}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        image_path = os.path.join(self.subfolders["images"], filename)
        
        # Guardar imagen
        try:
            import cv2
            import numpy as np
            
            # Si la imagen es un array de numpy (OpenCV)
            if isinstance(image, np.ndarray):
                cv2.imwrite(image_path, image)
            else:
                # Asumir que es PIL Image
                image.save(image_path)
        except Exception as e:
            # Fallback simple
            try:
                if hasattr(image, 'save'):
                    image.save(image_path)
                else:
                    raise ValueError(f"Formato de imagen no soportado: {type(image)}")
            except Exception as e2:
                print(f"Error al guardar imagen: {e2}")
                return None
        
        # Guardar metadatos si se proporcionan
        if metadata:
            meta_filename = f"{serial}_{now.strftime('%Y%m%d_%H%M%S')}.json"
            meta_path = os.path.join(self.subfolders["annotations"], meta_filename)
            
            metadata.update({
                "image_path": image_path,
                "serial": serial,
                "timestamp": now.isoformat(),
                "filename": filename
            })
            
            try:
                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error al guardar metadatos: {e}")
        
        return image_path

    def save_annotation(self, image_path, annotations, format="yolo"):
        """Guarda anotaciones en diferentes formatos"""
        # Obtener nombre base del archivo
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        if format.lower() == "yolo":
            return self._save_yolo_annotation(base_name, annotations, image_path)
        elif format.lower() == "coco":
            return self._save_coco_annotation(base_name, annotations, image_path)
        else:
            raise ValueError(f"Formato de anotación no soportado: {format}")

    def _save_yolo_annotation(self, base_name, annotations, image_path):
        """Guarda anotaciones en formato YOLO"""
        # Formato YOLO: class_id x_center y_center width height (normalizado 0-1)
        
        # Primero obtener dimensiones de la imagen
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                return None
            img_height, img_width = img.shape[:2]
        except:
            # Si no podemos leer la imagen, usar valores por defecto
            img_width, img_height = 640, 480
        
        # Crear archivo .txt
        txt_path = os.path.join(self.subfolders["yolo"], "labels", f"{base_name}.txt")
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        
        with open(txt_path, 'w') as f:
            for ann in annotations:
                # ann debe ser dict con: class_id, x_min, y_min, x_max, y_max
                class_id = ann.get("class_id", 0)
                
                # Convertir coordenadas absolutas a normalizadas
                x_min = ann.get("x_min", 0)
                y_min = ann.get("y_min", 0)
                x_max = ann.get("x_max", 0)
                y_max = ann.get("y_max", 0)
                
                # Calcular valores normalizados
                x_center = ((x_min + x_max) / 2) / img_width
                y_center = ((y_min + y_max) / 2) / img_height
                width = (x_max - x_min) / img_width
                height = (y_max - y_min) / img_height
                
                # Escribir línea en formato YOLO
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        return txt_path

    def _save_coco_annotation(self, base_name, annotations, image_path):
        """Guarda anotaciones en formato COCO (simplificado)"""
        # Esto es una versión simplificada del formato COCO
        import json
        import datetime
        
        coco_data = {
            "info": {
                "description": "Dataset de inspección automática",
                "version": "1.0",
                "year": datetime.datetime.now().year,
                "date_created": datetime.datetime.now().isoformat()
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # Añadir categorías (deberían venir de configuraciones)
        categories = [
            {"id": 0, "name": "defecto", "supercategory": "defect"},
            {"id": 1, "name": "correcto", "supercategory": "ok"}
        ]
        coco_data["categories"] = categories
        
        # Añadir información de la imagen
        try:
            import cv2
            img = cv2.imread(image_path)
            img_height, img_width = img.shape[:2]
        except:
            img_width, img_height = 640, 480
        
        image_info = {
            "id": 1,  # Debería ser único por imagen
            "file_name": os.path.basename(image_path),
            "width": img_width,
            "height": img_height,
            "date_captured": datetime.datetime.now().isoformat()
        }
        coco_data["images"].append(image_info)
        
        # Añadir anotaciones
        for i, ann in enumerate(annotations):
            annotation = {
                "id": i + 1,
                "image_id": 1,
                "category_id": ann.get("class_id", 0),
                "bbox": [
                    ann.get("x_min", 0),
                    ann.get("y_min", 0),
                    ann.get("x_max", 0) - ann.get("x_min", 0),
                    ann.get("y_max", 0) - ann.get("y_min", 0)
                ],
                "area": (ann.get("x_max", 0) - ann.get("x_min", 0)) * (ann.get("y_max", 0) - ann.get("y_min", 0)),
                "iscrowd": 0
            }
            coco_data["annotations"].append(annotation)
        
        # Guardar archivo JSON
        json_path = os.path.join(self.subfolders["coco"], f"{base_name}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        with open(json_path, 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        return json_path

    def export_for_training(self, format="yolo", classes=None):
        """Exporta imágenes y anotaciones para entrenamiento"""
        if format.lower() == "yolo":
            return self._export_yolo_format(classes)
        elif format.lower() == "coco":
            return self._export_coco_format(classes)
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _export_yolo_format(self, classes=None):
        """Exporta en formato YOLO para entrenamiento"""
        # Crear estructura YOLO completa
        yolo_folder = self.subfolders["yolo"]
        
        # Carpetas dentro de YOLO
        for subset in ["train", "val", "test"]:
            os.makedirs(os.path.join(yolo_folder, "images", subset), exist_ok=True)
            os.makedirs(os.path.join(yolo_folder, "labels", subset), exist_ok=True)
        
        # Configurar clases por defecto si no se proporcionan
        if classes is None:
            classes = {
                0: "defecto",
                1: "correcto"
            }
        
        # Crear dataset.yaml
        dataset_yaml = f"""# Dataset YOLO generado automáticamente
path: {os.path.abspath(yolo_folder)}
train: images/train
val: images/val
test: images/test

# Número de clases
nc: {len(classes)}

# Nombres de clases
names: {classes}
"""
        
        yaml_path = os.path.join(yolo_folder, "dataset.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(dataset_yaml)
        
        print(f"✅ Estructura YOLO creada en: {yolo_folder}")
        print(f"📄 Configuración guardada en: {yaml_path}")
        
        return yolo_folder

    def _export_coco_format(self, classes=None):
        """Exporta en formato COCO (simplificado)"""
        coco_folder = self.subfolders["coco"]
        
        # Configurar clases por defecto
        if classes is None:
            classes = {
                0: "defecto",
                1: "correcto"
            }
        
        # Crear archivo de clases
        classes_path = os.path.join(coco_folder, "classes.txt")
        with open(classes_path, 'w', encoding='utf-8') as f:
            for class_id, class_name in classes.items():
                f.write(f"{class_id}:{class_name}\n")
        
        print(f"✅ Estructura COCO creada en: {coco_folder}")
        print(f"📄 Archivo de clases en: {classes_path}")
        
        return coco_folder

    def list_images(self, folder="images"):
        """Lista todas las imágenes en una carpeta"""
        images_path = self.subfolders.get(folder, folder)
        
        if not os.path.exists(images_path):
            return []
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        images = []
        
        for file in os.listdir(images_path):
            if os.path.splitext(file)[1].lower() in image_extensions:
                images.append({
                    "filename": file,
                    "path": os.path.join(images_path, file),
                    "size": os.path.getsize(os.path.join(images_path, file)),
                    "modified": datetime.datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(images_path, file))
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return images

    def get_statistics(self):
        """Obtiene estadísticas del dataset"""
        stats = {
            "total_images": 0,
            "total_annotations": 0,
            "by_class": {},
            "storage_size": 0
        }
        
        # Contar imágenes
        images = self.list_images("images")
        stats["total_images"] = len(images)
        
        # Calcular tamaño total
        stats["storage_size"] = sum(img["size"] for img in images)
        
        # Contar anotaciones (simplificado)
        annotations_path = self.subfolders["annotations"]
        if os.path.exists(annotations_path):
            annotation_files = [f for f in os.listdir(annotations_path) if f.endswith('.json')]
            stats["total_annotations"] = len(annotation_files)
        
        return stats

# --- Versión simplificada (si solo necesitas lo básico) ---
class SimpleStorageManager:
    """Versión simplificada sin dependencias extras"""
    def __init__(self, base_folder=None):
        if base_folder:
            self.folder = base_folder
        else:
            self.folder = os.path.join(os.getcwd(), "capturas")
        
        os.makedirs(self.folder, exist_ok=True)
    
    def get_path(self):
        return self.folder
    
    def ask_folder(self):
        path = filedialog.askdirectory(initialdir=self.folder)
        if path:
            self.folder = path
            os.makedirs(path, exist_ok=True)
        return self.folder
    
    def save_image(self, image, serial):
        """Guarda una imagen - versión simple"""
        now = datetime.datetime.now()
        filename = f"{serial}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(self.folder, filename)
        
        try:
            # Intentar guardar con OpenCV si está disponible
            import cv2
            if hasattr(cv2, 'imwrite'):
                cv2.imwrite(path, image)
                return path
        except:
            pass
        
        # Fallback: usar PIL si está disponible
        try:
            from PIL import Image
            if isinstance(image, Image.Image):
                image.save(path)
            return path
        except:
            # Si todo falla, guardar como archivo binario
            try:
                with open(path, 'wb') as f:
                    f.write(image)
                return path
            except Exception as e:
                print(f"Error crítico al guardar imagen: {e}")
                return None