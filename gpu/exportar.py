"""
Exporta un proyecto del kit (voz_final.wav + timing.json + escenas.json)
a los datos que consume el motor WebGL: una nube de puntos por escena.

Uso:  python exportar.py CARPETA [--particulas 36000] [--salida CARPETA/gpu]
"""
import os, sys, json, argparse, shutil

ap = argparse.ArgumentParser()
ap.add_argument("carpeta")
ap.add_argument("--particulas", type=int, default=36000)
ap.add_argument("--salida", default=None)
ap.add_argument("--desde", type=float, default=0.0)
ap.add_argument("--hasta", type=float, default=None)
a = ap.parse_args()

os.environ["PARTICULAS"] = str(a.particulas)
MOTOR = "/home/claude/kit/motor"
sys.path.insert(0, MOTOR)

import numpy as np
import render as R          # reutiliza anclas, resolución de parámetros y formas
from formas import N, W, H

carpeta = os.path.abspath(a.carpeta)
salida = os.path.abspath(a.salida or os.path.join(carpeta, "gpu"))
os.makedirs(salida, exist_ok=True)

timing, dis, keys, dur, claves, fin_cfg, t_final = R.cargar(carpeta)
t0_corte = a.desde
t1_corte = a.hasta if a.hasta is not None else dur

# ---------------------------------------------------------------- oscilaciones
# Un parámetro como {"base":0,"osc":95,"vel":0.5} ya no se puede congelar: se
# exporta su amplitud para que el movimiento lo haga la GPU (así el iris de un
# ojo se mueve de lado a lado mientras la escena está en pantalla).
ANIM = ("dx", "dy", "x", "y")


def _despejar(d):
    """Devuelve (dict sin oscilaciones, ampX, ampY, vel)."""
    limpio, ax, ay, vel = dict(d), 0.0, 0.0, 0.0
    for k in ANIM:
        v = d.get(k)
        if isinstance(v, dict) and "osc" in v:
            limpio[k] = v.get("base", 0)
            amp = float(v["osc"]); vel = float(v.get("vel", 2.0))
            if k in ("dx", "x"): ax += amp
            else: ay += amp
    return limpio, ax, ay, vel


def osc_de_escena(esc, n):
    """(n,4) con [ampX, ampY, vel, fase] por partícula, y la escena ya sin osc."""
    out = np.zeros((n, 4), np.float32)
    esc, ax, ay, vel = _despejar(esc)
    if vel: out[:, 0], out[:, 1], out[:, 2] = ax, ay, vel
    if esc.get("forma") == "grupo":
        partes = esc["partes"]
        pesos = np.array([q.get("peso", 1.0) for q in partes], float); pesos /= pesos.sum()
        cuentas = np.floor(pesos * n).astype(int); cuentas[-1] = n - cuentas[:-1].sum()
        nuevas, i0 = [], 0
        for q, k in zip(partes, cuentas):
            q2, ax, ay, vel = _despejar(q)
            if vel:
                out[i0:i0 + k, 0], out[i0:i0 + k, 1], out[i0:i0 + k, 2] = ax, ay, vel
            nuevas.append(q2); i0 += k
        esc = dict(esc, partes=nuevas)
    return esc, out


# ---------------------------------------------------------------- escenas
# Cada escena se congela en el instante en que ya está formada; el movimiento
# (viaje, respiración, onda, latido, oscilaciones) lo pone la GPU.
escenas, POS, COL, ALF, NRM, OSC = [], [], [], [], [], []
for i, (t, esc) in enumerate(keys):
    t_next = keys[i + 1][0] if i + 1 < len(keys) else dur
    lt = min(0.45, max(0.0, (t_next - t) * 0.4))
    esc_q, osc = osc_de_escena(esc, N)
    T, C, A = R.construir(esc_q, t + lt, lt)
    T = np.asarray(T, np.float32)
    # normal de cada partícula, para la onda que recorre el contorno
    d = np.roll(T, -1, 0) - np.roll(T, 1, 0)
    nrm = np.c_[-d[:, 1], d[:, 0]]
    nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-6)[:, None]
    POS.append(T)
    NRM.append(nrm.astype(np.float32))
    OSC.append(osc)
    COL.append(np.clip(np.asarray(C), 0, 255).astype(np.uint8))
    ALF.append(np.clip(np.asarray(A) * 255, 0, 255).astype(np.uint8))
    lat = esc.get("latido")
    escenas.append({
        "t": round(t, 3),
        "rotulo": esc.get("rotulo"),
        "efecto": esc.get("efecto"),
        "rigidez": esc.get("rigidez", 1.0),
        "vida": esc.get("vida", 1.0),
        "latido": [lat.get("amp", 0.03), lat.get("vel", 1.1)] if lat else [0, 0],
    })

np.concatenate(POS).tofile(os.path.join(salida, "pos.bin"))
np.concatenate(COL).tofile(os.path.join(salida, "col.bin"))
np.concatenate(ALF).tofile(os.path.join(salida, "alf.bin"))
np.concatenate(NRM).tofile(os.path.join(salida, "nrm.bin"))
np.concatenate(OSC).tofile(os.path.join(salida, "osc.bin"))

# ---------------------------------------------------------------- metadatos
sub = dis.get("subtitulos", {})
frases = [{
    "inicio": f["inicio"], "fin": f["fin"],
    "palabras": [{"t": w["t"], "texto": w["texto"], "clave": bool(w["clave"])} for w in f["palabras"]],
} for f in timing["frases"]]

meta = {
    "W": W, "H": H, "N": N, "fps": 30,
    "duracion": round(dur, 3),
    "desde": t0_corte, "hasta": round(t1_corte, 3),
    "escenas": escenas,
    "frases": frases,
    "claves": claves,
    "estela": dis.get("estela", 0.62),
    "impulso": dis.get("impulso_palabras_clave", 0.03),
    "inicio_dispersion": dis.get("inicio_dispersion", 70),
    "final": fin_cfg, "t_final": t_final,
    "subtitulos": {
        "mostrar": sub.get("mostrar", True),
        "y": sub.get("y", 1430),
        "tamano": sub.get("tamano", 60),
        "color_clave": list(int(x) for x in R.color(sub.get("color_clave", "dorado"))),
    },
    "fuente_voz": "voz_final.wav",
}
json.dump(meta, open(os.path.join(salida, "datos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# fuentes al lado, para que la página las cargue
dst = os.path.join(salida, "fuentes")
os.makedirs(dst, exist_ok=True)
for f in os.listdir(os.path.join(MOTOR, "..", "fuentes")):
    shutil.copy(os.path.join(MOTOR, "..", "fuentes", f), dst)

print(f"{len(escenas)} escenas · {N} partículas · {dur:.1f} s  →  {salida}")
for e in escenas:
    print(f"  {e['t']:6.2f}")
