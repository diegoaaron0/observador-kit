"""
Prepara una escena animada: copia el HTML y la voz, y emite datos.json con
los tiempos de cada palabra.

Uso:  python construir.py PROYECTO escena.html [--sub-y 1690] [--clave "#ffd12e"]
"""
import os, sys, json, shutil, argparse

ap = argparse.ArgumentParser()
ap.add_argument("proyecto")
ap.add_argument("html")
ap.add_argument("--sub-y", type=int, default=1690)
ap.add_argument("--clave", default="#ffd12e")
ap.add_argument("--borde", default="#10131c")
ap.add_argument("--base", default="#ffffff")
ap.add_argument("--tamano", type=int, default=56)
a = ap.parse_args()

AQUI = os.path.dirname(os.path.abspath(__file__))
proy = os.path.abspath(a.proyecto)
salida = os.path.join(proy, "web")
os.makedirs(salida, exist_ok=True)

timing = json.load(open(os.path.join(proy, "timing.json"), encoding="utf-8"))

fuente_html = a.html if os.path.isabs(a.html) else (
    a.html if os.path.exists(a.html) else os.path.join(AQUI, a.html))
if not os.path.exists(fuente_html):
    sys.exit(f"no encuentro la escena: {a.html}")
shutil.copy(fuente_html, os.path.join(salida, "index.html"))
shutil.copy(os.path.join(AQUI, "web", "escena.js"), salida)
shutil.copy(os.path.join(AQUI, "base.css"), salida)
dst = os.path.join(salida, "fuentes")
os.makedirs(dst, exist_ok=True)
for f in os.listdir(os.path.join(AQUI, "fuentes")):
    shutil.copy(os.path.join(AQUI, "fuentes", f), dst)

dur = max(f["fin"] for f in timing["frases"]) + 0.9
datos = {
    "W": 1080, "H": 1920, "fps": 30, "duracion": round(dur, 2),
    "frases": [{"inicio": f["inicio"], "fin": f["fin"],
                "palabras": [{"t": w["t"], "texto": w["texto"], "clave": bool(w["clave"])}
                             for w in f["palabras"]]} for f in timing["frases"]],
    "subtitulos": {"mostrar": True, "y": a.sub_y, "tamano": a.tamano,
                   "color_clave": a.clave, "borde": a.borde, "color_base": a.base},
}
json.dump(datos, open(os.path.join(salida, "datos.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"{len(datos['frases'])} frases · {dur:.1f} s  →  {salida}")
