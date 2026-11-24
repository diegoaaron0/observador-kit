# Kit de Shorts — partículas en GPU

Convierte una grabación de voz en un Short vertical (1080×1920, 30 fps) donde una
nube de partículas se transforma en figuras, sincronizada palabra por palabra.

## Instalación (una vez por sesión)

```bash
pip install --break-system-packages numpy scipy pillow soundfile noisereduce nara-wpe sherpa-onnx
cd gpu && npm install            # three no es necesario: el motor es WebGL2 puro
```

Requisitos del sistema: `ffmpeg`, `google-chrome` (el render usa Chrome headless),
y Node 18+. El modelo de alineación (opcional pero recomendado) va en
`~/modelos/sherpa-onnx-whisper-base`.

## Flujo completo

```bash
# 1 · carpeta del proyecto
mkdir v8 && cd v8
#    escribe guion.txt y deja ahí la grabación

# 2 · voz limpia + tiempos por palabra
python kit/voz.py grabacion.m4a v8 --verificar

# 3 · diseña escenas.json (ver vocabulario abajo)

# 4 · exporta las formas a nubes de puntos
python gpu/exportar.py v8 --particulas 36000

# 5 · revisa cuatro fotogramas antes de gastar el render
node gpu/render.js v8/gpu --muestras 1.2,8,18,29

# 6 · render completo (~8 s de cómputo por segundo de video)
node gpu/render.js v8/gpu --voz v8/voz_final.wav --salida v8/video.mp4
```

## guion.txt

Una frase por línea. `*palabra*` marca palabra clave (se ve dorada y en cursiva,
y dispara la onda de partículas). `[pausa +0.6]` en su propia línea añade silencio.
`#` comenta.

## escenas.json

```jsonc
{
  "estela": 0.62,            // cuánto rastro dejan las partículas
  "inicio_formado": true,    // el primer fotograma ya muestra la figura armándose
  "final": {"tipo": "zoom", "desde": "fin+0.9", "velocidad": 1.35},
  "subtitulos": {"y": 1430, "tamano": 60, "color_clave": "dorado"},
  "escenas": [
    {"en": "inicio", "forma": "cerebro"},
    {"en": "corazón", "forma": "mascara", "archivo": "disenos/corazon.png", "color": "rojo"},
    {"en": "frase:4", "forma": "grupo", "partes": [
      {"forma": "persona", "color": "cian", "dx": -210, "peso": 0.5},
      {"forma": "persona", "color": "dorado", "dx": 210, "peso": 0.5}]}
  ]
}
```

**Anclas (`en`)**: `inicio`, `fin`, `t:12.3`, `frase:4`, `frase:4/palabra`, o
directamente una palabra del guion (toma la siguiente aparición). Admite `+0.3` / `-0.2`.

**Formas**: `icono` y `mapa` (ver abajo, son las principales), `globo`, `dos_globos`,
`ojo`, `persona`, `cabeza`, `marco`, `cerebro`,
`cara`, `onda`, `pensamiento`, `texto`, `mascara` (PNG blanco sobre negro 1080×1920),
`dispersion`, `espiral`, `grupo` (combina varias con `peso`).

**Transformaciones** por escena o por parte: `dx`, `dy`, `escala`, `rotar`, `brillo`,
`color`. Un valor puede animarse: `{"de": 0, "a": 200, "dur": 1.2}` o
`{"base": 540, "osc": 270, "vel": 0.55}`.

**Extras**: `rotulo` (texto pequeño arriba, para citar el estudio), `rigidez`
(qué tan rápido se arma la figura), `efecto: "glitch"`.

## Vocabulario visual: `icono` y `mapa`

Lo que hace que un video no se sienta decorativo es que cada figura ilustre la
palabra que se está diciendo. Para eso hay ~8.200 iconos vectoriales y los
contornos de todos los países, instalados con npm (`lucide-static` ISC,
`@tabler/icons` MIT, `world-atlas` dominio público).

```json
{"en": "pueblo", "forma": "icono", "nombre": "building-cottage", "alto": 380, "color": "blanco"}
{"en": "España", "forma": "mapa",  "pais": "España", "alto": 560, "color": "dorado"}
```

`icono`: `nombre`, `alto` (px), `color`, `x`, `y`, `grosor`.
`mapa`: `pais`, `alto`, `color`, `x`, `y`, `trozos` (cuántas islas conserva).

