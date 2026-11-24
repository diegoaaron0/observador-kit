/* Motor de partículas en WebGL2.
   Python entrega una nube de puntos por escena; aquí ocurre el movimiento:
   viaje escalonado y curvo entre formas, profundidad, ruido en reposo,
   estela por velocidad, bloom y onda en las palabras clave.            */

const VS_PUNTOS = `#version 300 es
precision highp float;
in vec2 aFrom, aTo;
in vec3 aColFrom, aColTo;
in float aAlfFrom, aAlfTo, aZ;
in vec4 aSeed;            // x retardo · y curvatura · z clase · w fase
in vec4 aOsc;             // amplitud x · amplitud y · velocidad · fase
in vec2 aNrm;             // normal del contorno
uniform float uMix, uT, uScale, uBurst, uLocal;
uniform vec3 uVida, uLatido;
uniform vec2 uRes, uCentro;
out vec3 vCol;
out float vAlf;

float backOut(float x){ float c1=1.22, c3=c1+1.0; float p=x-1.0; return 1.0+c3*p*p*p+c1*p*p; }

void main(){
  float SPREAD = 0.42;                                   // 1. salida escalonada
  float m = clamp((uMix - aSeed.x*SPREAD) / (1.0-SPREAD), 0.0, 1.0);
  float e = backOut(m);                                  //    con rebote al llegar
  vec2 p = mix(aFrom, aTo, e);

  vec2 d = aTo - aFrom;                                  // 2. trayectoria en arco
  float L = length(d);
  if (L > 2.0) {
    vec2 perp = vec2(-d.y, d.x) / L;
    p += perp * aSeed.y * min(L*0.30, 190.0) * sin(3.14159*m);
  }

  float ph = aSeed.w * 6.2831;                           // 3. vida en reposo
  float viva = mix(1.0, 3.2, 1.0 - abs(2.0*m - 1.0));
  p += vec2(sin(p.y*0.0135 + uT*0.75 + ph),
            cos(p.x*0.0117 - uT*0.62 + ph)) * 4.2 * viva;

  float rad = (aSeed.z*aSeed.z) * 7.0;                   //    el trazo es un banco
  p += vec2(cos(ph*3.1), sin(ph*3.1)) * rad;             //    de puntos, no una línea

  if (aOsc.z > 0.0)                                      // 3b. partes que oscilan
    p += aOsc.xy * sin(6.2831*aOsc.z*uLocal + aOsc.w);   //     (el iris de un ojo)

  p += aNrm * uVida.x *                                  // 3c. onda que recorre el
       sin(float(gl_VertexID)*uVida.y - uT*uVida.z);     //     trazo: nunca se congela

  if (uLatido.x > 0.0)                                   // 3d. latido
    p = (p - uCentro) * (1.0 + uLatido.x*sin(6.2831*uLatido.y*uLocal)) + uCentro;

  if (uBurst > 0.001) {                                  // 4. onda en palabra clave
    vec2 r = p - uCentro; float rl = max(length(r), 1.0);
    p += (r/rl) * uBurst * 90.0 * exp(-rl/620.0);
  }

  float ang = 0.085 * sin(uT*0.21);                      // 5. profundidad y paralaje
  float zz = aZ * 210.0;
  float dx = p.x - uCentro.x;
  p.x = uCentro.x + dx*cos(ang) + zz*sin(ang);
  float cerca = aZ*0.5 + 0.5;

  p = (p - uCentro) * uScale + uCentro;

  float clase = aSeed.z;                                 // 6. tamaños y brillos mezclados
  float size = clase < 0.62 ? 1.5 : (clase < 0.95 ? 2.4 : 4.6);
  float br   = clase < 0.62 ? 0.50 : (clase < 0.95 ? 0.95 : 2.4);
  size *= (0.78 + 0.42*cerca) * clamp(uScale, 0.8, 3.0);
  br   *= (0.52 + 0.48*cerca);
  float tw = 0.58 + 0.42*sin(uT*(1.5 + aSeed.w*3.0) + ph);

  vCol = mix(aColFrom, aColTo, e) * (br*tw/255.0);
  vAlf = mix(aAlfFrom, aAlfTo, e);
  gl_PointSize = size;
  vec2 cl = (p/uRes)*2.0 - 1.0;
  gl_Position = vec4(cl.x, -cl.y, 0.0, 1.0);
}`;

