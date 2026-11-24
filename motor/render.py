"""
Motor de video de partículas.

Uso:
  python motor/render.py CARPETA                 → CARPETA/video.mp4
  python motor/render.py CARPETA --muestras 1.5,4,9.8   → CARPETA/muestras.png (para revisar antes)

CARPETA debe contener:
  voz_final.wav   (de voz.py)
  timing.json     (de voz.py)
  escenas.json    (el diseño)
"""
import sys, os, json, math, re, subprocess, unicodedata, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formas as FM
from formas import W, H, CX, CY, N, REGISTRO, color, transformar

FPS = 30
FONT_DIR = FM.FUENTES


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ#]", "", w)


# ------------------------------------------------------------- valores animables
def valor(v, lt):
    """número | texto | {"de","a","dur","espera"} | {"base","osc","vel"}"""
    if isinstance(v, dict) and "de" in v:
        k = (lt - v.get("espera", 0)) / max(1e-3, v.get("dur", 0.5))
        k = ease(k) if v.get("curva", "suave") == "suave" else min(1, max(0, k))
        return v["de"] + (v["a"] - v["de"]) * k
    if isinstance(v, dict) and "osc" in v:
        return v.get("base", 0) + v["osc"] * math.sin(lt * v.get("vel", 2.0) * 2 * math.pi)
    return v


def resolver_params(esc, lt):
    return {k: (valor(v, lt) if k != "partes" else v) for k, v in esc.items()}


def construir(esc, t, lt, n=N):
    P = resolver_params(esc, lt)
    f = REGISTRO[P["forma"]]
    if P["forma"] == "grupo":
        sh = f(t, lt, P, n, resolver=lambda q, tt, ll, k: construir(q, tt, ll, k))
    else:
        sh = f(t, lt, P, n)
    if "color" in P and P["forma"] in ("globo",):
        pass
    return transformar(sh, P)


# ------------------------------------------------------------- anclas
class Anclas:
    def __init__(self, timing):
        self.fr = timing["frases"]
        self.words = [(i, w) for i, f in enumerate(self.fr) for w in f["palabras"]]
        self.cursor = 0
        self.fin = self.fr[-1]["fin"]

    def tiempo(self, en):
        m = re.match(r"^(.*?)([+-][0-9.]+)?$", en.strip())
        base, off = m.group(1).strip(), float(m.group(2) or 0)
        if base == "inicio": return 0.0 + off
        if base == "fin": return self.fin + off
        if base.startswith("t:"): return float(base[2:]) + off
        if base.startswith("frase:"):
            rest = base[6:]
            if "/" in rest:
                k, w = rest.split("/", 1); k = int(k) - 1
                for j, (fi, ww) in enumerate(self.words):
                    if fi == k and norm(ww["texto"]) == norm(w):
                        self.cursor = j + 1; return ww["t"] + off
                raise ValueError(f"No encuentro '{w}' en la frase {k + 1}")
            k = int(rest) - 1
            j = next(j for j, (fi, _) in enumerate(self.words) if fi == k)
            self.cursor = j; return self.fr[k]["inicio"] + off
        # palabra: siguiente aparición desde el cursor
        target = norm(base)
        for rango in (range(self.cursor, len(self.words)), range(0, len(self.words))):
            for j in rango:
                if norm(self.words[j][1]["texto"]) == target:
                    self.cursor = j + 1; return self.words[j][1]["t"] + off
        raise ValueError(f"La palabra '{base}' no está en el guion")


# ------------------------------------------------------------- nube con física
class Nube:
    def __init__(self):
        r = np.random.default_rng(1)
        self.P = r.uniform(0, 1, (N, 2)) * [W, H]; self.V = np.zeros((N, 2))
        self.C = np.tile(color("cian"), (N, 1)); self.A = np.zeros(N)
        self.k = r.uniform(0.10, 0.20, N)[:, None]; self.sg = r.choice([-1, 1], N)[:, None]

    def paso(self, T, Ct, At, rig=1.0):
        d = T - self.P
        perp = np.c_[-d[:, 1], d[:, 0]]
        k = np.clip(self.k * rig, 0.01, 0.35)
        self.V = self.V * 0.70 + d * k + perp * 0.18 * self.sg * k
        self.P = self.P + self.V
        self.C += (Ct - self.C) * 0.18; self.A += (At - self.A) * 0.18


