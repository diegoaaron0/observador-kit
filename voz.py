"""
Procesa la voz grabada y calcula los tiempos de cada palabra.

Uso:
  python voz.py GRABACION.m4a CARPETA [--sin-limpieza] [--cola 2.5] [--lufs -16] [--verificar]

CARPETA/guion.txt  (entrada): una frase por línea, tal como se grabó.
   - *palabras clave* entre asteriscos (pueden abarcar varias: *ni una sola vez.*)
   - [pausa +0.9]  en su propia línea: añade 0.9 s de silencio antes de la frase siguiente
   - líneas que empiezan por # se ignoran
Salida en CARPETA: voz_final.wav, timing.json
"""
import sys, os, re, json, argparse, subprocess, tempfile
import numpy as np, soundfile as sf

SR = 48000


# ------------------------------------------------------------- guion
def leer_guion(path):
    frases, pausa = [], 0.0
    for raw in open(path, encoding="utf-8"):
        ln = raw.strip()
        if not ln or ln.startswith("#"): continue
        m = re.match(r"^\[pausa\s*\+?([0-9.]+)\]$", ln, re.I)
        if m: pausa += float(m.group(1)); continue
        words, en = [], False
        for tok in ln.split():
            empieza = tok.startswith("*") or tok.lstrip("¿¡\"«(").startswith("*")
            if empieza: en = True
            limpio = tok.replace("*", "")
            words.append((limpio, en))
            if tok.rstrip(".,;:…!?\"»)").endswith("*") or tok.endswith("*"): en = False
        frases.append({"texto": ln.replace("*", ""), "palabras": words, "pausa_antes": pausa})
        pausa = 0.0
    return frases


def silabas(w):
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", w.lower())))


def peso(w):
    return silabas(w) + (0.6 if re.search(r"[,.…;:!?]$", w) else 0)


# ------------------------------------------------------------- limpieza
def ffmpeg_a_wav(src, dst, extra=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR)]
    if extra: cmd += ["-af", extra]
    subprocess.run(cmd + [dst], check=True)


def energia_db(x, hop=480):
    n = len(x) // hop
    fr = x[: n * hop].reshape(n, hop)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), hop / SR


def segmentos(x, min_sil=0.30, min_voz=0.12):
    db, dt = energia_db(x)
    piso = np.percentile(db, 10); pico = np.percentile(db, 98)
    umbral = max(piso + 10, pico - 38)
    voz = db > umbral
    # cerrar huecos de silencio más cortos que min_sil
    segs, i, n = [], 0, len(voz)
    while i < n:
        if voz[i]:
            j = i
            while j < n and voz[j]: j += 1
            segs.append([i * dt, j * dt]); i = j
        else: i += 1
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < min_sil: merged[-1][1] = s[1]
        else: merged.append(s)
    return [s for s in merged if s[1] - s[0] >= min_voz], umbral


def limpiar(x):
    import noisereduce as nr
    try:
        from nara_wpe.wpe import wpe
        from nara_wpe.utils import stft, istft
        x = x / (np.abs(x).max() + 1e-9) * 0.5
        X = stft(x[None], size=1024, shift=256).transpose(2, 0, 1)
        Y = wpe(X, taps=12, delay=3, iterations=5, statistics_mode="full")
        x = istft(Y.transpose(1, 2, 0), size=1024, shift=256)[0][: len(x)]
    except ImportError:
        print("  (nara_wpe no instalado: se omite quitar el eco)")
    segs, _ = segmentos(x, 0.2)
    gaps = [(a[1] + 0.05, b[0] - 0.05) for a, b in zip(segs, segs[1:]) if b[0] - a[1] > 0.25]
    if len(segs): gaps = [(0.0, max(0.0, segs[0][0] - 0.05))] + gaps
    trozos = [x[int(a * SR):int(b * SR)] for a, b in gaps if b - a > 0.1]
    if trozos:
        x = nr.reduce_noise(y=x, sr=SR, y_noise=np.concatenate(trozos), stationary=True, prop_decrease=0.6, n_fft=2048)
    else:
        x = nr.reduce_noise(y=x, sr=SR, stationary=False, prop_decrease=0.5)
    return x