const FS_PUNTOS = `#version 300 es
precision highp float;
in vec3 vCol; in float vAlf; out vec4 o;
void main(){
  vec2 q = gl_PointCoord - 0.5;
  float f = exp(-dot(q,q)*15.0);
  o = vec4(vCol*vAlf*f, 1.0);
}`;

const VS_QUAD = `#version 300 es
precision highp float;
in vec2 aP; out vec2 vUV;
void main(){ vUV = aP*0.5+0.5; gl_Position = vec4(aP,0.0,1.0); }`;

const FS_ESTELA = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uEscena, uPrevio; uniform float uK;
void main(){
  vec3 n = texture(uEscena, vUV).rgb;
  vec3 p = texture(uPrevio, vUV).rgb;
  o = vec4(max(n, n*(1.0-uK) + p*uK), 1.0);   // lo que se mueve deja rastro
}`;

const FS_BORRON = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uTex; uniform vec2 uPaso;
void main(){
  vec3 s = texture(uTex, vUV).rgb*0.2270;
  s += (texture(uTex, vUV+uPaso*1.3846).rgb + texture(uTex, vUV-uPaso*1.3846).rgb)*0.3162;
  s += (texture(uTex, vUV+uPaso*3.2307).rgb + texture(uTex, vUV-uPaso*3.2307).rgb)*0.0702;
  o = vec4(s,1.0);
}`;

