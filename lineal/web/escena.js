/* Anima una escena dibujada en SVG a partir de los tiempos de la voz.
   Cada elemento lleva su instrucción encima:
     data-en="palabra+0.2"   cuándo entra (palabra del guion, t:5.2, inicio, fin)
     data-anim="entra"       cómo entra
     data-dur="0.5"          cuánto tarda
   Animaciones: entra · sube · dibuja · pulso · late · flota · empuja · destello
   Todo es función del tiempo: ningún keyframe de CSS, para que cada
   fotograma salga igual siempre.                                            */

let D, ctx, piezas = [], escenas = [], W, H;

const sat = x => Math.min(1, Math.max(0, x));
const suave = x => { x = sat(x); return x * x * (3 - 2 * x); };
// Lo que entra frena al llegar (ease-out); lo que se va acelera al irse (ease-in).
// Es la diferencia entre un objeto que aterriza y uno que se escapa.
const salir = x => { x = sat(x); const p = 1 - x; return 1 - p * p * p; };   // ease-out cúbica
const entrar = x => { x = sat(x); return x * x * x; };                       // ease-in cúbica
const rebote = x => { x = sat(x); const p = x - 1; return 1 + 2.3 * p * p * p + 1.3 * p * p; };
const SALIDA = 0.7;   // lo que se va dura un 70% de lo que tarda en entrar
const norm = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

// ------------------------------------------------------------------ anclas
function resolverAnclas() {
  const lista = [];
  for (const f of D.frases) for (const p of f.palabras) lista.push({ n: norm(p.texto), t: p.t });
  let cursor = 0;
  return (expr) => {
    const m = /^(.*?)([+-][\d.]+)?$/.exec(expr.trim());
    let base = m[1].trim(); const off = m[2] ? parseFloat(m[2]) : 0;
    // "=palabra" vuelve a usar la misma aparición, sin avanzar al siguiente uso:
    // sirve para colgar varios elementos de una sola palabra del guion
    const misma = base.startsWith("=");
    if (misma) base = base.slice(1).trim();
    if (base === "inicio" || base === "") return off;
    if (base === "fin") return D.duracion + off;
    if (base.startsWith("t:")) return parseFloat(base.slice(2)) + off;
    if (base.startsWith("frase:")) {
      const i = parseInt(base.slice(6), 10) - 1;
      return (D.frases[i] ? D.frases[i].inicio : 0) + off;
    }
    const q = norm(base);
    if (misma) {
      for (let i = cursor - 1; i >= 0; i--) if (lista[i].n === q) return lista[i].t + off;
      for (let i = cursor; i < lista.length; i++) if (lista[i].n === q) return lista[i].t + off;
    }
    for (let i = cursor; i < lista.length; i++)
      if (lista[i].n === q) { cursor = i + 1; return lista[i].t + off; }
    for (let i = 0; i < lista.length; i++)
      if (lista[i].n === q) return lista[i].t + off;
    console.warn("ancla sin palabra:", expr);
    return 0;
  };
}

// ------------------------------------------------------------------ carga
async function preparar(base) {
  D = await (await fetch(base + "/datos.json")).json();
  W = D.W; H = D.H;
  const esc = document.getElementById("esc");
  esc.style.width = W + "px"; esc.style.height = H + "px";

  let cv = document.getElementById("subs");
  if (!cv) {
    cv = document.createElement("canvas"); cv.id = "subs";
    cv.style.cssText = "position:absolute;inset:0";
    esc.appendChild(cv);
  }
  cv.width = W; cv.height = H; ctx = cv.getContext("2d");

  const ancla = resolverAnclas();

  // las escenas se resuelven primero, para que marquen el orden del relato
  escenas = [...esc.querySelectorAll("[data-escena]")].map(el => ({ el, t: ancla(el.dataset.escena) }));
  escenas.sort((a, b) => a.t - b.t);
  escenas.forEach((s, i) => { s.fin = i + 1 < escenas.length ? escenas[i + 1].t : D.duracion + 1; });

  piezas = [...esc.querySelectorAll("[data-anim]")].map(el => {
    const p = {
      el, anim: el.dataset.anim,
      t: ancla(el.dataset.en || "inicio"),
      dur: parseFloat(el.dataset.dur || "0.5"),
      amp: parseFloat(el.dataset.amp || "1"),
      vel: parseFloat(el.dataset.vel || "1"),
      color: el.dataset.color || null,
      visible: el.dataset.visible === "1" || el.dataset.anim === "destello" || el.dataset.anim === "sale" || el.dataset.anim === "pan",
      dir: (el.dataset.dir || "0,0").split(",").map(Number),
      base: el.getAttribute("fill") || null,
    };
    if (p.anim === "dibuja") {
      p.largo = 0;
      for (const sub of el.querySelectorAll("path")) p.largo = Math.max(p.largo, sub.getTotalLength());
      if (!p.largo && el.getTotalLength) p.largo = el.getTotalLength();
    }
    el.style.opacity = p.visible ? "1" : "0";
    return p;
  });

  await document.fonts.ready;
  return { duracion: D.duracion, piezas: piezas.length, W, H };
}

