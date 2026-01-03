# CapturaTroquelados (ttkbootstrap)

Instalación:
1. `python -m pip install -r requirements.txt`
2. `python main.py`

Funciones:
- Detecta cámaras (0..5)
- Preview en vivo
- Seleccionar carpeta destino
- Capturar imagen con texto (número de parte + fecha/hora)
- Campo de serial se limpia automáticamente al guardar

Notas:
- Si tu cámara no aparece, desconecta otras apps que la estén usando (Teams, Zoom, Camera).
- Para cámaras industriales, es posible que necesites ajustar backend en `camera_service.py` (MSMF/DSHOW).


para empaquetar utilizar:
source .venv/bin/activate
rm -rf build/ dist/

pyinstaller --onefile --name CamaraDeterminales \
  --collect-all PIL \
  --collect-all ttkbootstrap \
  main.py