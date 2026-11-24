"""Mezcla efectos de sonido sobre la voz, cuadrados al fotograma en que ocurre cada cosa.

Cada clip trae su punto de sincronía (`sync.at`): el instante dentro del archivo donde
se oye el golpe. Para que el golpe caiga en el segundo T, el clip arranca en T - sync.at.
Eso lo calcula este script; tú solo dices en qué segundo pasa cada cosa.

uso:
  python sonido.py PROYECTO --plan plan.json  [--salida voz_con_sfx.wav] [--volumen 0.5]
  python sonido.py PROYECTO --auto            # propone un plan desde timing.json

plan.json:  [{"t": 2.05, "clip": "whoosh-slow-soft"}, {"t": 3.9, "clip": "pop-medium-in", "vol": 0.8}]
"""
import os, sys, json, argparse, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
CLIPS = json.load(open(os.path.join(AQUI, "clips.json"), encoding="utf-8"))["clips"]
POR_ID = {c["id"]: c for c in CLIPS}

ap = argparse.ArgumentParser()
ap.add_argument("proyecto")
ap.add_argument("--plan")
ap.add_argument("--auto", action="store_true")
ap.add_argument("--voz", default="voz_final.wav")
ap.add_argument("--salida", default="voz_con_sfx.wav")
ap.add_argument("--volumen", type=float, default=0.5, help="volumen global de los efectos (la voz manda)")
a = ap.parse_args()

proy = os.path.abspath(a.proyecto)
voz = os.path.join(proy, a.voz)
if not os.path.exists(voz):
    sys.exit(f"no encuentro la voz: {voz}")


def plan_automatico():
    """Un punto de partida, no el resultado final: cambio de escena en cada frase
    y un acento en cada palabra clave. Revísalo y quita lo que sobre."""
    t = json.load(open(os.path.join(proy, "timing.json"), encoding="utf-8"))
    frases = t["frases"]
    plan = []
    for i, f in enumerate(frases):
        if i:  # la primera frase no necesita transición
            plan.append({"t": round(f["inicio"] - 0.06, 3), "clip": "whoosh-slow-soft", "vol": 0.45})
        for w in f["palabras"]:
            if w.get("clave"):
                # el giro final pesa más que el resto
                ultima = i >= len(frases) - 2
                plan.append({"t": round(w["t"], 3),
                             "clip": "boom-hit-soft" if ultima else "impact-light-soft",
                             "vol": 0.55 if ultima else 0.6})
                break          # una por frase: si todo suena, nada suena
    return plan


plan = plan_automatico() if a.auto else json.load(open(a.plan, encoding="utf-8"))
if a.auto and not a.plan:
    destino = os.path.join(proy, "plan_sfx.json")
    json.dump(plan, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"plan propuesto ({len(plan)} efectos) → {destino}\nrevísalo y vuelve a correr con --plan")
    sys.exit(0)

desconocidos = sorted({p["clip"] for p in plan} - set(POR_ID))
if desconocidos:
    sys.exit("clips que no existen: " + ", ".join(desconocidos) +
             "\ndisponibles: " + ", ".join(sorted(POR_ID)))

entradas = ["-i", voz]
filtros, etiquetas = [], ["[0:a]"]
for n, p in enumerate(plan, start=1):
    c = POR_ID[p["clip"]]
    arranque = p["t"] - c.get("sync", {}).get("at", 0)
    if arranque < 0:
        print(f"  aviso: {p['clip']} en {p['t']}s arrancaría antes del cero; lo muevo a 0")
        arranque = 0
    entradas += ["-i", os.path.join(AQUI, "clips", p["clip"] + ".wav")]
    vol = a.volumen * p.get("vol", 1.0)
    filtros.append(f"[{n}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
                   f"adelay={int(round(arranque * 1000))},volume={vol:.3f}[s{n}]")
    etiquetas.append(f"[s{n}]")

# amix normaliza por número de entradas: lo compenso para que la voz no baje
filtros.append("".join(etiquetas) + f"amix=inputs={len(etiquetas)}:normalize=0:duration=first,"
                                    "alimiter=limit=0.95[out]")

salida = os.path.join(proy, a.salida)
cmd = ["ffmpeg", "-y", "-loglevel", "error"] + entradas + \
      ["-filter_complex", ";".join(filtros), "-map", "[out]", "-ar", "48000", "-ac", "1", salida]
subprocess.run(cmd, check=True)
print(f"{len(plan)} efectos mezclados  →  {salida}")
print("ahora renderiza con  --voz " + salida)
