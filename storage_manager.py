import os
from tkinter import filedialog
import datetime

class StorageManager:
    def __init__(self):
        self.folder = os.path.join(os.getcwd(), "capturas")
        os.makedirs(self.folder, exist_ok=True)

    def get_path(self):
        return self.folder

    def ask_folder(self):
        path = filedialog.askdirectory(initialdir=self.folder)
        if path:
            self.folder = path
        return self.folder

    def save_image(self, pil_image, serial):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{serial}_{now}.png"
        path = os.path.join(self.folder, filename)
        pil_image.save(path)
        return path
