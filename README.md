# Kit de producción — El Observador

Convierte una grabación de voz en un Short vertical (1080×1920, 30 fps) del canal
**El Observador**: neurología, conciencia, energía y vínculos. Las escenas van
sincronizadas palabra por palabra con la voz.

Se usa junto a la skill **shorts-lineales**, que es la que dice *qué* hacer. Este repo
es el *cómo*: el motor, las fuentes, los sonidos y un video de ejemplo.

```bash
git clone https://github.com/diegoaaron0/observador-kit
```

---

## Qué hay dentro

### `lineal/` — el estilo del canal

Figuras de línea blanca con halo sobre fondo negro. Es el único estilo que se usa.

| | |
|---|---|
| `web/escena.js` | El motor. Anima el SVG a partir de los tiempos de la voz. Todo es función del tiempo: ningún keyframe de CSS, para que cada fotograma salga igual siempre |
| `construir.py` | Prepara el proyecto: copia la escena, las fuentes y emite `datos.json` |
| `gen_dunbar.py` | **La plantilla.** Cópialo a `PROYECTO/escenas.py` y adáptalo. Trae los ayudantes `fig`, `pill`, `an` y `escena` |
| `hoja.py` | Junta los fotogramas de muestra en una hoja de contacto para revisarlos de un vistazo |
| `foto.js` | Captura un HTML suelto a PNG. Para las miniaturas |
| `base.css`, `fuentes/` | Tipografías y estilos base |
| `MOVIMIENTO.md` | **Cuánto dura cada cosa y con qué curva.** Léelo antes de escribir duraciones |
| `ESTILOS.md` | La dirección de arte: paleta, trazo, piezas que se repiten |
| `ejemplo_150/` | El guion y los tiempos de *Las 150 personas*, un video completo de referencia |

### `sonido/` — efectos

67 clips **CC0** sacados de [wyzowl/sfx-kit](https://github.com/wyzowl/sfx-kit). Cada uno
trae su punto de sincronía, así que basta decir en qué segundo ocurre la cosa y
`sonido.py` calcula dónde arrancar el archivo.

| | |
|---|---|
| `sonido.py` | Mezcla los efectos sobre la voz. Con `--auto` propone un plan desde los tiempos |
| `SONIDO.md` | **El mapa: momento del guion → clip.** Y lo que no se usa en este canal |
| `clips.json` | Los 67 clips con su uso, su duración y su punto de sincronía |

### `voz.py`

Limpia la grabación (eco, ruido, ecualización, volumen) y calcula el tiempo de cada
palabra alineando contra el guion. Produce `voz_final.wav` y `timing.json`.

### El resto

`gpu/` tiene el `render.js` que graba la pantalla a MP4, **necesario para cualquier
estilo**. `motor/`, `disenos/`, `panel/` y `ejemplo/` son del estilo de partículas y del
estilo HUD, que ya no se usan; se quedan por si algún día hacen falta.

---

## Preparación (una vez por sesión)

```bash
pip install --break-system-packages numpy scipy pillow soundfile noisereduce sherpa-onnx
cd gpu && npm install puppeteer-core
```

El modelo de alineación es **imprescindible**: sin él los tiempos se estiman por sílabas
y el video deja de ir pegado a la voz, que es de lo que vive este estilo.

```bash
mkdir -p ~/modelos && cd ~/modelos && curl -sSL -o wb.tar.bz2 \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2 \
  && tar xjf wb.tar.bz2
```

Hace falta `ffmpeg`, `google-chrome` y Node 18+.

---

## Producción de un video

```bash
# 1 · voz limpia + tiempos por palabra (guion.txt dentro de PROYECTO)
python voz.py GRABACION.m4a PROYECTO --verificar

# 2 · diseñar las escenas: copiar lineal/gen_dunbar.py y adaptarlo
python PROYECTO/escenas.py                       # → PROYECTO/tema.html

# 3 · construir
python lineal/construir.py PROYECTO PROYECTO/tema.html \
  --sub-y 1770 --tamano 46 --clave "#ffffff" --base "#8d939a" --borde "#000000"

# 4 · MIRAR los fotogramas antes de gastar el render
node gpu/render.js PROYECTO/web --web PROYECTO/web --muestras 1.2,8,18,29,40
python lineal/hoja.py PROYECTO/web

# 5 · sonido
python sonido/sonido.py PROYECTO --auto          # propone plan_sfx.json
python sonido/sonido.py PROYECTO --plan PROYECTO/plan_sfx.json

# 6 · render (≈4 s de cómputo por segundo de video)
node gpu/render.js PROYECTO/web --web PROYECTO/web \
  --voz PROYECTO/voz_con_sfx.wav --salida PROYECTO/video.mp4
```

### `guion.txt`

Una frase por línea. `*palabra*` marca clave (1–3 por frase). `[pausa +0.8]` en su propia
línea añade silencio. `#` comenta.

### Anclas y animaciones

Cada elemento lleva su instrucción encima:

```html
<g data-en="semana+0.2" data-anim="crece" data-dur="0.45">…</g>
```

**Anclas** (`data-en`): `inicio`, `fin`, `t:12.3`, `frase:N`, `palabra`, con `+0.3` / `-0.2`.
`=palabra` reutiliza la misma aparición; sin el `=` avanza al siguiente uso, así que escribe
los elementos **en el orden del guion**.

**Animaciones** (`data-anim`): `entra`, `sube`, `sale`, `crece`, `dibuja`, `pulso`, `late`,
`flota`, `empuja`, `destello`, `pan`, `gira`.

---

## Dos reglas que ahorran horas

**Mira los fotogramas dos veces.** La primera tanda casi siempre destapa elementos tapados
o fuera de cuadro. Corregirlos cuesta segundos; el render completo cuesta minutos.

**Un efecto de sonido por idea, no por elemento.** Una serie de quince puntos lleva un
sonido, no quince. Un video de 50 s aguanta entre 8 y 15 efectos.

---

## Licencias

El código es propio. Los sonidos de `sonido/clips/` son CC0 (dominio público), de
wyzowl/sfx-kit; la dedicación está en `sonido/LICENSE-sfx-kit.txt`. Las tablas de
`lineal/MOVIMIENTO.md` están adaptadas de LottieFiles/motion-design-skill, licencia MIT.
Los iconos y mapas que usa `motor/vectores.py` vienen de lucide (ISC), Tabler (MIT) y
world-atlas (dominio público).
