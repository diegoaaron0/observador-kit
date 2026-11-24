# Estilos de animación

Un estilo no se aprende mirando: se descompone. Cada uno de estos salió de abrir
el video de referencia fotograma a fotograma y anotar paleta, grosores, tipografía,
piezas que se repiten y cómo entran. Una vez escrito aquí, cualquier video futuro
se construye sin volver a deducirlo.

Para añadir un estilo nuevo: extraer 16 fotogramas repartidos, hacer zoom sobre un
detalle (una etiqueta, una figura) para medir grosores, y sacar 6 fotogramas
seguidos para ver cómo se mueve. Después rellenar las cinco secciones de abajo.

---

## 1 · Lineal  (`linea.html`)

Referencia: @cps_user. Infografía blanca sobre negro, aire de dato duro.

**Paleta** — negro puro `#000`, blanco `#fff`, gris de apoyo `#8d939a`,
rojo solo para negar `#ff4d4d`. Nada más. El color entra solo cuando algo se tacha.

**Trazo** — 7 px en figuras, 5 px en líneas y marcos, 4 px en guías.
Línea de suelo punteada `stroke-dasharray="24 22"` en gris.

**Brillo** — todo va dentro de un filtro de halo (`feGaussianBlur stdDeviation="7"`
sumado al original). Es lo que separa este estilo de un SVG plano: el blanco no es
plano, tiene aura.

**Tipografía** — Archivo 700 en mayúsculas con `letter-spacing` de 4–5 px para las
etiquetas (30 px) y los pies (24 px); Archivo 900 para las cifras grandes (300 px).

**Piezas** — el glifo de persona (círculo de cabeza + arco de cuerpo) en versión
contorno y versión rellena; la píldora, que viene en dos variantes y alternarlas es
media gracia del estilo: **rellena de blanco con texto negro** para lo que afirma,
**contorno con texto blanco** para lo que describe. Además: línea de tiempo con
marcas, llave de medida, flecha con punta de galón, equis roja, cono de foco
(degradado blanco al 30 % que se desvanece), malla de puntos de fondo al 8 %.

**Movimiento** — barrido lateral lento y continuo (20–30 px/s) sobre una
composición más ancha que el cuadro; los elementos entran con `entra` o `crece`;
una figura rellena entre las de contorno es la que lleva la atención.

**Para qué sirve** — datos, porcentajes, comparaciones, "la mayoría hace X".

---

## 2 · Cine  (pendiente)

Referencia: @mindset.alchemyst. Fondo casi negro con degradado, silueta de butacas
de cine abajo, como si el video se proyectara en una sala.

**Paleta** — negro azulado `#0a0b14`, blanco, dorado `#e8c06a` para la palabra
clave y el pie de pantalla, coral `#ff5a66` y azul lavanda `#8f8fe0` para los
iconos.

**Tipografía** — grotesca muy gruesa en mayúsculas, centrada, una o dos palabras
por pantalla. La palabra clave cambia a dorado dentro de la misma frase.

**Piezas** — bocadillos de diálogo como píldoras (gris o coral), iconos planos
simples de una sola idea (nube con lluvia, calendario, coche, libreta, luna),
pie de pantalla en dorado y mayúsculas.

**Movimiento** — corte seco entre tarjetas de texto, casi sin transición; el ritmo
lo lleva la voz. Cada frase es una tarjeta.

**Para qué sirve** — frases cortas con golpe emocional, listas de pensamientos.

---

## 3 · Nocturno  (pendiente)

Referencia: FundingPips. Escena urbana monocroma en azules, de noche.

**Paleta** — azul marino `#0b1b3a` a `#061024`, azul eléctrico `#2b6cff`,
blanco para las luces. Todo el cuadro en la misma familia de azules.

**Piezas** — escena con profundidad (fondo de rascacielos con ventanas encendidas,
plano medio de un vagón, primer plano de una silueta de espaldas), tablero de
caracteres tipo aeropuerto que gira, conos de luz desde focos, rejilla de suelo
en perspectiva.

**Movimiento** — cámara casi quieta, lo que se mueve es el tablero y las luces.
La silueta de espaldas, inmóvil, es el ancla.

**Para qué sirve** — atmósfera, apertura de marca, algo que se quiere sentir
grande.

---

## Cómo se usa un estilo

Los tres comparten el mismo motor: `escena.js` lee los tiempos de la voz y anima
lo que encuentre marcado en el SVG. El estilo solo cambia el dibujo.

```html
<g data-escena="frase:3">        <!-- entra cuando empieza esa frase -->
  <g data-en="=sesenta" data-anim="crece" data-dur="0.5">
```

Animaciones: `entra` · `sube` · `sale` · `crece` · `dibuja` · `pulso` · `late` ·
`flota` · `empuja` · `destello` · `pan`.

`=palabra` cuelga varios elementos de la misma aparición de una palabra; sin el
igual, cada uso salta a la siguiente aparición en el guion.
