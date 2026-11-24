"""
Formas a partir de vectores: miles de iconos SVG y contornos de países.

Las partículas se reparten a lo largo del trazo por longitud de arco, así que
quedan espaciadas de forma pareja y las curvas salen limpias a cualquier tamaño
(a diferencia de una silueta dibujada a mano y rasterizada).

Bibliotecas, instaladas con npm en gpu/:
  lucide-static      ~2.400 iconos   (ISC)
  @tabler/icons      ~6.500 iconos   (MIT)
  world-atlas        contornos de países (dominio público, Natural Earth)
"""
import os, re, json, glob, math
import numpy as np
from svgpathtools import parse_path

AQUI = os.path.dirname(os.path.abspath(__file__))
# dónde buscar node_modules: junto al kit, o en gpu/
RAICES = [os.path.join(AQUI, "..", "gpu", "node_modules"),
          os.path.join(AQUI, "..", "node_modules"),
          os.path.join(AQUI, "..", "..", "gpu", "node_modules")]


def _raiz():
    for r in RAICES:
        if os.path.isdir(r): return os.path.abspath(r)
    raise SystemExit("No encuentro node_modules. Corre:  cd gpu && npm install")


_CACHE_IDX = None


def indice():
    """{nombre: ruta.svg} con todos los iconos disponibles."""
    global _CACHE_IDX
    if _CACHE_IDX is not None: return _CACHE_IDX
    r = _raiz(); idx = {}
    fuentes = [
        (os.path.join(r, "@tabler", "icons", "icons", "outline"), ""),
        (os.path.join(r, "@tabler", "icons", "icons", "filled"), "relleno-"),
        (os.path.join(r, "lucide-static", "icons"), ""),
    ]
    for carpeta, pre in fuentes:
        for f in glob.glob(os.path.join(carpeta, "*.svg")):
            n = pre + os.path.basename(f)[:-4]
            idx.setdefault(n, f)          # el primero gana: tabler outline manda
    _CACHE_IDX = idx
    return idx


def buscar(termino, limite=25):
    t = termino.lower().strip().replace(" ", "-")
    idx = indice()
    exactos = [n for n in idx if n == t]
    empiezan = sorted(n for n in idx if n.startswith(t) and n not in exactos)
    contienen = sorted(n for n in idx if t in n and n not in exactos and n not in empiezan)
    return (exactos + empiezan + contienen)[:limite]


# ------------------------------------------------------------- muestreo de trazos
def _paths_de_svg(ruta):
    s = open(ruta, encoding="utf-8").read()
    ds = re.findall(r'\sd="([^"]+)"', s)
    vb = re.search(r'viewBox="([-\d.\s]+)"', s)
    caja = [float(x) for x in vb.group(1).split()] if vb else [0, 0, 24, 24]
    fuera = []
    for d in ds:
        if re.fullmatch(r"\s*M0\s+0h24v24H0z\s*", d.strip()): continue   # fondo de tabler
        try:
            p = parse_path(d)
            if p.length(error=1e-3) > 0.05: fuera.append(p)
        except Exception:
            pass
    return fuera, caja


def puntos_de_paths(paths, n, muestras=900):
    """Reparte n puntos a lo largo de los trazos, espaciados por longitud de arco.

    Se tabula cada trazo con `muestras` puntos y luego se interpola: invertir la
    longitud punto por punto sería exacto pero tarda minutos con 36.000 partículas.
    """
    tablas, largos = [], []
    for p in paths:
        ts = np.linspace(0, 1, muestras)
        z = np.array([p.point(t) for t in ts])
        xy = np.c_[z.real, z.imag]
        d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
        if d[-1] <= 1e-9: continue
        tablas.append((xy, d)); largos.append(d[-1])
    if not tablas: return np.zeros((n, 2))
    largos = np.array(largos, float)
    cuota = np.maximum(2, np.floor(n * largos / largos.sum()).astype(int))
    cuota[int(np.argmax(largos))] += n - cuota.sum()        # cuadra el total exacto
    out = []
    for (xy, d), k in zip(tablas, cuota):
        if k <= 0: continue
        s = (np.arange(k) + 0.5) * d[-1] / k
        out.append(np.c_[np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])])
    pts = np.vstack(out)
    return pts[:n] if len(pts) >= n else np.r_[pts, pts[:n - len(pts)]]


def encajar(pts, caja, alto, centro):
    """Escala la nube para que ocupe `alto` píxeles y la centra."""
    mn, mx = pts.min(0), pts.max(0)
    span = max(mx[1] - mn[1], 1e-6), max(mx[0] - mn[0], 1e-6)
    k = alto / span[0]
    if span[1] * k > 980: k = 980 / span[1]          # que no se salga de ancho
    c = (mn + mx) / 2
    return (pts - c) * k + np.array(centro, float)


# ------------------------------------------------------------- mapas
_CACHE_MAPA = {}
ALIAS_PAIS = {
    "españa": "Spain", "espana": "Spain", "méxico": "Mexico", "mexico": "Mexico",
    "colombia": "Colombia", "argentina": "Argentina", "chile": "Chile", "perú": "Peru",
    "peru": "Peru", "estados unidos": "United States of America", "eeuu": "United States of America",
    "japón": "Japan", "japon": "Japan", "francia": "France", "italia": "Italy",
    "alemania": "Germany", "brasil": "Brazil", "reino unido": "United Kingdom",
    "canadá": "Canada", "canada": "Canada", "india": "India", "china": "China",
    "portugal": "Portugal", "ecuador": "Ecuador", "venezuela": "Venezuela",
}


