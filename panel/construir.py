"""
Prepara una portada 16:9 estilo panel a partir de un guion corto en JSON.

Uso:  python construir.py portada.json CARPETA_SALIDA
"""
import os, sys, json, re, shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
MOTOR = os.path.join(AQUI, "..", "kit", "motor")
sys.path.insert(0, MOTOR)
import vectores as V

spec = json.load(open(sys.argv[1], encoding="utf-8"))
salida = os.path.abspath(sys.argv[2])
os.makedirs(os.path.join(salida, "fuentes"), exist_ok=True)

NODE = V._raiz()
FUENTES = {
    "archivo-900.woff": "@fontsource/archivo/files/archivo-latin-900-normal.woff",
    "archivo-700.woff": "@fontsource/archivo/files/archivo-latin-700-normal.woff",
    "mono-400.woff": "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff",
    "mono-700.woff": "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff",
    "cond-700.woff": "@fontsource/barlow-condensed/files/barlow-condensed-latin-700-normal.woff",
}
for dst, src in FUENTES.items():
    shutil.copy(os.path.join(NODE, src), os.path.join(salida, "fuentes", dst))


def trazos(nombre):
    """Los caminos del icono, para dibujarlo como SVG dentro de la página."""
    idx = V.indice()
    if nombre not in idx:
        raise SystemExit(f"No existe el icono '{nombre}'. ¿Querías {V.buscar(nombre, 6)}?")
    s = open(idx[nombre], encoding="utf-8").read()
    ds = [d for d in re.findall(r'\sd="([^"]+)"', s)
          if not re.fullmatch(r"\s*M0\s+0h24v24H0z\s*", d.strip())]
    vb = re.search(r'viewBox="([-\d.\s]+)"', s)
    return {"trazos": ds, "caja": vb.group(1) if vb else "0 0 24 24"}


PALETA = {"naranja": "#ff9433", "cian": "#4fd3ef", "dorado": "#ffc46b",
          "verde": "#5fe0a8", "violeta": "#b08cff", "rojo": "#ff6b74"}

insignias = []
for i, b in enumerate(spec["insignias"]):
    col = b.get("color") or ("naranja" if i % 2 == 0 else "cian")
    insignias.append({**trazos(b["icono"]), "etiqueta": b["etiqueta"],
                      "color": PALETA.get(col, col)})

datos = {
    "W": spec.get("ancho", 1920), "H": spec.get("alto", 1080), "fps": 30,
    "duracion": spec.get("duracion", 10.0),
    "tipo": spec.get("tipo", "portada"),
    "titulo": spec["titulo"], "pildora": spec.get("pildora", ""),
    "subtitulo": spec.get("subtitulo", ""),
    "titulo_desde": spec.get("titulo_desde", 0.45),
    "insignia_desde": spec.get("insignia_desde", 2.3),
    "insignia_paso": spec.get("insignia_paso", 0.34),
    "insignias": insignias,
    "logo": trazos(spec["logo"]) if spec.get("logo") else None,
}
json.dump(datos, open(os.path.join(salida, "datos.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"{len(insignias)} insignias · {datos['W']}x{datos['H']} · {datos['duracion']} s  →  {salida}")
