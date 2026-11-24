# Plantilla "panel" — portada y cierre 16:9

Mismo pipeline que las partículas (Chrome headless + ffmpeg), pero la imagen es
HTML y SVG en vez de una nube de puntos: fondo con estrellas, rejilla en
perspectiva, título, píldora y una fila de insignias que entran una a una.
Render ~4,6 s de cómputo por segundo de video, contra ~8 s de las partículas.

```bash
python panel/construir.py panel/portada.json salida_portada
node  gpu/render.js salida_portada --web panel/web --muestras 2.9,9.4
node  gpu/render.js salida_portada --web panel/web --salida portada.mp4
```

## El JSON

```json
{
  "ancho": 1920, "alto": 1080, "duracion": 10.0,
  "titulo": "CÓMO TE ENGAÑA TU CEREBRO",
  "pildora": "EL OBSERVADOR · neurociencia",
  "subtitulo": "SIETE COSAS QUE DECIDEN POR TI",
  "logo": "eye",
  "insignia_desde": 2.3, "insignia_paso": 0.34,
  "insignias": [
    {"etiqueta": "MEMORIA", "icono": "brain", "color": "naranja"},
    {"etiqueta": "ATENCIÓN", "icono": "eye",  "color": "cian"}
  ]
}
```

`icono` usa los mismos nombres que las partículas, así que el buscador sirve igual:
`python motor/vectores.py buscar fuego`. Colores: naranja, cian, dorado, verde,
violeta, rojo, o un `#rrggbb`.

El título se encoge solo hasta caber en una línea y las insignias se reparten
solas: con más de siete se juntan, con menos se separan. Siete es el máximo cómodo.

Para el cierre, el mismo archivo con `"tipo": "cierre"`: el logo pasa al centro y
late, el título se vuelve el nombre del canal y la píldora la llamada a la acción
(`panel/cierre.json`).

## Si falta algo

Todo es función del tiempo dentro de `web/hud.js` (ninguna animación de CSS, para
que cada fotograma salga igual siempre). Los tiempos de entrada están en `frame()`
y las posiciones en `preparar()`, las dos en fracciones del alto.
