import cv2
import platform

class CameraService:
    def __init__(self):
        self.cap = None
        self.index = None
        self.system = platform.system()  # Detecta el sistema operativo

    def find_cameras(self):
        """Retorna una lista de índices de cámaras disponibles"""
        cameras = []
        
        # Diferentes métodos según el sistema operativo
        if self.system == "Windows":
            # Windows - probar con DSHOW
            for i in range(5):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    cameras.append(i)
                    cap.release()
                else:
                    # Intentar con MSMF si DSHOW falla
                    cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
                    if cap.isOpened():
                        cameras.append(i)
                        cap.release()
        
        elif self.system == "Linux":
            # Linux/Raspberry Pi - usar V4L2
            for i in range(5):
                # Probar diferentes índices y backends
                for api in [cv2.CAP_V4L2, cv2.CAP_ANY]:
                    cap = cv2.VideoCapture(i, api)
                    if cap.isOpened():
                        # Verificar si realmente puede obtener un frame
                        ret, frame = cap.read()
                        if ret:
                            cameras.append(i)
                            cap.release()
                            break  # Salir del loop de APIs si funciona
                        cap.release()
                    else:
                        # También probar con índice de dispositivo USB
                        dev_path = f"/dev/video{i}"
                        try:
                            cap = cv2.VideoCapture(dev_path)
                            if cap.isOpened():
                                ret, frame = cap.read()
                                if ret:
                                    cameras.append(dev_path)  # Guardar path en lugar de índice
                                    cap.release()
                                    break
                                cap.release()
                        except:
                            pass
        
        elif self.system == "Darwin":  # macOS
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras.append(i)
                    cap.release()
        
        return cameras

    def start(self, camera_id):
        """Inicia la cámara seleccionada"""
        self.stop()  # Detener cualquier cámara previa
        
        print(f"🔧 Intentando iniciar cámara: {camera_id} en {self.system}")
        
        if self.system == "Windows":
            # Intentar con DSHOW primero, luego MSMF
            for api in [cv2.CAP_DSHOW, cv2.CAP_MSMF]:
                self.cap = cv2.VideoCapture(camera_id, api)
                if self.cap.isOpened():
                    print(f"✅ Cámara {camera_id} iniciada con {api}")
                    self.index = camera_id
                    # Configurar propiedades básicas
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    return True
                if self.cap:
                    self.cap.release()
        
        elif self.system == "Linux":
            # Si camera_id es un string como "/dev/video0", usarlo directamente
            if isinstance(camera_id, str) and camera_id.startswith("/dev/video"):
                self.cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
            else:
                # Probar diferentes APIs para Linux
                for api in [cv2.CAP_V4L2, cv2.CAP_ANY]:
                    self.cap = cv2.VideoCapture(camera_id, api)
                    if self.cap.isOpened():
                        break
            
            if self.cap and self.cap.isOpened():
                print(f"✅ Cámara {camera_id} iniciada en Linux")
                self.index = camera_id
                # Configurar propiedades para Raspberry Pi
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                # Añadir buffers para mejor rendimiento
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return True
        
        elif self.system == "Darwin":  # macOS
            self.cap = cv2.VideoCapture(camera_id)
            if self.cap.isOpened():
                print(f"✅ Cámara {camera_id} iniciada en macOS")
                self.index = camera_id
                return True
        
        # Si llegamos aquí, falló
        if self.cap:
            self.cap.release()
            self.cap = None
        print(f"❌ No se pudo iniciar la cámara {camera_id}")
        return False

    def get_frame(self):
        """Obtiene un frame de la cámara"""
        if not self.cap:
            return None
        
        # Leer frame
        ret, frame = self.cap.read()
        
        if not ret:
            print("⚠️ No se pudo leer frame, reintentando...")
            # Intentar reconectar
            self.cap.release()
            if self.index is not None:
                self.start(self.index)
                ret, frame = self.cap.read() if self.cap else (False, None)
        
        return frame if ret else None

    def stop(self):
        """Detiene la cámara"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.index = None

    def get_camera_info(self):
        """Obtiene información de la cámara actual"""
        if not self.cap:
            return {}
        
        info = {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "index": self.index,
            "system": self.system
        }
        return info