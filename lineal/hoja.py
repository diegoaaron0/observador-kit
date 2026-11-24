"""Junta los fotogramas de muestra en una sola hoja de contacto para revisarlos de un vistazo.

uso:  python hoja.py PROYECTO/web [salida.png]
"""
import sys, os, re, glob
from PIL import Image

carpeta = sys.argv[1]
salida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(carpeta, "..", "hoja.png")

fs = sorted(glob.glob(os.path.join(carpeta, "m_*.png")),
            key=lambda f: float(re.findall(r"m_([\d.]+)\.png", os.path.basename(f))[0]))
if not fs:
    sys.exit("no hay fotogramas m_*.png: lánzalos con render.js --muestras")

w, h = 360, 640
cols = min(6, len(fs))
filas = (len(fs) + cols - 1) // cols
hoja = Image.new("RGB", (cols * w, filas * h), "#222")
for i, f in enumerate(fs):
    hoja.paste(Image.open(f).convert("RGB").resize((w, h)), ((i % cols) * w, (i // cols) * h))
hoja.save(os.path.abspath(salida))
print(f"{len(fs)} fotogramas  →  {os.path.abspath(salida)}")
