# Estilo lineal (único estilo del canal)

```bash
# 1 · voz limpia + tiempos (guion.txt en PROYECTO)
python kit_observador/voz.py grabacion.m4a PROYECTO --verificar
# 2 · diseñar escenas: copiar gen_dunbar.py a PROYECTO/escenas.py y adaptarlo
python PROYECTO/escenas.py                     # → PROYECTO/tema.html
# 3 · construir y revisar fotogramas
python lineal/construir.py PROYECTO PROYECTO/tema.html --sub-y 1770 --tamano 46 --clave "#ffffff" --base "#8d939a" --borde "#000000"
node kit_observador/gpu/render.js PROYECTO/web --web PROYECTO/web --muestras 1.2,8,18,29
python lineal/hoja.py PROYECTO/web             # → hoja de contacto para mirarlos
# 4 · render final (~4 s de cómputo por segundo de video)
node kit_observador/gpu/render.js PROYECTO/web --web PROYECTO/web --voz PROYECTO/voz_final.wav --salida PROYECTO/video.mp4
```
Anclas: `inicio`, `fin`, `t:12.3`, `frase:N`, `palabra±0.3`, `=palabra` (misma aparición).
Animaciones: entra, sube, sale, crece, dibuja, pulso, late, flota, empuja, destello, pan, gira.
Nunca pongas `transform=` en el mismo elemento que lleva `data-anim`.

## Sonido (opcional pero recomendado)

```bash
python kit_observador/sonido/sonido.py PROYECTO --auto        # propone plan_sfx.json
# revisa y quita lo que sobre, luego:
python kit_observador/sonido/sonido.py PROYECTO --plan PROYECTO/plan_sfx.json
# y renderiza con la pista mezclada:
node kit_observador/gpu/render.js PROYECTO/web --web PROYECTO/web --voz PROYECTO/voz_con_sfx.wav --salida PROYECTO/video.mp4
```
Los clips están en `sonido/clips/` con su uso en `sonido/clips.json`. Cada uno trae su
punto de sincronía, así que basta decir en qué segundo pasa la cosa. Son CC0.

Ver también `lineal/MOVIMIENTO.md` para duraciones y curvas.
