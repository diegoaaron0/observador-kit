/* Plantilla "panel": portada 16:9 con rejilla en perspectiva, estrellas y una
   fila de insignias que entran una a una. Todo es función del tiempo: ninguna
   animación de CSS, para que cada fotograma salga igual siempre.           */

let D, W, H, ctx, estrellas, marcas = [], ultimo = -1;

const sat = x => Math.min(1, Math.max(0, x));
const suave = x => { x = sat(x); return x * x * (3 - 2 * x); };
const salida = x => 1 - Math.pow(1 - sat(x), 3);
const rebote = x => {           // llega pasándose un poco y se asienta
  x = sat(x); const p = x - 1;
  return 1 + 2.2 * p * p * p + 1.2 * p * p;
};

function azar(semilla) {
  let s = semilla >>> 0;
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
}

// ------------------------------------------------------------------ fondo
function fondo(t) {
  ctx.clearRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W / 2, H * 0.42, 0, W / 2, H * 0.42, W * 0.72);
  g.addColorStop(0, "#0a1726"); g.addColorStop(0.55, "#060d17"); g.addColorStop(1, "#04070d");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

  for (const e of estrellas) {                       // polvo de estrellas
    const a = e.a * (0.45 + 0.55 * Math.sin(t * e.v + e.f));
    ctx.fillStyle = `rgba(190,215,240,${a.toFixed(3)})`;
    ctx.fillRect(e.x, e.y, e.r, e.r);
  }

  // rejilla en perspectiva: el suelo del plano
  const hor = H * 0.62, prof = H - hor;
  const ap = suave((t - 0.15) / 1.1);
  ctx.save();
  ctx.lineWidth = 1.4;
  for (let i = 1; i <= 16; i++) {                    // líneas que se alejan
    const k = i / 16;
    const y = hor + prof * Math.pow(k, 2.1) + ((t * 26) % (prof / 16));
    if (y > H + 2) continue;
    const a = 0.30 * Math.pow((y - hor) / prof, 0.75) * ap;
    ctx.strokeStyle = `rgba(80,190,225,${a.toFixed(3)})`;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }
  for (let i = -13; i <= 13; i++) {                  // líneas que convergen
    const x = W / 2 + i * W * 0.085;
    ctx.strokeStyle = `rgba(80,190,225,${(0.16 * ap).toFixed(3)})`;
    ctx.beginPath(); ctx.moveTo(W / 2 + i * W * 0.012, hor); ctx.lineTo(x * 1.9 - W * 0.45, H); ctx.stroke();
  }
  const hz = ctx.createLinearGradient(0, hor - 60, 0, hor + 40);
  hz.addColorStop(0, "rgba(0,0,0,0)"); hz.addColorStop(1, `rgba(90,200,235,${(0.10 * ap).toFixed(3)})`);
  ctx.fillStyle = hz; ctx.fillRect(0, hor - 60, W, 100);
  ctx.restore();
}

// ------------------------------------------------------------------ montaje
function svgDe(ins) {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", ins.caja || "0 0 24 24");
  s.innerHTML = ins.trazos.map(d => `<path d="${d}"/>`).join("");
  return s;
}

