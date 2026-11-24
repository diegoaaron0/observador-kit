# Movimiento: cuánto dura y con qué curva

Tablas adaptadas de **LottieFiles/motion-design-skill** (licencia MIT). El original está
escrito para interfaces (botones, modales); aquí quedan traducidas a lo que hacemos:
vídeo vertical, figuras de línea, todo colgado de los tiempos de una voz.

## Lo que ya hace el motor solo

No hay que pedirlo, `escena.js` lo aplica:

| Regla | Cómo está implementado |
|---|---|
| Lo que entra frena al llegar | `salir()`, ease-out cúbica, en toda aparición |
| Lo que se va acelera al irse | `entrar()`, ease-in cúbica, en `sale` y al cerrar escena |
| La salida dura menos que la entrada | `SALIDA = 0.7` sobre la duración declarada |
| Un trazo frena al cerrarse | `dibuja` usa ease-out |

La diferencia se nota sobre todo en los cortes: antes las escenas entraban y salían con
la misma curva y el cambio se sentía plano.

## Lo que decides tú al escribir las escenas

### Duración según lo que aparece

| Qué es | `data-dur` |
|---|---|
| Un elemento de una serie (un punto, una celda) | 0.25–0.35 |
| Una píldora, una etiqueta, una figura | 0.35–0.45 |
| Un diagrama que se dibuja | 0.6–0.8 |
| **La cifra grande del gancho** | **0.6–1.2** |

La cifra de apertura es una revelación, no un elemento de lista: dale 0.6 s como mínimo.
Durante mucho tiempo le pusimos 0.45 s, lo mismo que a una etiqueta, y por eso pasaba sin
pesar.

### La duración escala con la distancia

Si algo recorre más camino, necesita más tiempo o se ve teletransportado:

`100px = 1.0x · 200px = 1.3x · 300px = 1.5x · pantalla completa = 1.8–2.0x`

Aplica al desplazamiento de `empuja`, `sube` y a las figuras que cruzan el cuadro.

### Escalonado de una serie

Cuando entran varios elementos iguales (los puntos de un anillo, las celdas de un
calendario, las figuras de una fila):

| Cuántos | Separación entre uno y otro | Total |
|---|---|---|
| 3–8 | 0.05–0.08 s | < 0.5 s |
| 10–20 | 0.03–0.04 s | < 0.7 s |
| más de 30 | 0.01–0.02 s | < 1 s |

Se escribe con el ancla repetida y un desfase creciente: `=palabra+{0.05*i}`.

La serie entera tiene que terminar **antes** de que la voz pase a la idea siguiente. Si no
cabe, no metas más elementos: agrupa.

### Qué suena a qué

| Si quieres que se sienta | Curva | Dónde |
|---|---|---|
| Que aterriza con peso | `entra` / `crece` (rebote) | cifras, píldoras |
| Que se posa sin ruido | `sube` | etiquetas, notas al pie |
| Que se escapa | `sale` | el vínculo que se degrada |
| Que respira | `late` / `pulso` | corazón, reloj, lo que debe seguir vivo |

No mezcles rebote en todo. El rebote llama la atención, y si todo rebota deja de llamarla:
resérvalo para la cifra o la palabra que carga la frase.

## Errores que estas tablas corrigen

- Todo entrando con la misma curva y la misma duración: el ojo deja de distinguir qué
  importa.
- Salidas tan lentas como las entradas: el corte se siente pesado.
- Series largas con la misma separación que una serie corta: o se eterniza, o parpadea.
