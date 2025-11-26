import cv2

class CameraService:
    def __init__(self):
        self.cap = None
        self.index = None

    def start(self):
        # Primero DSHOW
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                self.cap = cap
                self.index = i
                print(f"🎥 Cámara iniciada en índice {i} (DSHOW)")
                return True
            cap.release()
        # fallback MSMF
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
            if cap.isOpened():
                self.cap = cap
                self.index = i
                print(f"🎥 Cámara iniciada en índice {i} (MSMF)")
                return True
            cap.release()
        return False

    def get_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None