async function preparar(base) {
  D = await (await fetch(base + "/datos.json")).json();
  W = D.W; H = D.H;
  const esc = document.getElementById("esc");
  esc.style.width = W + "px"; esc.style.height = H + "px";
  const cv = document.getElementById("fondo");
  cv.width = W; cv.height = H; ctx = cv.getContext("2d");

  const r = azar(21);
  estrellas = Array.from({ length: 220 }, () => ({
    x: r() * W, y: r() * H * 0.72, r: r() < 0.82 ? 1 : 2,
    a: 0.18 + r() * 0.55, v: 0.6 + r() * 2.4, f: r() * 6.28,
  }));

  // logo redondo de la esquina
  const lg = document.getElementById("logo");
  const d = Math.round(H * 0.075);
  Object.assign(lg.style, { left: `${H * 0.038}px`, top: `${H * 0.038}px`, width: `${d}px`, height: `${d}px` });
  if (D.logo) { lg.appendChild(svgDe({ trazos: D.logo.trazos, caja: D.logo.caja })); lg.querySelectorAll("path").forEach(p => { p.style.fill = "none"; p.style.stroke = "currentColor"; p.style.strokeWidth = "2"; }); }

  // texto
  const ti = document.getElementById("titulo");
  ti.textContent = D.titulo;
  Object.assign(ti.style, {
    top: `${H * 0.15}px`, letterSpacing: `${Math.round(H * 0.006)}px`,
    whiteSpace: "nowrap",
  });
  // el título siempre en una línea: se encoge hasta caber
  let tam = Math.round(H * 0.105);
  await document.fonts.load(`900 ${tam}px "Display"`);
  const med = document.createElement("span");
  med.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font-family:Display;`
    + `font-weight:900;letter-spacing:${Math.round(H * 0.006)}px;`;
  med.textContent = D.titulo;
  document.body.appendChild(med);
  med.style.fontSize = tam + "px";
  while (tam > 28 && med.offsetWidth > W * 0.86) { tam -= 2; med.style.fontSize = tam + "px"; }
  med.remove();
  ti.style.fontSize = tam + "px";
  const pi = document.getElementById("pildora");
  pi.textContent = D.pildora;
  Object.assign(pi.style, {
    top: `${H * 0.288}px`, height: `${Math.round(H * 0.058)}px`,
    padding: `0 ${Math.round(H * 0.028)}px`, fontSize: `${Math.round(H * 0.027)}px`,
    letterSpacing: "1px",
  });
  const su = document.getElementById("sub");
  su.textContent = D.subtitulo;
  Object.assign(su.style, {
    top: `${H * 0.372}px`, fontSize: `${Math.round(H * 0.026)}px`,
    letterSpacing: `${Math.round(H * 0.009)}px`,
  });

  if (D.tipo === "cierre") {                       // portada y cierre comparten piezas
    const d2 = Math.round(H * 0.26);
    Object.assign(lg.style, {
      left: `${Math.round(W / 2 - d2 / 2)}px`, top: `${Math.round(H * 0.20)}px`,
      width: `${d2}px`, height: `${d2}px`, background: "transparent",
      border: `${Math.max(2, H * 0.003).toFixed(1)}px solid #4fd3ef`,
    });
    Object.assign(ti.style, { top: `${H * 0.545}px` });
    Object.assign(pi.style, { top: `${H * 0.70}px` });
    document.getElementById("sub").style.display = "none";
    await document.fonts.ready;
    marcas = [];
    return { duracion: D.duracion, W, H };
  }

  // insignias
  const capa = document.getElementById("capa");
  const n = D.insignias.length;
  const dia = Math.round(H * 0.145);
  const paso = Math.min(W / (n + 0.6), dia * 1.62);
  const x0 = W / 2 - (paso * (n - 1)) / 2;
  const y = H * 0.505;
  marcas = D.insignias.map((ins, i) => {
    const el = document.createElement("div");
    el.className = "marca";
    Object.assign(el.style, {
      left: `${Math.round(x0 + paso * i - dia / 2)}px`, top: `${Math.round(y)}px`,
      width: `${dia}px`, height: `${dia}px`, color: ins.color,
    });
    el.appendChild(svgDe(ins));
    const lb = document.createElement("div");
    lb.className = "etq"; lb.textContent = ins.etiqueta;
    Object.assign(lb.style, {
      left: `${Math.round(x0 + paso * i - paso / 2)}px`, top: `${Math.round(y + dia + H * 0.022)}px`,
      width: `${Math.round(paso)}px`, fontSize: `${Math.round(H * 0.0245)}px`,
      letterSpacing: `${Math.round(H * 0.002)}px`, color: ins.color,
    });
    capa.appendChild(el); capa.appendChild(lb);
    return { el, lb, color: ins.color, t: D.insignia_desde + i * D.insignia_paso };
  });

  await document.fonts.ready;
  return { duracion: D.duracion, W, H };
}

