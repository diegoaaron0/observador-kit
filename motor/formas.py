"""
Vocabulario de formas para la nube de partículas.

Cada forma es una función  f(t, lt, P) -> (pos[N,2], color[N,3], alfa[N])
  t  = tiempo global del video (s)
  lt = tiempo desde que empezó esta escena (s), para animar parámetros
  P  = parámetros ya resueltos para este instante (números, colores, textos)

Para añadir una forma nueva: o bien se dibuja una máscara PNG (blanco sobre negro, 1080x1920)
y se usa la forma "mascara", o se registra aquí una función nueva con @forma("nombre").
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_erosion, binary_dilation, gaussian_filter

W, H = 1080, 1920
CX, CY = 540, 860
N = int(os.environ.get("PARTICULAS", 2600))   # el motor GPU la sube; por defecto, el de siempre
AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, "..", "fuentes")
F_SANS_BLACK = os.path.join(FUENTES, "montserrat-latin-900-normal.woff")
F_SERIF = os.path.join(FUENTES, "playfair-display-latin-700-italic.woff")

COLORES = {
    "cian": (90, 220, 255), "dorado": (255, 196, 107), "blanco": (235, 245, 255),
    "naranja": (255, 120, 60), "azul": (80, 130, 255), "magenta": (255, 70, 200),
    "rojo": (255, 70, 80), "verde": (90, 240, 160), "violeta": (170, 120, 255), "gris": (120, 130, 150),
}


def color(c):
    if c is None: return None
    if isinstance(c, str):
        if c.startswith("#"): return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)
        return np.array(COLORES[c], float)
    return np.array(c, float)


rng = np.random.default_rng(11)
REGISTRO = {}


def forma(nombre):
    def deco(f):
        REGISTRO[nombre] = f; return f
    return deco


# ---------------------------------------------------------------- utilidades
def orden_angular(p):
    c = p.mean(0)
    return np.argsort(np.arctan2(p[:, 1] - c[1], p[:, 0] - c[0]), kind="stable")


def elegir(arr, n, r=rng):
    idx = r.choice(len(arr), n, replace=len(arr) < n)
    return arr[idx].astype(float) + r.uniform(-0.5, 0.5, (n, 2))


def muestrear_mascara(mask, n=N, borde=0.6, grosor=2, seed=3):
    r = np.random.default_rng(seed)
    er = binary_erosion(mask, iterations=grosor)
    edge = np.argwhere(mask & ~er)[:, ::-1]
    inner = np.argwhere(er)[:, ::-1]
    if len(edge) == 0: edge = np.argwhere(mask)[:, ::-1]
    ne = int(n * borde)
    pe = elegir(edge, ne, r)
    pi = elegir(inner if len(inner) else edge, n - ne, r)
    a = np.r_[np.full(ne, 1.0), np.full(n - ne, 0.16)]
    p = np.r_[pe, pi]
    o = orden_angular(p)
    return p[o], a[o]


def lienzo():
    im = Image.new("L", (W, H), 0); return im, ImageDraw.Draw(im)


CACHE = {}


def cache(key, fn):
    if key not in CACHE: CACHE[key] = fn()
    return CACHE[key]


def solido(n, c): return np.tile(color(c), (n, 1))


# ---------------------------------------------------------------- formas
FIB = {}


def _fib(n):
    if n not in FIB:
        i = np.arange(n) + 0.5
        phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
        v = np.c_[np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)]
        FIB[n] = v[np.argsort(np.arctan2(v[:, 2], v[:, 0]))]
    return FIB[n]


@forma("globo")
def globo(t, lt, P, n=N):
    """Esfera de puntos que gira. P: radio, giro (vel.), color, x, y"""
    v = _fib(n); a = t * P.get("giro", 0.35)
    x = v[:, 0] * np.cos(a) - v[:, 2] * np.sin(a); z = v[:, 0] * np.sin(a) + v[:, 2] * np.cos(a)
    tl = 0.35
    y = v[:, 1] * np.cos(tl) - z * np.sin(tl); z2 = v[:, 1] * np.sin(tl) + z * np.cos(tl)
    R = P.get("radio", 360)
    p = np.c_[P.get("x", CX) + R * x, P.get("y", CY) + R * y]
    al = 0.28 + 0.9 * ((z2 + 1) / 2) ** 1.5
    c = solido(n, P.get("color", "cian")) * (0.75 + 0.25 * ((z2[:, None] + 1) / 2))
    return p, c, al


@forma("dos_globos")
def dos_globos(t, lt, P, n=N):
    """Dos mundos. P: color1, color2, radio"""
    n1 = n // 2; R = P.get("radio", 215)
    p1, c1, a1 = globo(t, lt, {"radio": R, "giro": 0.5, "color": P.get("color1", "naranja"), "x": CX - 255}, n1)
    p2, c2, a2 = globo(-t, lt, {"radio": R, "giro": 0.5, "color": P.get("color2", "azul"), "x": CX + 255}, n - n1)
    return np.r_[p1, p2], np.r_[c1, c2], np.r_[a1, a2]


EYE = {}


@forma("ojo")
def ojo(t, lt, P, n=N):
    """Ojo con iris. P: abrir (0-1), mirar_x, mirar_y (-1..1), pupila (1=normal, >1 dilatada), escala, x, y, color_iris"""
    if n not in EYE:
        r = np.random.default_rng(5)
        nl = int(n * .26); nlow = int(n * .22); ni = n - nl - nlow
        EYE[n] = (r.uniform(-1, 1, nl), r.uniform(-1, 1, nlow), r.uniform(0, 2 * np.pi, ni), r.uniform(0, 1, ni) ** 0.7)
    xu, xl, ang, rr = EYE[n]
    sc = P.get("escala", 1.0); cx, cy = P.get("x", CX), P.get("y", CY)
    w, h = 400 * sc, 210 * sc
    o = max(0.02, P.get("abrir", 1.0))
    up = np.c_[cx + w * xu, cy - h * o * (1 - xu ** 2) * (1 + 0.15 * xu)]
    lo = np.c_[cx + w * xl, cy + h * 0.78 * o * (1 - xl ** 2)]
    r_in, r_out = 62 * P.get("pupila", 1.0) * sc, 140 * sc
    spoke = (np.floor(ang / (2 * np.pi) * 48) / 48) * 2 * np.pi
    a2 = ang * 0.35 + spoke * 0.65
    rad = r_in + (r_out - r_in) * rr
    ix = cx + P.get("mirar_x", 0) * 120 * sc + rad * np.cos(a2); iy = cy + P.get("mirar_y", 0) * 60 * sc + rad * np.sin(a2)
    q = ((ix - cx) / w).clip(-1, 1) ** 2
    top = cy - h * o * (1 - q); bot = cy + h * 0.78 * o * (1 - q)
    iy = np.clip(iy, top + 3, bot - 3)
    p = np.r_[up, lo, np.c_[ix, iy]]
    gi = color(P.get("color_iris", "dorado")); go = color("cian")
    col = np.r_[solido(len(up) + len(lo), "blanco"), gi * (1 - rr[:, None]) + go * rr[:, None]]
    al = np.r_[np.ones(len(up) + len(lo)), (0.55 + 0.45 * (1 - rr)) * ((bot - top) > 8)]
    return p, col, al


def _mask_persona():
    im, d = lienzo()
    d.ellipse([540 - 132, 700 - 165, 540 + 132, 700 + 165], fill=255)
    d.rectangle([488, 820, 592, 960], fill=255)
    d.polygon([(488, 925), (592, 925), (700, 1045), (380, 1045)], fill=255)
    d.ellipse([540 - 330, 1000, 540 + 330, 1420], fill=255)
    d.rectangle([0, 1170, W, H], fill=0)
    return np.asarray(im) > 0


NOISE = rng.normal(0, 1, (N, 2))


@forma("persona")
def persona(t, lt, P, n=N):
    """Silueta de busto. P: color, deshacer (0-1: se desintegra)"""
    p, a = cache(("persona", n), lambda: muestrear_mascara(_mask_persona(), n, 0.62))
    p = p.copy()
    k = P.get("deshacer", 0)
    if k: p = p + NOISE[:n] * 95 * k; a = a * (1 - 0.2 * k)
    return p, solido(n, P.get("color", "blanco")), a


def _mask_perfil():
    im, d = lienzo()
    d.ellipse([290, 560, 720, 1030], fill=255)
    d.polygon([(600, 590), (690, 650), (725, 740), (728, 805), (775, 880), (735, 900), (742, 945), (728, 968),
               (735, 1000), (705, 1045), (650, 1060), (618, 1110), (612, 1200), (420, 1200), (425, 1040), (330, 960)], fill=255)
    return np.asarray(im) > 0


PERM = rng.permutation(N)


@forma("cabeza")
def cabeza(t, lt, P, n=N):
    """Cabeza de perfil. P: contenido ('globo' | 'nucleo' | 'nada'), color, color_contenido"""
    p, a = cache(("perfil", n), lambda: muestrear_mascara(_mask_perfil(), n, 0.6))
    p, a = p.copy(), a.copy(); c = solido(n, P.get("color", "cian"))
    cont = P.get("contenido", "nada")
    if cont != "nada":
        k = int(n * 0.38); idx = PERM[PERM < n][:k]
        if cont == "globo":
            gp, gc, ga = globo(t, lt, {"radio": 130, "giro": 0.6, "color": P.get("color_contenido", "dorado"), "x": 505, "y": 790}, k)
        else:
            r = np.random.default_rng(2)
            rr = np.abs(r.normal(0, 1, k)); th = r.uniform(0, 2 * np.pi, k)
            gp = np.c_[505 + 55 * rr * np.cos(th), 790 + 55 * rr * np.sin(th)]
            gc = solido(k, P.get("color_contenido", "dorado")); ga = np.ones(k)
        p[idx], c[idx], a[idx] = gp, gc, ga
    return p, c, a


@forma("marco")
def marco(t, lt, P, n=N):
    """Una persona dentro de un marco de foto ('imagen'). P: color, color_marco"""
    def build():
        r = np.random.default_rng(4); n1 = int(n * 0.32)
        u = r.uniform(0, 4, n1); w2, h2 = 300, 380
        x = np.where(u < 1, -w2 + 2 * w2 * u, np.where(u < 2, w2, np.where(u < 3, w2 - 2 * w2 * (u - 2), -w2)))
        y = np.where(u < 1, -h2, np.where(u < 2, -h2 + 2 * h2 * (u - 1), np.where(u < 3, h2, h2 - 2 * h2 * (u - 3))))
        bp, ba = muestrear_mascara(_mask_persona(), n - n1, 0.62)
        bp = (bp - [540, 900]) * 0.78 + [CX, CY + 40]
        p = np.r_[np.c_[CX + x, CY + y], bp]; a = np.r_[np.ones(n1), ba]
        o = orden_angular(p); return p[o], a[o], (np.r_[np.ones(n1), np.zeros(n - n1)] > 0)[o]
    p, a, es_marco = cache(("marco", n), build)
    c = np.where(es_marco[:, None], color(P.get("color_marco", "dorado")), color(P.get("color", "blanco")))
    return p, c, a


def _brain_pts():
    Wb, Hb = 900, 760
    m = Image.new("L", (Wb, Hb), 0); d = ImageDraw.Draw(m)
    d.ellipse([60, 70, 860, 560], fill=255); d.ellipse([170, 40, 820, 520], fill=255); d.ellipse([140, 330, 640, 600], fill=255)
    ce = Image.new("L", (Wb, Hb), 0); ImageDraw.Draw(ce).ellipse([540, 470, 830, 660], fill=255)
    st = Image.new("L", (Wb, Hb), 0); ImageDraw.Draw(st).polygon([(520, 540), (585, 540), (600, 755), (555, 755)], fill=255)
    M = np.asarray(m) > 0; C = (np.asarray(ce) > 0) & ~M; S = (np.asarray(st) > 0) & ~M & ~C
    r = np.random.default_rng(4)
    f = sum(gaussian_filter(r.standard_normal((Hb, Wb)), s) * s for s in (18, 30, 50)); f = (f - f.mean()) / f.std()
    yy, xx = np.mgrid[0:Hb, 0:Wb]
    gyri = np.abs(np.sin(f * 4.2)) < 0.2
    stripes = np.abs(np.sin(yy * 0.22 + f * 1.5)) < 0.22
    fy = 300 + (xx - 230) * 0.32 + 18 * np.sin((xx - 230) / 60)
    fis = (np.abs(yy - fy) < 9) & (xx > 230) & (xx < 640)
    lines = (gyri & M & ~fis) | (stripes & C)
    edge = np.zeros_like(M)
    for part in (M, C, S): edge |= binary_dilation(part, iterations=4) & ~part & ~(M if part is not M else np.zeros_like(M))
    pts = np.argwhere(lines | edge)[:, ::-1].astype(float)
    return (pts - np.array([450, 400])) + np.array([CX, CY])


@forma("cerebro")
def cerebro(t, lt, P, n=N):
    """Cerebro de perfil, degradado magenta→cian. P: color1, color2"""
    p = cache(("cerebro", n), lambda: (lambda q: q[orden_angular(q)])(elegir(_brain_pts(), n, np.random.default_rng(6))))
    gx = ((p[:, 0] - (CX - 450)) / 900).clip(0, 1)[:, None]
    c = color(P.get("color1", "magenta")) * (1 - gx) + color(P.get("color2", "cian")) * gx
    return p, c, np.full(n, 0.9)


@forma("cara")
def cara(t, lt, P, n=N):
    """Rostro de frente en línea. P: color"""
    def build():
        r = np.random.default_rng(8); parts = []
        def curve(fx, fy, k, t0=0, t1=2 * np.pi):
            u = r.uniform(t0, t1, k); return np.c_[fx(u), fy(u)]
        parts.append(curve(lambda u: CX + 215 * np.cos(u), lambda u: CY + 285 * np.sin(u), int(n * .38)))
        for sx in (-1, 1):
            ex, ey = CX + sx * 92, CY - 40
            parts.append(curve(lambda u: ex + 62 * np.cos(u), lambda u: ey - 24 * np.sin(u) * np.where(np.sin(u) > 0, 1, 0.8), int(n * .07)))
            parts.append(curve(lambda u: ex + 18 * np.cos(u), lambda u: ey + 18 * np.sin(u), int(n * .04)))
            parts.append(curve(lambda u: ex + 70 * np.cos(u), lambda u: ey - 60 - 22 * np.sin(u), int(n * .05), 0.2, np.pi - 0.2))
        parts.append(curve(lambda u: CX - 8 + 14 * u / np.pi, lambda u: CY - 20 + 95 * u / np.pi, int(n * .05), 0, np.pi))
        parts.append(curve(lambda u: CX + 75 * np.cos(u), lambda u: CY + 150 + 28 * np.sin(u), int(n * .07), 0.15, np.pi - 0.15))
        p = np.concatenate(parts); p = elegir(p, n, r)
        return p[orden_angular(p)]
    p = cache(("cara", n), build)
    return p, solido(n, P.get("color", "blanco")), np.full(n, 0.95)


WAVE = {}


@forma("onda")
def onda(t, lt, P, n=N):
    """Onda de voz animada (barras). P: color1, color2, energia (0-2)"""
    if n not in WAVE:
        r = np.random.default_rng(9); WAVE[n] = (r.integers(0, 46, n), r.uniform(-1, 1, n))
    bi, u = WAVE[n]
    x = 150 + bi * (780 / 45); env = np.exp(-((bi - 22.5) / 14) ** 2)
    e = P.get("energia", 1.0)
    hgt = 40 + 330 * e * env * (0.55 + 0.45 * np.sin(t * 9 + bi * 0.55)) * (0.7 + 0.3 * np.sin(t * 5.3 + bi * 1.3))
    gx = (bi / 45)[:, None]
    c = color(P.get("color1", "cian")) * (1 - gx) + color(P.get("color2", "dorado")) * gx
    return np.c_[x, CY + u * hgt], c, np.full(n, 0.9)


def _mask_texto(txt, fuente, tam, x=CX, y=CY):
    im, d = lienzo()
    f = ImageFont.truetype(fuente, int(tam))
    d.multiline_text((x, y), txt, font=f, fill=255, anchor="mm", align="center", spacing=int(tam * 0.1))
    return np.asarray(im) > 0


@forma("pensamiento")
def pensamiento(t, lt, P, n=N):
    """Nube de pensamiento con un símbolo dentro. P: simbolo ('?'), color, color_simbolo"""
    sim = P.get("simbolo", "?")
    def build():
        im, d = lienzo()
        for x, y, r in [(-150, 0, 120), (0, -85, 150), (150, -10, 125), (60, 95, 120), (-90, 95, 110)]:
            d.ellipse([CX + x - r, CY + y - r, CX + x + r, CY + y + r], fill=255)
        im2, d2 = lienzo()
        for x, y, r in [(-250, 240, 42), (-325, 315, 24)]:
            d2.ellipse([CX + x - r, CY + y - r, CX + x + r, CY + y + r], fill=255)
        n1 = int(n * .5); n2 = int(n * .12); n3 = n - n1 - n2
        p1, _ = muestrear_mascara(np.asarray(im) > 0, n1, 1.0); p2, _ = muestrear_mascara(np.asarray(im2) > 0, n2, 1.0)
        p3, a3 = muestrear_mascara(_mask_texto(sim, F_SERIF, 300, CX, CY + 5), n3, 0.5, 3)
        return np.r_[p1, p2, p3], np.r_[np.ones(n1 + n2), np.maximum(a3, 0.6)], n1 + n2
    p, a, k = cache(("pens", sim, n), build)
    c = np.r_[solido(k, P.get("color", "blanco")), solido(n - k, P.get("color_simbolo", "dorado"))]
    return p, c, a


@forma("texto")
def texto(t, lt, P, n=N):
    """Una palabra o símbolo hecho de partículas. P: texto, tamano, fuente ('sans'|'serif'), color, x, y"""
    txt = P.get("texto", "TÚ"); tam = P.get("tamano", 520)
    fnt = F_SERIF if P.get("fuente", "sans") == "serif" else F_SANS_BLACK
    x, y = P.get("x", CX), P.get("y", CY)
    p, a = cache(("txt", txt, tam, fnt, x, y, n), lambda: muestrear_mascara(_mask_texto(txt, fnt, tam, x, y), n, 0.45, 3))
    return p, solido(n, P.get("color", "dorado")), np.maximum(a, 0.55)


@forma("mascara")
def mascara(t, lt, P, n=N):
    """Cualquier silueta: PNG blanco sobre negro de 1080x1920 (o se centra si es más pequeño).
    P: archivo, color, borde (0-1, proporción de partículas en el contorno)"""
    f = P["archivo"]
    def build():
        im = Image.open(f).convert("L")
        if im.size != (W, H):
            base = Image.new("L", (W, H), 0)
            base.paste(im, ((W - im.width) // 2, CY - im.height // 2)); im = base
        return muestrear_mascara(np.asarray(im) > 127, n, P.get("borde", 0.6))
    p, a = cache(("mask", f, n), build)
    return p, solido(n, P.get("color", "blanco")), a


SC = rng.uniform(0, 1, (N, 2))


@forma("dispersion")
def dispersion(t, lt, P, n=N):
    """Partículas flotando por toda la pantalla ('el mundo de afuera'). P: amplitud (1 = pantalla), color1, color2"""
    s = SC[:n]; c0 = np.array([CX, CY])
    p = c0 + (s * [W, H * 0.8] + [0, H * 0.04] - c0) * P.get("amplitud", 1.0)
    p = p + np.c_[np.sin(t * 0.5 + s[:, 1] * 9), np.cos(t * 0.4 + s[:, 0] * 9)] * 18
    gx = s[:, :1]
    return p, color(P.get("color1", "cian")) * (1 - gx) + color(P.get("color2", "blanco")) * gx, np.full(n, 0.75)


SPI = {}


@forma("espiral")
def espiral(t, lt, P, n=N):
    """Galaxia de 3 brazos girando ('te explico', un torbellino de ideas). P: radio, giro, color1, color2"""
    if n not in SPI:
        r = np.random.default_rng(12)
        SPI[n] = (r.integers(0, 3, n), r.uniform(0, 1, n) ** 0.6, r.normal(0, 1, (n, 2)))
    arm, rr, jit = SPI[n]
    R = P.get("radio", 400) * rr
    th = arm * 2 * np.pi / 3 + rr * 4.2 + t * P.get("giro", 0.9)
    p = np.c_[CX + R * np.cos(th), CY + R * np.sin(th) * 0.9] + jit * (8 + 22 * rr[:, None])
    c = color(P.get("color1", "dorado")) * (1 - rr[:, None]) + color(P.get("color2", "cian")) * rr[:, None]
    return p, c, 0.45 + 0.55 * (1 - rr)


# Formas compuestas: {"forma":"grupo","partes":[{"forma":..., "peso":0.6, ...}, ...]}
@forma("grupo")
def grupo(t, lt, P, n=N, resolver=None):
    partes = P["partes"]; pesos = np.array([q.get("peso", 1.0) for q in partes], float); pesos /= pesos.sum()
    cuentas = np.floor(pesos * n).astype(int); cuentas[-1] = n - cuentas[:-1].sum()
    ps, cs, as_ = [], [], []
    for q, k in zip(partes, cuentas):
        pp, cc, aa = resolver(q, t, lt, k)
        ps.append(pp); cs.append(cc); as_.append(aa)
    return np.concatenate(ps), np.concatenate(cs), np.concatenate(as_)


def transformar(sh, P):
    """Transformaciones comunes a cualquier forma: dx, dy, escala, rotar (grados), brillo"""
    p, c, a = sh
    esc, gir, dx, dy = P.get("escala", 1.0), P.get("rotar", 0.0), P.get("dx", 0.0), P.get("dy", 0.0)
    if esc != 1.0 or gir:
        piv = p.mean(0); th = np.deg2rad(gir); q = p - piv
        q = np.c_[q[:, 0] * np.cos(th) - q[:, 1] * np.sin(th), q[:, 0] * np.sin(th) + q[:, 1] * np.cos(th)] * esc
        p = q + piv
    if dx or dy: p = p + [dx, dy]
    k = P.get("deshacer", 0)
    if k and P.get("forma") != "persona":  # cualquier forma se desintegra / se rearma
        p = p + NOISE[:len(p)] * 95 * k; a = a * (1 - 0.2 * k)
    if "brillo" in P: a = a * P["brillo"]
    return p, c, a


# ---------------------------------------------------------------- vectores
# Iconos SVG (miles) y contornos de países: curvas limpias y partículas parejas.
@forma("icono")
def icono(t, lt, P, n=N):
    """Un icono de las bibliotecas vectoriales.
    P: nombre ('home', 'flame', 'users'...), alto (px), color, x, y, grosor
    Busca el nombre con:  python motor/vectores.py buscar fuego"""
    import vectores as V
    nom = P["nombre"]; alto = P.get("alto", 620)
    x, y = P.get("x", CX), P.get("y", CY)

    def build():
        idx = V.indice()
        if nom not in idx:
            op = V.buscar(nom, 8)
            raise ValueError(f"No existe el icono '{nom}'." + (f" ¿Querías {op}?" if op else ""))
        paths, caja = V._paths_de_svg(idx[nom])
        if not paths: raise ValueError(f"El icono '{nom}' no tiene trazo utilizable")
        sel = P.get("trazos")           # quedarse con parte del dibujo: [1] = solo el contorno
        if sel is not None: paths = [paths[i] for i in sel]
        pts = V.puntos_de_paths(paths, n)
        return V.encajar(pts, caja, alto, (x, y))

    p = cache(("icono", nom, alto, x, y, n, tuple(P.get("trazos") or ())), build).copy()
    g = P.get("grosor", 1.0)
    if g != 1.0:
        p = p + rng.normal(0, 1.0, (n, 2)) * (g - 1.0) * 6
    a = np.full(n, 1.0)
    return p, solido(n, P.get("color", "blanco")), a


@forma("mapa")
def mapa(t, lt, P, n=N):
    """Contorno de un país. P: pais ('España'), alto (px), color, x, y, trozos"""
    import vectores as V
    pais = P["pais"]; alto = P.get("alto", 620)
    x, y = P.get("x", CX), P.get("y", CY)
    trozos = P.get("trozos", 6)

    def build():
        pts = V.puntos_pais(pais, n, trozos)
        return V.encajar(pts, None, alto, (x, y))

    p = cache(("mapa", pais, alto, x, y, trozos, n), build).copy()
    return p, solido(n, P.get("color", "blanco")), np.full(n, 1.0)