Las partículas se reparten por longitud de arco a lo largo del trazo, así que
quedan parejas y las curvas salen limpias a cualquier tamaño.

**Encontrar el icono de una palabra** (los nombres están en inglés):

```bash
python motor/vectores.py buscar fuego          # lista nombres que coinciden
python motor/vectores.py buscar flame
python motor/vectores.py ver home,flame,mapa:España hoja.png   # hoja de contacto
```

Mira siempre la hoja de contacto antes de diseñar: hay nombres que no son lo que
parecen (`campfire` es una gota sobre leños, el fuego de verdad es `flame-kindling`).

Para "un pueblo", "el público" y cosas en plural, combina varios iconos con `grupo`:

```json
{"en": "pueblo", "forma": "grupo", "partes": [
  {"forma": "icono", "nombre": "building-cottage", "alto": 300, "dx": -300, "dy": 60, "peso": 0.3},
  {"forma": "icono", "nombre": "building-cottage", "alto": 380, "dy": -40,  "peso": 0.4},
  {"forma": "icono", "nombre": "building-cottage", "alto": 290, "dx": 300,  "dy": 70, "peso": 0.3}]}
```

Dos escenas casi iguales cuentan un cambio mejor que dos escenas distintas: dos
pulsos separados → los mismos dos pulsos alineados dice "al mismo tiempo" sin
explicarlo. Un pulso al lado de una línea plana dice "los desconocidos, no".

Con `trazos` te quedas con parte del dibujo: en el ojo, `"trazos": [1]` deja solo
el contorno sin iris, para ponerle uno propio que se mueva.

## Que nada quede congelado

El ritmo se cae cuando una figura se queda quieta más de dos segundos. Tres
herramientas, en orden de importancia:

**1. Más escenas.** Lo que más se nota. Apunta a una escena cada 0,8–1,2 s, también
en la segunda mitad del guion, que es donde suele haber menos sustantivos concretos.
Si una frase no tiene nada que ilustrar, ancla una escena en un verbo o en un
conector ("quizá" → un signo de interrogación).

**2. `latido`** — la figura late mientras está en pantalla. Para corazones y pulsos:

```json
{"en": "amas", "forma": "icono", "nombre": "heart", "latido": {"amp": 0.05, "vel": 1.15}}
```

**3. `vida`** — multiplica la onda que recorre el contorno (1 por defecto; 2 o 3
para una figura que se queda sola un rato).

**Partes que se mueven**: cualquier `dx`, `dy`, `x` o `y` puede oscilar, y el
movimiento lo hace la GPU mientras la escena está en pantalla:

```json
{"en": "mira", "forma": "grupo", "partes": [
  {"forma": "icono", "nombre": "eye", "trazos": [1], "alto": 300, "peso": 0.74},
  {"forma": "icono", "nombre": "circle", "alto": 150, "color": "cian", "peso": 0.26,
   "dx": {"base": 0, "osc": 115, "vel": 0.6}}]}
```

Eso es el ojo mirando de lado a lado: `osc` son los píxeles de recorrido y `vel`
los ciclos por segundo. Calcula `vel` para que entre al menos una ida y vuelta en
el tiempo que la escena está en pantalla.

## Qué hace la GPU

El motor Python solo entrega una nube de puntos por escena. Todo el movimiento ocurre
en el shader (`gpu/web/motor.js`):

1. **Viaje escalonado**: cada partícula sale en un momento distinto y llega con rebote.
2. **Trayectoria en arco**: no viajan en línea recta, se curvan.
3. **Banco de puntos**: dispersión radial por partícula, para que el trazo no sea una línea sólida.
4. **Vida en reposo**: ruido suave que respira, más intenso durante el viaje.
5. **Onda en palabra clave**: empuje radial que se desvanece en 0.4 s.
6. **Profundidad**: eje z con paralaje, tamaño y brillo según la distancia.
7. **Tamaños mezclados**: 62 % polvo, 33 % medias, 5 % brillantes.
8. **Estela por velocidad**: realimentación de fotograma; lo que va rápido deja rastro largo.

Ajustes rápidos en `gpu/web/motor.js`: `SPREAD` (escalonado), el `0.30` del arco,
los tres tamaños/brillos, y los multiplicadores de `FS_FINAL` (nitidez vs brillo).