// ------------------------------------------------------------------ fotograma
function frame(t) {
  fondo(t);

  const sube = (el, k, dy, extra = "") => {
    el.style.opacity = k.toFixed(3);
    el.style.transform = `translateY(${(dy * (1 - k)).toFixed(2)}px) ${extra}`;
  };

  const kT = suave((t - D.titulo_desde) / 0.75);
  const ti = document.getElementById("titulo");
  sube(ti, kT, 34);
  ti.style.filter = `blur(${((1 - kT) * 9).toFixed(2)}px)`;
  ti.style.textShadow = `0 0 ${(26 * kT).toFixed(0)}px rgba(120,190,240,${(0.33 * kT).toFixed(2)})`;

  const kP = suave((t - D.titulo_desde - 0.5) / 0.6);
  const pi = document.getElementById("pildora");
  pi.style.opacity = sat((t - D.titulo_desde - 0.62) / 0.35).toFixed(3);
  pi.style.transform = `translateX(-50%) scaleX(${(0.12 + 0.88 * salida(kP)).toFixed(3)})`;
  pi.style.boxShadow = `0 0 ${(22 * kP).toFixed(0)}px rgba(95,216,240,${(0.30 * kP).toFixed(2)}), inset 0 0 ${(16 * kP).toFixed(0)}px rgba(95,216,240,0.10)`;

  sube(document.getElementById("sub"), suave((t - D.titulo_desde - 0.95) / 0.6), 18);

  const lg = document.getElementById("logo");
  const kL = suave((t - 0.25) / 0.6);
  lg.style.opacity = kL.toFixed(3);
  if (D.tipo === "cierre") {
    const lat = 1 + 0.028 * Math.sin(t * 2.0);
    lg.style.transform = `scale(${(0.72 + 0.28 * rebote(kL)) * lat})`;
    lg.style.boxShadow = `0 0 ${(44 * kL).toFixed(0)}px rgba(79,211,239,0.45), inset 0 0 ${(34 * kL).toFixed(0)}px rgba(79,211,239,0.18)`;
  } else {
    lg.style.transform = `scale(${(0.6 + 0.4 * rebote(kL)).toFixed(3)})`;
  }

  for (const m of marcas) {
    const k = sat((t - m.t) / 0.52);
    const e = rebote(k);
    const pulso = Math.exp(-Math.max(0, t - m.t - 0.5) / 0.3);
    const brillo = 14 + 26 * pulso;
    m.el.style.opacity = suave(k * 1.6).toFixed(3);
    m.el.style.transform = `scale(${(0.55 + 0.45 * e).toFixed(3)})`;
    m.el.style.border = `${Math.max(1, H * 0.0026).toFixed(1)}px solid ${m.color}`;
    m.el.style.boxShadow = k > 0
      ? `0 0 ${brillo.toFixed(0)}px ${m.color}66, inset 0 0 ${(brillo * 0.8).toFixed(0)}px ${m.color}33`
      : "none";
    m.el.style.background = `radial-gradient(circle at 50% 45%, ${m.color}1f, rgba(6,12,22,0.86) 70%)`;
    const kl = sat((t - m.t - 0.18) / 0.45);
    m.lb.style.opacity = kl.toFixed(3);
    m.lb.style.transform = `translateY(${((1 - suave(kl)) * 12).toFixed(2)}px)`;
    m.lb.style.textShadow = `0 0 ${(12 * kl).toFixed(0)}px ${m.color}55`;
  }

  // deriva lenta del conjunto: el plano respira
  const z = 1 + 0.012 * Math.sin(t * 0.33);
  document.getElementById("capa").style.transform = `scale(${z.toFixed(4)})`;
  ultimo = t;
}

window.preparar = preparar;
window.frame = frame;