CADENA = ",".join([
    "highpass=f=80",
    "agate=threshold=0.02:ratio=3:range=0.12:attack=3:release=90:knee=4",
    "equalizer=f=380:t=q:w=1.3:g=-3.5", "equalizer=f=130:t=q:w=1:g=1.5", "equalizer=f=3200:t=q:w=1.5:g=1.5",
    "deesser=i=0.4:m=0.5:f=0.5",
    "acompressor=threshold=-20dB:ratio=2:attack=15:release=160:makeup=1",
])


def lufs(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", out)[-1])


def masterizar(x, objetivo):
    with tempfile.TemporaryDirectory() as td:
        a, b, c = (os.path.join(td, f) for f in ("a.wav", "b.wav", "c.wav"))
        sf.write(a, x, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-af", CADENA, b], check=True)
        g = objetivo - lufs(b) + 1.0
        for _ in range(3):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", b, "-af",
                            f"volume={g}dB,alimiter=limit=0.80:attack=3:release=80:level=false", c], check=True)
            err = objetivo - lufs(c)
            if abs(err) < 0.4: break
            g += err
        y, _ = sf.read(c)
    return y


# ------------------------------------------------------------- alineación
def agrupar(segs, frases):
    """Agrupa segmentos consecutivos de voz en tantas frases como tiene el guion (programación dinámica)."""
    m, n = len(segs), len(frases)
    sil = np.array([sum(peso(w) for w, _ in f["palabras"]) for f in frases], float)
    span = segs[-1][1] - segs[0][0]
    rate = sum(s[1] - s[0] for s in segs) / sil.sum()
    INF = 1e18
    C = np.full((n + 1, m + 1), INF); B = np.zeros((n + 1, m + 1), int); C[0, 0] = 0
    for j in range(1, n + 1):
        for e in range(j, m + 1):
            for s in range(j - 1, e):
                if C[j - 1, s] >= INF: continue
                dur = sum(g[1] - g[0] for g in segs[s:e])
                cost = np.log(max(dur, 0.05) / (sil[j - 1] * rate)) ** 2
                # unir a través de una pausa larga cuesta: las frases suelen cortarse en los silencios más largos
                gaps = [segs[q + 1][0] - segs[q][1] for q in range(s, e - 1)]
                cost += 4.0 * sum(max(0.0, g - 0.25) for g in gaps)
                if C[j - 1, s] + cost < C[j, e]: C[j, e] = C[j - 1, s] + cost; B[j, e] = s
    grupos, e = [], m
    for j in range(n, 0, -1):
        s = B[j, e]; grupos.append(segs[s:e]); e = s
    return grupos[::-1]


def tiempos_palabras(sub, palabras):
    """Reparte las palabras sobre el tiempo con voz (saltando las micro-pausas internas)."""
    pesos = np.array([peso(w) for w, _ in palabras], float)
    total_voz = sum(b - a for a, b in sub)
    out, acc = [], 0.0
    for (w, k), p in zip(palabras, pesos):
        pos = acc / pesos.sum() * total_voz
        for a, b in sub:
            if pos <= (b - a) + 1e-6: t = a + pos; break
            pos -= (b - a)
        else: t = sub[-1][1]
        out.append({"texto": w, "clave": bool(k), "t": round(float(t), 3)})
        acc += p
    return out


# ------------------------------------------------------------- alineación con Whisper (más precisa)
NUM = {"0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro", "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve",
       "10": "diez", "15": "quince", "20": "veinte", "30": "treinta", "40": "cuarenta", "50": "cincuenta", "60": "sesenta", "100": "cien"}


