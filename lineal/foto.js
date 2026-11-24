/* Captura páginas HTML sueltas a PNG, al tamaño que diga cada una.
   uso: node foto.js escena_a.html escena_b.html ...                */
const fs = require("fs"), path = require("path"), http = require("http");
const puppeteer = require(path.join(__dirname, "..", "gpu", "node_modules", "puppeteer-core"));

const archivos = process.argv.slice(2).map(f => path.resolve(f));
const dir = path.dirname(archivos[0]);
const MIME = { ".html": "text/html", ".css": "text/css", ".woff": "font/woff",
               ".svg": "image/svg+xml", ".js": "text/javascript", ".png": "image/png" };

(async () => {
  const srv = http.createServer((req, res) => {
    const p = path.join(dir, decodeURIComponent(req.url.split("?")[0]));
    if (!p.startsWith(dir) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(p)] || "application/octet-stream" });
    fs.createReadStream(p).pipe(res);
  }).listen(0);
  const port = srv.address().port;

  const browser = await puppeteer.launch({
    executablePath: "/usr/bin/google-chrome", headless: "new",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
           "--force-device-scale-factor=1", "--font-render-hinting=none"],
  });
  const page = await browser.newPage();
  page.on("pageerror", e => console.error("PAGINA:", e.message));

  for (const f of archivos) {
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
    await page.goto(`http://localhost:${port}/${path.basename(f)}`, { waitUntil: "networkidle0" });
    await page.evaluate(() => document.fonts.ready);
    const caja = await page.evaluate(() => {
      const e = document.getElementById("esc");
      const r = e.getBoundingClientRect();
      return { width: Math.round(r.width), height: Math.round(r.height) };
    });
    await page.setViewport({ ...caja, deviceScaleFactor: 1 });
    const salida = f.replace(/\.html$/, ".png");
    fs.writeFileSync(salida, await page.screenshot({ type: "png" }));
    console.log(salida, caja.width + "x" + caja.height);
  }
  await browser.close(); srv.close();
})();