// ------------------------------------------------------------------ fotograma
const CRUCE = 0.34;                       // cuánto dura el cambio de escena

function frame(t) {
  for (const s of escenas) {
    const entra = salir((t - s.t) / CRUCE);
    const sale = 1 - entrar((t - (s.fin - CRUCE * SALIDA * 0.6)) / (CRUCE * SALIDA));
    const a = Math.min(entra, sale);
    s.el.style.display = a <= 0.002 ? "none" : "block";
    if (a <= 0.002) continue;
    s.el.style.opacity = a.toFixed(3);
    // la escena entra empujando un poco y la anterior se va encogiendo
    const k = 1 + 0.045 * (1 - entra) - 0.035 * (1 - sale);
    s.el.style.transform = `scale(${k.toFixed(4)}) translateY(${((1 - entra) * 26 - (1 - sale) * 18).toFixed(1)}px)`;
  }

  for (const p of piezas) {
    const dt = t - p.t, k = sat(dt / p.dur);
    const el = p.el;
    if (dt < -0.001) { el.style.opacity = p.visible ? "1" : "0"; continue; }
    el.style.opacity = p.visible ? "1" : salir(k).toFixed(3);
    switch (p.anim) {
      case "entra":
        el.style.transform = `scale(${(0.86 + 0.14 * rebote(k)).toFixed(4)})`;
        break;
      case "sube":
        el.style.transform = `translateY(${((1 - salir(k)) * 30 * p.amp).toFixed(2)}px)`;
        break;
      case "dibuja":
        el.style.strokeDasharray = p.largo;
        el.style.strokeDashoffset = (p.largo * (1 - salir(k))).toFixed(1);
        break;
      case "pulso": {
        const e0 = p.visible ? 1 : 0.86 + 0.14 * rebote(k);
        const s = e0 + (k >= 1 ? 0.035 * p.amp * Math.sin(dt * 6.2831 * 1.1 * p.vel) : 0);
        el.style.transform = `scale(${s.toFixed(4)})`;
        break;
      }
      case "late": {
        const e1 = p.visible ? 1 : 0.86 + 0.14 * rebote(k);
        const s = e1 + (k >= 1 ? 0.05 * p.amp * Math.sin(dt * 6.2831 * 0.9 * p.vel) : 0);
        el.style.transform = `scale(${s.toFixed(4)})`;
        break;
      }
      case "flota":
        el.style.transform = `translateY(${(Math.sin(dt * 1.5 * p.vel) * 14 * p.amp - (1 - salir(k)) * 26).toFixed(2)}px)`;
        break;
      case "empuja": {
        const v = k < 1 ? (1 - salir(k)) * -70 : 0;
        const osc = k >= 1 ? (1 - Math.cos(dt * 6.2831 * 0.85 * p.vel)) * 0.5 * 26 * p.amp : 0;
        el.style.transform = `translate(${((v + osc) * p.dir[0]).toFixed(2)}px, ${((v + osc) * p.dir[1]).toFixed(2)}px)`;
        break;
      }
      case "sale": {
        const ks = sat(dt / (p.dur * SALIDA));
        el.style.opacity = (1 - entrar(ks)).toFixed(3);
        el.style.transform = `translateY(${(-entrar(ks) * 34 * p.amp).toFixed(2)}px)`;
        break;
      }
      case "pan":
        el.style.transform = `translate(${(p.dir[0] * p.amp * dt).toFixed(2)}px, ${(p.dir[1] * p.amp * dt).toFixed(2)}px)`;
        break;
      case "gira":
        el.style.transform = `rotate(${(p.amp * dt).toFixed(2)}deg)`;
        break;
      case "crece":
        el.style.transform = `scale(${(0.72 + 0.28 * rebote(k)).toFixed(4)})`;
        break;
      case "destello": {
        const f = k < 1 ? salir(k) : Math.max(0, 1 - (dt - p.dur) / 0.9);
        if (p.color && p.base) {
          el.style.fill = f > 0.02 ? mezcla(p.base, p.color, f * 0.85) : p.base;
        }
        el.style.opacity = "1";
        break;
      }
    }
  }
  subtitulos(t);
}

