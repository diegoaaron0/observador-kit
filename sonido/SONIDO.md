# Sonido: qué suena en cada momento

67 clips CC0 de `wyzowl/sfx-kit`. Cada uno trae su punto de sincronía, así que basta
decir en qué segundo ocurre la cosa: `sonido.py` calcula el arranque del archivo.
La lista completa con su uso está en `clips.json`.

## La regla que importa

**Un efecto por idea, no por elemento.** Una serie de quince puntos que entran
escalonados lleva UN sonido, no quince. Si todo suena, nada suena, y la voz se pierde.

Un video de 50 s aguanta entre 8 y 15 efectos. `--auto` propone más que eso a
propósito, para que quites: es más fácil borrar que inventar.

Volumen: nunca por encima de 0.6. Comprueba con `ffmpeg -af ebur128` que la mezcla no
sube más de ~0.5 LUFS sobre la voz sola.

## Mapa rápido

| Momento del guion | Clip |
|---|---|
| Cambio de escena, normal | `whoosh-slow-soft` |
| Cambio rápido, corte seco | `whoosh-medium-soft`, `swish-soft` |
| Entra algo por un lado | `zip-in-soft` · se va: `zip-out-soft` |
| Aparece una figura pequeña | `pop-small-in` |
| Aparece una píldora o etiqueta | `pop-medium-in` |
| Una cifra grande se revela | `shimmer-medium-soft` + `data-number-land` |
| Un contador corre | `data-countup-medium` (1,2 s) o `data-countup-long` (2,2 s) |
| Una barra o un anillo crece | `data-bar-grow`, `transform-grow` |
| Un diagrama aparece | `data-chart-reveal` |
| Un trazo se dibuja (`anim dibuja`) | `writing-pen-draw`, `writing-pencil-draw` |
| Subrayar una palabra | `writing-highlighter` |
| Borrar y empezar bloque nuevo | `writing-wipe` |
| De muchos a pocos (1.500 → 150) | `transform-shrink` |
| Algo se llena / se vacía | `transform-fill` / `transform-empty` |
| Capas que se nombran una a una | `tone-step-1` … `tone-step-5` |
| Algo se apaga, un vínculo que se degrada | `faller-4s-soft` |
| Tensión antes de una revelación | `riser-2s-soft`, `reverse-whoosh-medium-soft` |
| **El giro final** | `boom-hit-soft`, o `bass-sub-drop-medium` bajo la frase |
| Acento sobre una palabra clave | `impact-light-soft` (suave), `impact-heavy-soft` (con peso) |
| Cierre | `sting-minimal-short` |

## Lo que no se usa en este canal

`notifications`, `interface`, `keyboard`, `money`, `phone`, `celebration` y casi todo
`digital`: suenan a aplicación o a videojuego, y aquí se habla bajito. `cinematic-thunder-big`
y `cinematic-drum-big` están, pero son para un cierre que de verdad lo pida: uno por video
como mucho, y muchos videos no lo piden.