def _topo():
    if "t" not in _CACHE_MAPA:
        r = _raiz()
        _CACHE_MAPA["t"] = json.load(open(os.path.join(r, "world-atlas", "countries-50m.json")))
    return _CACHE_MAPA["t"]


def _arco(topo, i):
    rev = i < 0
    if rev: i = -i - 1
    a = topo["arcs"][i]
    x = y = 0; out = []
    for dx, dy in a:
        x += dx; y += dy; out.append((x, y))
    sc, tr = topo["transform"]["scale"], topo["transform"]["translate"]
    out = [(px * sc[0] + tr[0], py * sc[1] + tr[1]) for px, py in out]
    return out[::-1] if rev else out


def anillos_pais(nombre):
    topo = _topo()
    busca = ALIAS_PAIS.get(nombre.lower().strip(), nombre)
    geos = topo["objects"]["countries"]["geometries"]
    g = next((g for g in geos if g.get("properties", {}).get("name", "").lower() == busca.lower()), None)
    if g is None:
        disp = sorted(x.get("properties", {}).get("name", "") for x in geos)
        raise ValueError(f"No encuentro el país '{nombre}'. Ejemplos: {disp[:8]}…")
    polis = g["arcs"] if g["type"] == "Polygon" else [p for m in g["arcs"] for p in m]
    anillos = []
    for anillo in polis:
        pts = []
        for i in anillo: pts.extend(_arco(topo, i))
        if len(pts) > 8: anillos.append(np.array(pts, float))
    anillos.sort(key=lambda a: -(np.ptp(a[:, 0]) * np.ptp(a[:, 1])))
    return anillos


def puntos_pais(nombre, n, trozos=6, minimo=0.06):
    # se quedan las islas que aportan a la silueta y se descartan las lejanas
    # (si no, las Canarias encogen la península)
    todos = anillos_pais(nombre)
    area = lambda a: np.ptp(a[:, 0]) * np.ptp(a[:, 1])
    mayor = area(todos[0])
    anillos = [a for a in todos[:trozos] if area(a) >= mayor * minimo]
    largos = np.array([len(a) for a in anillos], float)
    cuota = np.maximum(3, np.round(n * largos / largos.sum()).astype(int))
    out = []
    for a, k in zip(anillos, cuota):
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(a, axis=0).T))]
        if d[-1] <= 0: continue
        s = np.linspace(0, d[-1], int(k), endpoint=False)
        out.append(np.c_[np.interp(s, d, a[:, 0]), np.interp(s, d, a[:, 1])])
    pts = np.vstack(out)
    pts[:, 1] *= -1                      # la latitud crece hacia arriba
    pts[:, 0] *= np.cos(np.radians(np.abs(pts[:, 1]).mean()))   # que no se estire
    if len(pts) >= n:
        return pts[np.linspace(0, len(pts) - 1, n).astype(int)]
    ex = np.random.default_rng(8).choice(len(pts), n - len(pts))
    return np.r_[pts, pts[ex]]


# ------------------------------------------------------------- CLI
def _lamina(nombres, salida, n=2200):
    """Hoja de contacto para elegir iconos de un vistazo."""
    from PIL import Image, ImageDraw, ImageFont
    import formas as FM
    cols = min(4, max(1, len(nombres))); filas = math.ceil(len(nombres) / cols)
    c = 420
    im = Image.new("RGB", (cols * c, filas * c), (8, 10, 18)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(AQUI, "..", "fuentes", "montserrat-latin-600-normal.woff"), 20)
    for k, nom in enumerate(nombres):
        cx, cy = (k % cols) * c + c / 2, (k // cols) * c + c / 2
        try:
            if nom.startswith("mapa:"):
                pts = puntos_pais(nom[5:], n); pts = encajar(pts, None, c * 0.60, (cx, cy - 12))
            else:
                paths, caja = _paths_de_svg(indice()[nom])
                pts = encajar(puntos_de_paths(paths, n), caja, c * 0.60, (cx, cy - 12))
        except Exception as e:
            d.text((cx, cy), "?", font=f, fill=(255, 80, 80), anchor="mm"); continue
        for x, y in pts:
            d.point((x, y), fill=(150, 220, 255))
            d.point((x + 1, y), fill=(60, 100, 130))
        d.text((cx, cy + c / 2 - 22), nom, font=f, fill=(190, 200, 215), anchor="mm")
    im.save(salida); print(salida)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "buscar":
        for n in buscar(sys.argv[2], int(sys.argv[4]) if len(sys.argv) > 4 else 30): print(n)
    elif len(sys.argv) > 3 and sys.argv[1] == "ver":
        _lamina(sys.argv[2].split(","), sys.argv[3])
    else:
        print("uso:  python vectores.py buscar FUEGO\n      python vectores.py ver home,flame,mapa:España salida.png")