# ------------------------------------------------------------- dibujo
yy, xx = np.mgrid[0:H, 0:W]
R = np.sqrt(((xx - CX) / 700.) ** 2 + ((yy - CY) / 900.) ** 2)
VIGN = np.clip(1.15 - R * 0.75, 0.25, 1)[..., None].astype(np.float32)
GLOWMAP = np.exp(-R ** 2 * 2.5)[..., None].astype(np.float32)
BG = (np.array([4, 6, 14]) + np.zeros((H, W, 3))).astype(np.float32)
KER = [(0, 0, 1.0), (1, 0, .45), (-1, 0, .45), (0, 1, .45), (0, -1, .45), (1, 1, .2), (-1, 1, .2), (1, -1, .2), (-1, -1, .2)]


PREV = {"can": None}
_tw = np.random.default_rng(3)
TW_W, TW_P = _tw.uniform(1.5, 4.5, N), _tw.uniform(0, 6.3, N)


def dibujar_nube(nb, s, amb, centro=(CX, CY), t=0.0, estela=0.6):
    P = (nb.P - centro) * s + centro
    tw = (0.72 + 0.28 * np.sin(t * TW_W + TW_P))[:, None]
    w = (nb.C * nb.A[:, None] * 0.95 * tw).astype(np.float32)
    xi = np.round(P[:, 0]).astype(int); yi = np.round(P[:, 1]).astype(int)
    ok = (xi > 4) & (xi < W - 5) & (yi > 4) & (yi < H - 5)
    xi, yi, w = xi[ok], yi[ok], w[ok]
    can = np.zeros((H, W, 3), np.float32)
    big = min(3, max(1, int(s)))
    for dx, dy, kv in KER:
        np.add.at(can, (yi + dy * big, xi + dx * big), w * kv)
    if estela and PREV["can"] is not None:  # estelas de luz: lo que se mueve deja rastro
        can = can * (1 - estela) + PREV["can"] * estela
        can = np.maximum(can, 0)
    PREV["can"] = can
    small = can.reshape(H // 4, 4, W // 4, 4, 3).mean((1, 3))
    g1 = gaussian_filter(small, (2, 2, 0)); g2 = gaussian_filter(small, (7, 7, 0))
    glow = np.asarray(Image.fromarray(np.clip(g1 * 4 + g2 * 5, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
    img = BG + GLOWMAP * amb * 0.22 + can * 1.5 + glow
    img = 255 * (1 - np.exp(-img * VIGN / 200))
    return np.clip(img, 0, 255).astype(np.uint8)


class Subtitulos:
    def __init__(self, timing, cfg):
        self.fr = timing["frases"]; self.y = cfg.get("y", 1430); self.on = cfg.get("mostrar", True)
        self.fn = ImageFont.truetype(os.path.join(FONT_DIR, "montserrat-latin-600-normal.woff"), cfg.get("tamano", 60))
        self.fk = ImageFont.truetype(os.path.join(FONT_DIR, "playfair-display-latin-700-italic.woff"), int(cfg.get("tamano", 60) * 1.3))
        self.col_k = tuple(int(x) for x in color(cfg.get("color_clave", "dorado")))

    def dibujar(self, img, t, dur):
        if not self.on: return img
        for i, f in enumerate(self.fr):
            a, b = f["inicio"], f["fin"]
            nxt = self.fr[i + 1]["inicio"] if i + 1 < len(self.fr) else dur
            end = min(b + 0.55, nxt - 0.32)
            if not (a - 0.05 <= t < end + 0.25): continue
            fo = 1 - ease((t - end) / 0.25)
            items = []
            for w in f["palabras"]:
                fnt = self.fk if w["clave"] else self.fn
                items.append((w["texto"], w["clave"], w["t"], fnt, fnt.getlength(w["texto"]), fnt.getlength(" ")))
            lines, cur, cw = [], [], 0
            for it in items:
                if cur and cw + it[5] + it[4] > 900: lines.append(cur); cur, cw = [], 0
                cw += (it[5] if cur else 0) + it[4]; cur.append(it)
            lines.append(cur)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
            y0 = self.y - (len(lines) - 1) * 48
            for li, ln in enumerate(lines):
                lw = sum(x[4] for x in ln) + sum(x[5] for x in ln[1:])
                x = (W - lw) / 2; y = y0 + li * 96
                for k, (w, hl, tw, fnt, wl, sp) in enumerate(ln):
                    if k: x += sp
                    p = ease((t - tw + 0.04) / 0.18)
                    if p > 0:
                        al = int(255 * p * fo); col = self.col_k if hl else (240, 244, 250); dy = (1 - p) * 14
                        ds.text((x, y + dy), w, font=fnt, fill=(0, 0, 0, al), anchor="ls", stroke_width=8, stroke_fill=(0, 0, 0, al))
                        d.text((x, y + dy), w, font=fnt, fill=col + (al,), anchor="ls")
                    x += wl
            sh = sh.filter(ImageFilter.GaussianBlur(12))
            img.alpha_composite(sh); img.alpha_composite(lay)
        return img


F_ROT = ImageFont.truetype(os.path.join(FONT_DIR, "montserrat-latin-600-normal.woff"), 34)


def rotulo(img, txt, lt, total):
    """Texto pequeño arriba (fuente de un estudio, un dato)."""
    a = ease(lt / 0.35) * (1 - ease((lt - (total - 0.3)) / 0.3))
    if a <= 0: return img
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((W / 2, 330), txt, font=F_ROT, fill=(200, 210, 225, int(200 * a)), anchor="mm")
    img.alpha_composite(lay); return img


def glitch(arr, lt, dur, frame):
    k = 1 - min(1.0, lt / dur)
    if k <= 0: return arr
    r = np.random.default_rng(frame)
    o = int(28 * k) + 2
    out = arr.copy()
    out[..., 0] = np.roll(arr[..., 0], o, axis=1); out[..., 2] = np.roll(arr[..., 2], -o, axis=1)
    for _ in range(int(3 + 7 * k)):
        y0 = r.integers(200, 1300); hgt = r.integers(10, 70)
        out[y0:y0 + hgt] = np.roll(out[y0:y0 + hgt], int(r.integers(-90, 90) * k), axis=1)
    return out


# ------------------------------------------------------------- principal
def cargar(carpeta):
    timing = json.load(open(os.path.join(carpeta, "timing.json"), encoding="utf-8"))
    dis = json.load(open(os.path.join(carpeta, "escenas.json"), encoding="utf-8"))
    an = Anclas(timing)
    keys = []
    for e in dis["escenas"]:
        t0 = an.tiempo(e["en"]) + e.get("desplazar", -0.1 if e["en"] not in ("inicio",) else 0)
        e2 = {k: v for k, v in e.items() if k not in ("en", "desplazar", "nota")}
        if isinstance(e2.get("partes"), list):
            pass
        keys.append((max(0.0, t0), e2))
    keys.sort(key=lambda k: k[0])
    voz, sr = sf.read(os.path.join(carpeta, "voz_final.wav"))
    dur = len(voz) / sr
    claves = [w["t"] for f in timing["frases"] for w in f["palabras"] if w["clave"]]
    fin_cfg = dis.get("final", {"tipo": "fundido"})
    t_final = an.tiempo(fin_cfg.get("desde", "fin+0.9")) if fin_cfg.get("tipo") == "zoom" else None
    return timing, dis, keys, dur, claves, fin_cfg, t_final


def render(carpeta, muestras=None, salida=None):
    timing, dis, keys, dur, claves, fin_cfg, t_final = cargar(carpeta)
    subs = Subtitulos(timing, dis.get("subtitulos", {}))
    impulso = dis.get("impulso_palabras_clave", 0.03)
    nb = Nube(); amb = np.zeros(3)
    if dis.get("inicio_formado", True):  # gancho: el primer fotograma ya muestra la forma armándose
        T0, C0, A0 = construir(keys[0][1], 0.0, 0.0)
        rr = np.random.default_rng(7)
        nb.P = T0 + rr.normal(0, 1, (N, 2)) * dis.get("inicio_dispersion", 70)
        nb.C = C0.copy(); nb.A = A0 * 0.7
    nf = int(dur * FPS)
    want = {int(round(x * FPS)): x for x in (muestras or [])}; ims = []
    if not muestras:
        tmp = os.path.join(carpeta, "_tmp_video.mp4")
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    ki = 0
    for i in range(nf):
        t = i / FPS
        while ki + 1 < len(keys) and keys[ki + 1][0] <= t: ki += 1
        t0, esc = keys[ki]
        T, Ct, At = construir(esc, t, t - t0)
        nb.paso(T, Ct, At, esc.get("rigidez", 1.0))
        amb += ((nb.C * nb.A[:, None]).mean(0) - amb) * 0.1
        if muestras and i not in want: continue
        s = 1 + 0.018 * math.sin(t * 0.6)
        for tw in claves:
            if 0 <= t - tw < 1.2: s += impulso * math.exp(-(t - tw) / 0.2)
        if t_final is not None and t > t_final: s *= math.exp((t - t_final) * fin_cfg.get("velocidad", 1.35))
        arr = dibujar_nube(nb, s, amb, t=t, estela=0 if muestras else dis.get("estela", 0.6))
        t_next = keys[ki + 1][0] if ki + 1 < len(keys) else dur
        if esc.get("efecto") == "glitch": arr = glitch(arr, t - t0, esc.get("dur_efecto", 0.7), i)
        img = Image.fromarray(arr).convert("RGBA")
        if esc.get("rotulo"): img = rotulo(img, esc["rotulo"], t - t0, t_next - t0)
        img = subs.dibujar(img, t, dur).convert("RGB")
        fade = (0.55 + 0.45 * ease(t / 0.15)) * (1 - ease((t - (dur - 0.65)) / 0.6))
        if fade < 1: img = Image.eval(img, lambda v: int(v * fade))
        if muestras:
            ims.append(img.resize((360, 640)))
            if len(ims) == len(want): break
        else:
            pr.stdin.write(img.tobytes())
            if i % 150 == 0: print(f"  {i}/{nf}", flush=True)
    if muestras:
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims): sheet.paste(im, (360 * k, 0))
        out = os.path.join(carpeta, "muestras.png"); sheet.save(out); print(out); return out
    pr.stdin.close()
    if pr.wait() != 0: raise SystemExit("ffmpeg falló")
    salida = salida or os.path.join(carpeta, "video.mp4")
    audio = os.path.join(carpeta, "voz_final.wav")
    mus = dis.get("musica")
    if mus:
        fc = (f"[1:a]volume={mus.get('volumen_db', -12)}dB[m];[0:a]asplit=2[v][sc];"
              "[m][sc]sidechaincompress=threshold=0.02:ratio=6:attack=12:release=350[md];"
              "[v][md]amix=inputs=2:normalize=0,alimiter=limit=0.84:attack=1:level=false[a]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-i", mus["archivo"], "-filter_complex", fc,
                        "-map", "[a]", "-t", str(dur), os.path.join(carpeta, "_mezcla.wav")], check=True)
        audio = os.path.join(carpeta, "_mezcla.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", salida], check=True)
    os.remove(tmp); print(salida); return salida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta"); ap.add_argument("--muestras", default=None); ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    render(a.carpeta, [float(x) for x in a.muestras.split(",")] if a.muestras else None, a.salida)