def _norm(w):
    import unicodedata
    w = NUM.get(re.sub(r"[^0-9]", "", w), w) if re.fullmatch(r"\W*\d+\W*", w) else w
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-zñ]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def _modelo():
    m = os.path.expanduser("~/modelos/sherpa-onnx-whisper-base/")
    if not os.path.exists(m + "base-encoder.onnx"): return None
    import sherpa_onnx
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m + "base-encoder.onnx", decoder=m + "base-decoder.onnx",
                                                      tokens=m + "base-tokens.txt", language="es", task="transcribe")


def alinear_whisper(x, frases, rec):
    """En cada pausa transcribe lo dicho desde el último ancla y cuenta cuántas palabras del guion cubre."""
    from difflib import SequenceMatcher
    from scipy.signal import resample_poly
    x16 = resample_poly(x, 1, 3).astype(np.float32)
    words = [(_norm(w), j, w, k) for j, f in enumerate(frases) for (w, k) in f["palabras"]]
    W = [w[0] for w in words]
    segs, _ = segmentos(x, 0.12)
    grupos, cur_s, cur_w = [], 0, 0
    for k in range(len(segs)):
        a, e = segs[cur_s][0], segs[k][1]
        ultimo = k == len(segs) - 1
        if not ultimo and (e - a < 1.4 or segs[k + 1][0] - e < 0.15): continue
        if ultimo: c = len(W) - cur_w
        else:
            st = rec.create_stream(); st.accept_waveform(16000, x16[int(max(0, a - 0.1) * 16000):int((e + 0.1) * 16000)])
            rec.decode_stream(st)
            hyp = " ".join(_norm(t) for t in st.result.text.split() if _norm(t))
            best, c = -1, 0
            for cc in range(0, len(W) - cur_w + 1):
                ref = " ".join(W[cur_w:cur_w + cc])
                sc = SequenceMatcher(None, hyp, ref).ratio()
                if sc > best: best, c = sc, cc
        grupos.append((segs[cur_s:k + 1], cur_w, cur_w + c))
        cur_s, cur_w = k + 1, cur_w + c
    # tiempos por palabra dentro de cada grupo
    t_w = [None] * len(W)
    for sub, w0, w1 in grupos:
        if w1 <= w0: continue
        pal = tiempos_palabras(sub, [(words[i][2], words[i][3]) for i in range(w0, w1)])
        for i, p in zip(range(w0, w1), pal): t_w[i] = p["t"]
    fin_grupo = {}
    for sub, w0, w1 in grupos:
        for i in range(w0, w1): fin_grupo[i] = sub[-1][1]
    out = []
    idx = 0
    for j, f in enumerate(frases):
        n = len(f["palabras"]); ids = list(range(idx, idx + n)); idx += n
        a0 = t_w[ids[0]]
        nxt = ids[-1] + 1
        if nxt < len(W) and fin_grupo.get(nxt) == fin_grupo.get(ids[-1]): b0 = t_w[nxt] - 0.05
        else: b0 = fin_grupo[ids[-1]]
        out.append((a0, b0, [{"texto": words[i][2], "clave": bool(words[i][3]), "t": round(float(t_w[i]), 3)} for i in ids]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grabacion"); ap.add_argument("carpeta")
    ap.add_argument("--sin-limpieza", action="store_true"); ap.add_argument("--cola", type=float, default=2.5)
    ap.add_argument("--lufs", type=float, default=-16.0); ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--sin-whisper", action="store_true")
    a = ap.parse_args()
    frases = leer_guion(os.path.join(a.carpeta, "guion.txt"))
    print(f"Guion: {len(frases)} frases")
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, "in.wav"); ffmpeg_a_wav(a.grabacion, w); x, _ = sf.read(w)
    if not a.sin_limpieza:
        print("Limpiando voz (eco, ruido, ecualización, volumen)…")
        x = masterizar(limpiar(x), a.lufs)
    # recortar silencio inicial/final
    segs, _ = segmentos(x, 0.3)
    x0 = max(0, int((segs[0][0] - 0.15) * SR)); x1 = min(len(x), int((segs[-1][1] + 0.3) * SR))
    x = x[x0:x1]
    # segmentar y alinear
    for ms in (0.15, 0.10, 0.07):  # segmentación fina; la programación dinámica decide cómo agrupar
        segs, _ = segmentos(x, ms)
        if len(segs) >= len(frases): break
    if len(segs) < len(frases):
        raise SystemExit(f"Solo encontré {len(segs)} bloques de voz para {len(frases)} frases. ¿El guion coincide con lo grabado?")
    rec = _modelo()
    alin = alinear_whisper(x, frases, rec) if rec and not a.sin_whisper else None
    if alin: print("Alineación con Whisper")
    grupos = agrupar(segs, frases) if not alin else None
    finos, _ = segmentos(x, 0.10)
    # insertar pausas marcadas
    piezas, cursor, shift, out_frases = [], 0, 0.0, []
    for fi, f in enumerate(frases):
        if alin: a0, b0, pal_w = alin[fi]
        else: g = grupos[fi]; a0, b0 = g[0][0], g[-1][1]
        if f["pausa_antes"] > 0:
            prev_end = out_frases[-1]["_b0"] if out_frases else 0.0
            # cortar en el silencio más largo entre las dos frases (nunca sobre una palabra)
            lo, hi = prev_end - 0.6, a0 + 0.3
            huecos = [(finos[i][1], finos[i + 1][0]) for i in range(len(finos) - 1) if finos[i][1] >= lo and finos[i + 1][0] <= hi]
            g = max(huecos, key=lambda h: h[1] - h[0]) if huecos else (prev_end, a0)
            cut = int(((g[0] + g[1]) / 2) * SR)
            piezas.append(x[cursor:cut]); piezas.append(np.zeros(int(f["pausa_antes"] * SR))); cursor = cut
            shift += f["pausa_antes"]
        if alin: pal = [dict(p) for p in pal_w]
        else:
            sub = [(max(a0, s[0]), min(b0, s[1])) for s in finos if s[1] > a0 and s[0] < b0] or [(a0, b0)]
            pal = tiempos_palabras(sub, f["palabras"])
        for p in pal: p["t"] = round(p["t"] + shift, 3)
        out_frases.append({"texto": f["texto"], "inicio": round(a0 + shift, 3), "fin": round(b0 + shift, 3), "palabras": pal, "_b0": b0})
    piezas.append(x[cursor:]); piezas.append(np.zeros(int(a.cola * SR)))
    y = np.concatenate(piezas)
    sf.write(os.path.join(a.carpeta, "voz_final.wav"), y, SR)
    for f in out_frases: f.pop("_b0")
    json.dump({"duracion": round(len(y) / SR, 3), "frases": out_frases}, open(os.path.join(a.carpeta, "timing.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Listo: {len(y) / SR:.1f} s\n")
    for i, f in enumerate(out_frases, 1):
        print(f"{i:2d}  {f['inicio']:6.2f}–{f['fin']:6.2f}  {f['texto']}")
    if a.verificar: verificar(y, out_frases)


def verificar(y, frases):
    """Transcribe cada frase con Whisper (si el modelo está en ~/modelos/sherpa-onnx-whisper-base) para comprobar la alineación."""
    m = os.path.expanduser("~/modelos/sherpa-onnx-whisper-base/")
    if not os.path.exists(m + "base-encoder.onnx"):
        print("\n(Para verificar: descargar el modelo, ver README)"); return
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m + "base-encoder.onnx", decoder=m + "base-decoder.onnx",
                                                     tokens=m + "base-tokens.txt", language="es", task="transcribe")
    print("\nVerificación (lo que se oye en cada tramo):")
    for i, f in enumerate(frases, 1):
        s = rec.create_stream()
        s.accept_waveform(SR, y[int(max(0, f["inicio"] - 0.1) * SR):int((f["fin"] + 0.15) * SR)].astype(np.float32))
        rec.decode_stream(s); print(f"{i:2d}  {s.result.text}")


if __name__ == "__main__":
    main()