function mezcla(a, b, k) {
  const h = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
  const [r1, g1, b1] = h(a), [r2, g2, b2] = h(b);
  const m = (x, y) => Math.round(x + (y - x) * k);
  return `rgb(${m(r1, r2)},${m(g1, g2)},${m(b1, b2)})`;
}

// ------------------------------------------------------------------ subtítulos
function subtitulos(t) {
  ctx.clearRect(0, 0, W, H);
  const S = D.subtitulos;
  if (!S || S.mostrar === false) return;
  const fn = `900 ${S.tamano}px "Mont"`, fk = `900 ${Math.round(S.tamano * 1.04)}px "Mont"`;
  for (let i = 0; i < D.frases.length; i++) {
    const f = D.frases[i];
    const sig = i + 1 < D.frases.length ? D.frases[i + 1].inicio : D.duracion;
    const fin = Math.min(f.fin + 0.5, sig - 0.28);
    if (!(f.inicio - 0.05 <= t && t < fin + 0.25)) continue;
    const fo = 1 - suave((t - fin) / 0.25);
    let items, lineas;
    for (const k of [1, 0.91, 0.83, 0.76]) {
      const sz = Math.round(S.tamano * k);
      const fn2 = `900 ${sz}px "Mont"`, fk2 = `900 ${Math.round(sz * 1.04)}px "Mont"`;
      items = f.palabras.map(w => {
        ctx.font = w.clave ? fk2 : fn2;
        return { ...w, f: w.clave ? fk2 : fn2, w: ctx.measureText(w.texto).width, sp: ctx.measureText(" ").width };
      });
      lineas = []; let cur = [], cw = 0;
      for (const it of items) {
        if (cur.length && cw + it.sp + it.w > 940) { lineas.push(cur); cur = []; cw = 0; }
        cw += (cur.length ? it.sp : 0) + it.w; cur.push(it);
      }
      lineas.push(cur);
      if (lineas.length <= 3) break;
    }
    const y0 = S.y - (lineas.length - 1) * 38;
    for (let li = 0; li < lineas.length; li++) {
      const ln = lineas[li];
      const lw = ln.reduce((s, x) => s + x.w, 0) + ln.slice(1).reduce((s, x) => s + x.sp, 0);
      let x = (W - lw) / 2; const y = y0 + li * 76;
      for (let k = 0; k < ln.length; k++) {
        const it = ln[k]; if (k) x += it.sp;
        const pr = suave((t - it.t + 0.04) / 0.17);
        if (pr > 0) {
          ctx.save();
          ctx.font = it.f; ctx.textBaseline = "alphabetic";
          ctx.globalAlpha = pr * fo;
          ctx.lineWidth = 14; ctx.lineJoin = "round"; ctx.strokeStyle = S.borde || "#10131c";
          const dy = (1 - pr) * 12;
          ctx.strokeText(it.texto, x, y + dy);
          ctx.fillStyle = it.clave ? S.color_clave : (S.color_base || "#ffffff");
          ctx.fillText(it.texto, x, y + dy);
          ctx.restore();
        }
        x += it.w;
      }
    }
  }
}

window.preparar = preparar;
window.frame = frame;