const FS_FINAL = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uNitido, uBrilloA, uBrilloB;
uniform vec2 uRes, uCentro; uniform vec3 uAmb;
void main(){
  vec3 c = texture(uNitido, vUV).rgb*1.85
         + texture(uBrilloA, vUV).rgb*1.05
         + texture(uBrilloB, vUV).rgb*1.45;
  vec2 q = (vUV*uRes - uCentro) / vec2(700.0, 900.0);
  float r = length(q);
  float vign = clamp(1.15 - r*0.75, 0.25, 1.0);
  vec3 fondo = vec3(4.0, 6.0, 14.0)/255.0 + uAmb*0.22*exp(-r*r*2.5);
  vec3 img = fondo + c;
  o = vec4(1.0 - exp(-img*vign*1.35), 1.0);
}`;

// ----------------------------------------------------------------- utilidades GL
let gl, D = null, prog = {}, buf = {}, rt = {}, vaoPuntos, vaoQuad, ui, ctx;
let posAll, colAll, alfAll, nrmAll, oscAll, inicioPos, escActual = -1, ultimoT = -1;

function compilar(vs, fs) {
  const p = gl.createProgram();
  for (const [tipo, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
    const s = gl.createShader(tipo);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    gl.attachShader(p, s);
  }
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  return p;
}

function destino(w, h) {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
  for (const p of [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER]) gl.texParameteri(gl.TEXTURE_2D, p, gl.LINEAR);
  for (const p of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T]) gl.texParameteri(gl.TEXTURE_2D, p, gl.CLAMP_TO_EDGE);
  const f = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, f);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
  return { t, f, w, h };
}

function atributo(p, nombre, datos, comps, tipo = gl.FLOAT, norm = false) {
  const b = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.bufferData(gl.ARRAY_BUFFER, datos, gl.DYNAMIC_DRAW);
  const l = gl.getAttribLocation(p, nombre);
  if (l >= 0) { gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, comps, tipo, norm, 0, 0); }
  return b;
}

// ----------------------------------------------------------------- carga
async function preparar(base) {
  D = await (await fetch(base + "/datos.json")).json();
  const N = D.N, nEsc = D.escenas.length;
  posAll = new Float32Array(await (await fetch(base + "/pos.bin")).arrayBuffer());
  colAll = new Uint8Array(await (await fetch(base + "/col.bin")).arrayBuffer());
  alfAll = new Uint8Array(await (await fetch(base + "/alf.bin")).arrayBuffer());
  nrmAll = new Float32Array(await (await fetch(base + "/nrm.bin")).arrayBuffer());
  oscAll = new Float32Array(await (await fetch(base + "/osc.bin")).arrayBuffer());

  const cv = document.getElementById("gl");
  gl = cv.getContext("webgl2", { antialias: false, preserveDrawingBuffer: true, alpha: false });
  if (!gl.getExtension("EXT_color_buffer_float")) throw new Error("sin texturas float");
  ui = document.getElementById("ui"); ctx = ui.getContext("2d");

  prog.puntos = compilar(VS_PUNTOS, FS_PUNTOS);
  prog.estela = compilar(VS_QUAD, FS_ESTELA);
  prog.borron = compilar(VS_QUAD, FS_BORRON);
  prog.final = compilar(VS_QUAD, FS_FINAL);

  // semillas deterministas por partícula
  const rnd = (s => () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296)(7);
  const seed = new Float32Array(N * 4), z = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    seed[i * 4] = rnd();                        // retardo
    seed[i * 4 + 1] = (rnd() * 2 - 1) * 0.9;    // curvatura con signo
    seed[i * 4 + 2] = rnd();                    // clase de tamaño
    seed[i * 4 + 3] = rnd();                    // fase
    z[i] = rnd() * 2 - 1;
  }
  // estado inicial: la primera forma, dispersa (el primer fotograma ya engancha)
  inicioPos = new Float32Array(N * 2);
  const disp = D.inicio_dispersion || 70;
  for (let i = 0; i < N * 2; i++) {
    const u = Math.max(1e-6, rnd()), v = rnd();
    inicioPos[i] = posAll[i] + Math.sqrt(-2 * Math.log(u)) * Math.cos(6.2831 * v) * disp;
  }

  vaoPuntos = gl.createVertexArray(); gl.bindVertexArray(vaoPuntos);
  buf.from = atributo(prog.puntos, "aFrom", inicioPos, 2);
  buf.to = atributo(prog.puntos, "aTo", posAll.subarray(0, N * 2), 2);
  buf.colFrom = atributo(prog.puntos, "aColFrom", colAll.slice(0, N * 3), 3, gl.UNSIGNED_BYTE);
  buf.colTo = atributo(prog.puntos, "aColTo", colAll.slice(0, N * 3), 3, gl.UNSIGNED_BYTE);
  buf.alfFrom = atributo(prog.puntos, "aAlfFrom", alfAll.slice(0, N), 1, gl.UNSIGNED_BYTE, true);
  buf.alfTo = atributo(prog.puntos, "aAlfTo", alfAll.slice(0, N), 1, gl.UNSIGNED_BYTE, true);
  atributo(prog.puntos, "aSeed", seed, 4);
  atributo(prog.puntos, "aZ", z, 1);
  buf.nrm = atributo(prog.puntos, "aNrm", nrmAll.subarray(0, N * 2), 2);
  buf.osc = atributo(prog.puntos, "aOsc", oscAll.subarray(0, N * 4), 4);
  gl.bindVertexArray(null);

  vaoQuad = gl.createVertexArray(); gl.bindVertexArray(vaoQuad);
  atributo(prog.borron, "aP", new Float32Array([-1, -1, 3, -1, -1, 3]), 2);
  gl.bindVertexArray(null);

  const W = D.W, H = D.H;
  rt.escena = destino(W, H);
  rt.estelaA = destino(W, H); rt.estelaB = destino(W, H);
  rt.q1 = destino(W >> 2, H >> 2); rt.q2 = destino(W >> 2, H >> 2);
  rt.q3 = destino(W >> 4, H >> 4); rt.q4 = destino(W >> 4, H >> 4);
  for (const k of ["estelaA", "estelaB"]) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, rt[k].f);
    gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
  }
  await document.fonts.load('60px "Mont"');
  await document.fonts.load('78px "Playfair"');
  await document.fonts.load('34px "Mont"');
  await document.fonts.ready;
  return { N, escenas: nEsc, duracion: D.duracion };
}

// ----------------------------------------------------------------- escenas
function subirEscena(ki) {
  const N = D.N;
  const sub = (a, i, k) => a.subarray(i * N * k, (i + 1) * N * k);
  const prevPos = ki === 0 ? inicioPos : sub(posAll, ki - 1, 2);
  const prevCol = sub(colAll, Math.max(0, ki - 1), 3);
  const prevAlf = sub(alfAll, Math.max(0, ki - 1), 1);
  gl.bindVertexArray(vaoPuntos);
  const sube = (b, d) => { gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferSubData(gl.ARRAY_BUFFER, 0, d); };
  sube(buf.from, prevPos); sube(buf.to, sub(posAll, ki, 2));
  sube(buf.colFrom, prevCol); sube(buf.colTo, sub(colAll, ki, 3));
  sube(buf.nrm, sub(nrmAll, ki, 2)); sube(buf.osc, sub(oscAll, ki, 4));
  sube(buf.alfFrom, ki === 0 ? prevAlf.map(v => v * 0.7) : prevAlf); sube(buf.alfTo, sub(alfAll, ki, 1));
  gl.bindVertexArray(null);
  escActual = ki;
}

function escalaY(t) {
  let s = 1 + 0.018 * Math.sin(t * 0.6), burst = 0;
  for (const tw of D.claves) {
    const dt = t - tw;
    if (dt >= 0 && dt < 1.2) s += D.impulso * Math.exp(-dt / 0.2);
    if (dt >= 0 && dt < 0.45) burst = Math.max(burst, Math.exp(-dt / 0.13));
  }
  if (D.t_final != null && t > D.t_final) s *= Math.exp((t - D.t_final) * (D.final.velocidad || 1.35));
  return [s, burst];
}

// ----------------------------------------------------------------- dibujo
function quad(p, uniformes) {
  gl.useProgram(p); gl.bindVertexArray(vaoQuad);
  let u = 0;
  for (const [k, v] of Object.entries(uniformes)) {
    const l = gl.getUniformLocation(p, k);
    if (l === null) continue;
    if (v && v.t !== undefined) { gl.activeTexture(gl.TEXTURE0 + u); gl.bindTexture(gl.TEXTURE_2D, v.t); gl.uniform1i(l, u); u++; }
    else if (Array.isArray(v)) (v.length === 2 ? gl.uniform2fv : gl.uniform3fv).call(gl, l, v);
    else gl.uniform1f(l, v);
  }
  gl.drawArrays(gl.TRIANGLES, 0, 3);
}

function aDestino(d) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, d.f);
  gl.viewport(0, 0, d.w, d.h);
}

function frame(t) {
  const W = D.W, H = D.H, CX = W / 2, CY = 860;
  // escena vigente y avance del morph
  let ki = 0;
  while (ki + 1 < D.escenas.length && D.escenas[ki + 1].t <= t) ki++;
  if (ki !== escActual) subirEscena(ki);
  const t0 = D.escenas[ki].t;
  const sig = ki + 1 < D.escenas.length ? D.escenas[ki + 1].t : D.duracion;
  const trans = Math.min(0.80, Math.max(0.25, (sig - t0) * 0.85)) / (D.escenas[ki].rigidez || 1);
  const mix = Math.min(1, Math.max(0, (t - t0) / trans));
  const [esc, burst] = escalaY(t);

  // 1 · partículas, aditivo
  aDestino(rt.escena);
  gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
  gl.useProgram(prog.puntos); gl.bindVertexArray(vaoPuntos);
  const U = k => gl.getUniformLocation(prog.puntos, k);
  gl.uniform1f(U("uMix"), mix); gl.uniform1f(U("uT"), t);
  gl.uniform1f(U("uScale"), esc); gl.uniform1f(U("uBurst"), burst);
  gl.uniform2f(U("uRes"), W, H); gl.uniform2f(U("uCentro"), CX, CY);
  gl.uniform1f(U("uLocal"), t - t0);
  const vida = D.escenas[ki].vida == null ? 1 : D.escenas[ki].vida;
  gl.uniform3f(U("uVida"), 3.4 * vida, 6.2831 * 7 / D.N, 2.2);
  const lat = D.escenas[ki].latido || [0, 0];
  gl.uniform3f(U("uLatido"), lat[0], lat[1], 0);
  gl.drawArrays(gl.POINTS, 0, D.N);
  gl.disable(gl.BLEND);

  // 2 · estela (lo que viaja rápido deja rastro largo)
  const k = (t <= ultimoT || ultimoT < 0) ? 0 : D.estela;
  aDestino(rt.estelaB);
  quad(prog.estela, { uEscena: rt.escena, uPrevio: rt.estelaA, uK: k });
  const tmp = rt.estelaA; rt.estelaA = rt.estelaB; rt.estelaB = tmp;
  ultimoT = t;

  // 3 · brillo en dos escalas
  aDestino(rt.q1); quad(prog.borron, { uTex: rt.estelaA, uPaso: [1 / rt.q1.w, 0] });
  aDestino(rt.q2); quad(prog.borron, { uTex: rt.q1, uPaso: [0, 1 / rt.q1.h] });
  aDestino(rt.q3); quad(prog.borron, { uTex: rt.q2, uPaso: [1 / rt.q3.w, 0] });
  aDestino(rt.q4); quad(prog.borron, { uTex: rt.q3, uPaso: [0, 1 / rt.q3.h] });

  // 4 · composición
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.viewport(0, 0, W, H);
  quad(prog.final, {
    uNitido: rt.estelaA, uBrilloA: rt.q2, uBrilloB: rt.q4,
    uRes: [W, H], uCentro: [CX, CY], uAmb: ambiente(ki),
  });
  gl.finish();

  dibujarUI(t, ki);
}

function ambiente(ki) {
  const N = D.N, c = [0, 0, 0];
  for (let i = 0; i < N; i += 29) {
    const a = alfAll[ki * N + i] / 255;
    for (let j = 0; j < 3; j++) c[j] += colAll[(ki * N + i) * 3 + j] / 255 * a;
  }
  const n = Math.ceil(N / 29);
  return c.map(v => v / n);
}

// ----------------------------------------------------------------- texto
const suave = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };

function dibujarUI(t, ki) {
  ctx.clearRect(0, 0, D.W, D.H);
  const rot = D.escenas[ki].rotulo;
  if (rot) {
    const sig = ki + 1 < D.escenas.length ? D.escenas[ki + 1].t : D.duracion;
    const lt = t - D.escenas[ki].t, total = sig - D.escenas[ki].t;
    const a = suave(lt / 0.35) * (1 - suave((lt - (total - 0.3)) / 0.3));
    if (a > 0) {
      ctx.save(); ctx.globalAlpha = a * 0.8; ctx.font = '34px "Mont"';
      ctx.fillStyle = "rgb(200,210,225)"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(rot, D.W / 2, 330); ctx.restore();
    }
  }
  if (!D.subtitulos.mostrar) return;
  const S = D.subtitulos, fn = `600 ${S.tamano}px "Mont"`, fk = `italic 700 ${Math.round(S.tamano * 1.3)}px "Playfair"`;
  for (let i = 0; i < D.frases.length; i++) {
    const f = D.frases[i];
    const sig = i + 1 < D.frases.length ? D.frases[i + 1].inicio : D.duracion;
    const fin = Math.min(f.fin + 0.55, sig - 0.32);
    if (!(f.inicio - 0.05 <= t && t < fin + 0.25)) continue;
    const fo = 1 - suave((t - fin) / 0.25);
    const items = f.palabras.map(w => {
      ctx.font = w.clave ? fk : fn;
      return { ...w, f: w.clave ? fk : fn, w: ctx.measureText(w.texto).width, sp: ctx.measureText(" ").width };
    });
    const lineas = []; let cur = [], cw = 0;
    for (const it of items) {
      if (cur.length && cw + it.sp + it.w > 900) { lineas.push(cur); cur = []; cw = 0; }
      cw += (cur.length ? it.sp : 0) + it.w; cur.push(it);
    }
    lineas.push(cur);
    const y0 = S.y - (lineas.length - 1) * 48;
    for (let li = 0; li < lineas.length; li++) {
      const ln = lineas[li];
      const lw = ln.reduce((s, x) => s + x.w, 0) + ln.slice(1).reduce((s, x) => s + x.sp, 0);
      let x = (D.W - lw) / 2; const y = y0 + li * 96;
      for (let k = 0; k < ln.length; k++) {
        const it = ln[k]; if (k) x += it.sp;
        const p = suave((t - it.t + 0.04) / 0.18);
        if (p > 0) {
          ctx.save();
          ctx.font = it.f; ctx.textBaseline = "alphabetic";
          ctx.globalAlpha = p * fo;
          ctx.shadowColor = "rgba(0,0,0,0.95)"; ctx.shadowBlur = 24;
          ctx.fillStyle = it.clave ? `rgb(${S.color_clave.join(",")})` : "rgb(240,244,250)";
          const dy = (1 - p) * 14;
          ctx.fillText(it.texto, x, y + dy);
          ctx.shadowBlur = 10; ctx.fillText(it.texto, x, y + dy);
          ctx.restore();
        }
        x += it.w;
      }
    }
  }
}

window.preparar = preparar;
window.frame = frame;
