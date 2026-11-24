/* Render del motor WebGL a MP4.
   uso: node render.js CARPETA_GPU [--salida v.mp4] [--voz ruta.wav]
        [--muestras 1.5,4,9.8] [--desde 0] [--hasta 6] [--formato png|jpeg] */
const fs = require("fs"), path = require("path"), http = require("http");
const { spawn } = require("child_process");
const puppeteer = require("puppeteer-core");

const args = process.argv.slice(2);
const dir = path.resolve(args[0]);
const opt = (n, d) => { const i = args.indexOf("--" + n); return i < 0 ? d : args[i + 1]; };
const salida = path.resolve(opt("salida", path.join(dir, "video.mp4")));
const voz = opt("voz", null);
const muestras = opt("muestras", null);
const desde = parseFloat(opt("desde", "0"));
const hastaOpt = opt("hasta", null);
const formato = opt("formato", "png");
const webDir = path.resolve(opt("web", path.join(__dirname, "web")));
const FPS = 30;

const MIME = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json",
               ".bin": "application/octet-stream", ".woff": "font/woff", ".css": "text/css",
               ".svg": "image/svg+xml", ".png": "image/png" };

(async () => {
  for (const f of fs.readdirSync(webDir)) {
    const o = path.join(webDir, f);
    if (fs.statSync(o).isFile()) fs.copyFileSync(o, path.join(dir, f));
  }
  const meta = JSON.parse(fs.readFileSync(path.join(dir, "datos.json"), "utf8"));
  const ANCHO = meta.W || 1080, ALTO = meta.H || 1920;

  const srv = http.createServer((req, res) => {
    const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]) === "/" ? "index.html" : decodeURIComponent(req.url.split("?")[0]));
    if (!p.startsWith(dir) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(p)] || "application/octet-stream" });
    fs.createReadStream(p).pipe(res);
  }).listen(0);
  const port = srv.address().port;

  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/google-chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle", "--use-angle=swiftshader",
           "--enable-unsafe-swiftshader", "--hide-scrollbars", "--force-device-scale-factor=1"],
  });
  const page = await browser.newPage();
  page.on("pageerror", e => console.error("PAGINA:", e.message));
  await page.setViewport({ width: ANCHO, height: ALTO, deviceScaleFactor: 1 });
  await page.goto(`http://localhost:${port}/index.html`, { waitUntil: "load" });
  const info = await page.evaluate(() => window.preparar("."));
  console.log(`${info.N} partículas · ${info.escenas} escenas · ${info.duracion.toFixed(1)} s`);

  const captura = () => page.screenshot(formato === "png"
    ? { type: "png", optimizeForSpeed: true }
    : { type: "jpeg", quality: 95 });

  // ---- muestras sueltas para revisar antes del render completo
  if (muestras) {
    const ts = muestras.split(",").map(Number);
    const out = [];
    for (const t of ts) {
      for (let w = Math.max(0, t - 0.5); w < t; w += 1 / FPS) await page.evaluate(x => window.frame(x), w);
      await page.evaluate(x => window.frame(x), t);
      const f = path.join(dir, `m_${t}.png`);
      fs.writeFileSync(f, await page.screenshot({ type: "png" }));
      out.push(f); console.log(f);
    }
    await browser.close(); srv.close(); return;
  }

  // ---- render completo
  const hasta = hastaOpt != null ? parseFloat(hastaOpt) : info.duracion;
  const n0 = Math.round(desde * FPS), n1 = Math.round(hasta * FPS);
  const tmp = salida.replace(/\.mp4$/, "") + ".parcial.mp4";
  const ff = ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-"];
  if (voz) ff.push("-ss", String(desde), "-i", path.resolve(voz), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest");
  ff.push("-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", tmp);
  const enc = spawn("ffmpeg", ff, { stdio: ["pipe", "inherit", "inherit"] });

  const t0 = Date.now();
  for (let i = n0; i < n1; i++) {
    await page.evaluate(x => window.frame(x), i / FPS);
    const img = await captura();
    if (!enc.stdin.write(img)) await new Promise(r => enc.stdin.once("drain", r));
    if ((i - n0) % 30 === 0) {
      const hechos = i - n0 + 1, falta = (n1 - i - 1) * (Date.now() - t0) / hechos / 1000;
      process.stdout.write(`\r  ${hechos}/${n1 - n0} fotogramas · faltan ${falta.toFixed(0)} s   `);
    }
  }
  enc.stdin.end();
  await new Promise(r => enc.on("close", r));
  fs.renameSync(tmp, salida);
  console.log(`\n${salida}  (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  await browser.close(); srv.close();
})();
