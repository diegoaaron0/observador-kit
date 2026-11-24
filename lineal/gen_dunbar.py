"""Genera dunbar.html (estilo Lineal) a partir de funciones pequeñas."""
import math, random, os

random.seed(7)
W, H = 1080, 1920
out = []


def a(s): out.append(s)


def fig(x, y, s=1.0, ll=False, op=None):
    st = f' style="opacity:{op}"' if op is not None else ""
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f})"><use href="#{"perll" if ll else "per"}"{st}/></g>'


def pill(x, y, txt, lleno=True, w=None, h=66):
    w = w or int(22.5 * len(txt) + 64)
    x0, y0 = x - w / 2, y - h / 2
    if lleno:
        return (f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="{h//2}" fill="#fff"/>'
                f'<text class="etq neg" x="{x}" y="{y+10}" text-anchor="middle">{txt}</text>')
    return (f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="{h//2}" fill="#000" stroke="#fff" stroke-width="5"/>'
            f'<text class="etq" x="{x}" y="{y+10}" text-anchor="middle">{txt}</text>')


def an(inner, en, anim="entra", dur=0.4, extra=""):
    return f'<g data-en="{en}" data-anim="{anim}" data-dur="{dur}" {extra}>{inner}</g>'


def escena(en, cuerpo):
    a(f'<g data-escena="{en}">')
    a('<g transform="translate(0,60)"><g filter="url(#halo)">')
    a(cuerpo)
    a('</g></g></g>')


# ═══════════════════════════════════════════════════════════════ 1 · mil quinientas
def escena_multitud():
    c = []
    filas = [(760, .20), (830, .26), (910, .32), (1000, .38), (1110, .44), (1240, .50), (1390, .56)]
    for r, (yb, s) in enumerate(filas):
        paso = 130 * s + 10
        x = -160 - (r * 0.37 * paso) % paso
        figs = []
        while x < 1300:
            figs.append(fig(x, yb - 40 * s, s, ll=True))
            x += paso
        c.append(f'<g data-en="inicio" data-anim="pan" data-dir="-1,0" data-amp="{10 + 7 * r}" opacity="{0.5 + 0.08 * r:.2f}">' + "".join(figs) + '</g>')
    c.append(an('<text class="cifra" x="540" y="470" text-anchor="middle" font-size="230">1.500</text>'
                '<text class="mini" x="540" y="548" text-anchor="middle">NOMBRES QUE CONOCES</text>', "mil-0.1", "crece", 0.9))
    escena("inicio", "".join(c))


# ═══════════════════════════════════════════════════════════════ 2 · ciento cincuenta
def escena_150():
    c = [an('<text class="mini" x="540" y="500" text-anchor="middle">LO QUE TU CEREBRO SOSTIENE</text>', "cerebro", "sube", 0.4)]
    c.append(an('<text class="cifra" x="540" y="760" text-anchor="middle" font-size="230">150</text>', "ciento", "crece", 0.5))
    for r in range(10):
        fs = "".join(fig(92 + i * 64, 900 + r * 76 - 40 * .3, .30, ll=True) for i in range(15))
        c.append(an(fs, f"=ciento+{0.05 + 0.07 * r:.2f}", "entra", 0.35))
    escena("frase:2", "".join(c))


# ═══════════════════════════════════════════════════════════════ 3 · cinco
def escena_5():
    c = [an(pill(540, 400, "DE VERDAD"), "verdad", "entra", 0.4)]
    c.append(an('<text class="cifra" x="540" y="820" text-anchor="middle" font-size="400">5</text>', "cinco", "crece", 0.5))
    for i in range(5):
        c.append(an(fig(140 + i * 200, 1260 - 40, 1.0, ll=True), f"=cinco+{0.15 + 0.12 * i:.2f}", "entra", 0.4))
    escena("frase:3", "".join(c))


# ═══════════════════════════════════════════════════════════════ 4 · Dunbar compara
def escena_dunbar():
    c = [an(pill(540, 330, "DUNBAR"), "dunbar", "entra", 0.4)]
    c.append(an('<path d="M170 1330 H960" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/>', "comparando", "dibuja", 0.7))
    c.append(an('<path d="M170 1330 V540" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/>', "=comparando+0.2", "dibuja", 0.7))
    c.append(an('<text class="mini" x="565" y="1402" text-anchor="middle">TAMAÑO DEL CEREBRO →</text>', "cerebro", "sube", 0.4))
    c.append(an('<g transform="rotate(-90 112 935)"><text class="mini" x="112" y="935" text-anchor="middle">TAMAÑO DEL GRUPO →</text></g>', "grupo", "sube", 0.4))
    xs = [290, 380, 470, 560, 650, 730, 800]
    jit = [-18, 14, -10, 22, -16, 10, -6]
    for i, (x, j) in enumerate(zip(xs, jit)):
        y = 1260 - (x - 250) * 0.782 + j
        c.append(an(f'<circle cx="{x}" cy="{y:.0f}" r="15" fill="#fff"/>', f"=primates+{0.12 * i:.2f}", "entra", 0.3))
    c.append(an('<path d="M250 1260 L880 767" stroke="#8d939a" stroke-width="5" stroke-dasharray="20 18" fill="none"/>', "=primates+0.9", "dibuja", 0.8))
    c.append(an('<circle cx="880" cy="690" r="30" fill="#fff"/><circle cx="880" cy="690" r="52" fill="none" stroke="#fff" stroke-width="5"/>', "nosotros", "crece", 0.5))
    c.append(an(pill(700, 590, "NOSOTROS · 150", False), "=nosotros+0.1", "entra", 0.4))
    escena("frase:4", "".join(c))


# ═══════════════════════════════════════════════════════════════ 5 · capas
CX, CY = 540, 900
RADIOS = [95, 195, 295, 395]


def puntos_anillo(n, r, fase=0.5):
    return [(CX + r * math.cos(math.radians(-90 + (k + fase) * 360 / n)),
             CY + r * math.sin(math.radians(-90 + (k + fase) * 360 / n))) for k in range(n)]


def escena_capas():
    c = [an(pill(540, 300, "LAS CAPAS"), "capas", "entra", 0.4)]
    c.append(an(fig(CX, CY + 22, .6, ll=True), "encontró", "entra", 0.4))
    for i, r in enumerate(RADIOS):
        c.append(an(f'<path d="M{CX} {CY-r} A{r} {r} 0 1 1 {CX} {CY+r} A{r} {r} 0 1 1 {CX} {CY-r}" fill="none" stroke="#8d939a" stroke-width="5" stroke-linecap="round"/>',
                    f"=capas+{0.1 + 0.15 * i:.2f}", "dibuja", 0.6))
    cuentas = [5, 10, 35, 100]
    ancla = ["cinco", "quince", "cincuenta", "ciento"]
    etq = ["5", "15", "50", "150"]
    for i, (r, n) in enumerate(zip(RADIOS, cuentas)):
        radio_p = 11 if i < 3 else 8
        pts = puntos_anillo(n, r, 0.5)
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio_p}" fill="#fff"/>' for x, y in pts)
        c.append(an(dots, ancla[i], "crece", 0.5))
        c.append(an(pill(CX, CY - r, etq[i], True, 118, 58), f"={ancla[i]}", "entra", 0.35))
    escena("frase:5", "".join(c))


# ═══════════════════════════════════════════════════════════════ 6 · tiempo
HEART = "M0 30 C-60 -20 -90 -50 -60 -85 C-35 -110 -5 -95 0 -70 C5 -95 35 -110 60 -85 C90 -50 60 -20 0 30 Z"


def escena_tiempo():
    c = []
    ticks = "".join(f'<line x1="0" y1="-170" x2="0" y2="-186" stroke="#fff" stroke-width="7" transform="rotate({k * 30})"/>' for k in range(12))
    c.append(an(f'<g transform="translate(540,700)"><circle r="196" fill="none" stroke="#fff" stroke-width="8"/>{ticks}</g>', "cuesta", "crece", 0.5))
    c.append(an('<g transform="translate(540,700)"><circle r="196" fill="none" stroke="none"/><line x1="0" y1="12" x2="0" y2="-150" stroke="#fff" stroke-width="8" stroke-linecap="round"/></g>', "cuesta", "gira", 0.4, 'data-amp="120"'))
    c.append(an('<g transform="translate(540,700)"><circle r="196" fill="none" stroke="none"/><line x1="0" y1="10" x2="0" y2="-100" stroke="#fff" stroke-width="12" stroke-linecap="round"/></g>', "=cuesta", "gira", 0.4, 'data-amp="10"'))
    c.append(an('<circle cx="540" cy="700" r="14" fill="#fff"/>', "=cuesta", "entra", 0.3))
    c.append(an(f'<g transform="translate(540,1290) scale(1.45)"><path d="{HEART}" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/></g>', "cariño", "entra", 0.4))
    c.append(an('<path d="M410 1160 L670 1420" stroke="#ff4d4d" stroke-width="12" stroke-linecap="round"/>', "=cariño+0.35", "dibuja", 0.35))
    c.append(an(pill(540, 1010, "TIEMPO"), "tiempo", "crece", 0.45))
    escena("frase:7", "".join(c))


# ═══════════════════════════════════════════════════════════════ 7 · seis meses
def escena_vinculo():
    c = []
    c.append(an(fig(260, 1050, 1.3, ll=True), "inicio", "entra", 0.4, 'data-visible="1"'))
    c.append(an(fig(820, 1050, 1.3, ll=True), "inicio", "entra", 0.4, 'data-visible="1"'))
    c.append(an(pill(540, 520, "SIN TIEMPO", False), "dejas", "entra", 0.4))
    enlace = ('<line x1="370" y1="990" x2="710" y2="990" stroke="#fff" stroke-width="7"/>'
              '<text class="mini" x="540" y="950" text-anchor="middle">VÍNCULO</text>')
    c.append(an(enlace, "dejas", "sale", 3.4, 'data-visible="1" data-amp="0"'))
    for i in range(6):
        x = 100 + i * 140
        c.append(an(f'<rect x="{x}" y="1260" width="124" height="124" rx="26" fill="none" stroke="#fff" stroke-width="6"/>'
                    f'<text x="{x+62}" y="1344" text-anchor="middle" font-size="64">{i+1}</text>', f"=seis+{0.0 + 0.2 * i:.2f}", "entra", 0.3))
    c.append(an('<text class="mini" x="540" y="1450" text-anchor="middle">MESES</text>', "=seis+1.2", "sube", 0.4))
    escena("frase:8", "".join(c))


# ═══════════════════════════════════════════════════════════════ 8 · sin aviso
def escena_se_va():
    c = []
    c.append(an(pill(540, 460, "SIN PELEA", False), "pelea", "entra", 0.4))
    c.append(an(pill(540, 560, "SIN AVISO"), "aviso", "entra", 0.4))
    c.append(an(fig(260, 1050, 1.3, ll=True), "inicio", "entra", 0.3, 'data-visible="1"'))
    c.append(an(fig(820, 1050, 1.3, op=0.35), "día", "entra", 0.5))
    c.append(an(fig(820, 1050, 1.3, ll=True), "inicio", "sale", 1.6, 'data-visible="1" data-amp="0"'))
    # el sale arranca en "día": se reajusta abajo con un segundo anclaje
    c[-1] = an(fig(820, 1050, 1.3, ll=True), "=día+0.1", "sale", 1.6, 'data-visible="1" data-amp="0"')
    c.append(an('<path d="M370 990 H710" stroke="#fff" stroke-width="7" stroke-dasharray="14 18"/>', "inicio", "sale", 1.3, 'data-visible="1" data-amp="0"'))
    c.append(an('<text class="mini" x="540" y="1330" text-anchor="middle">YA NO ES LO QUE ERA</text>', "=era-0.3", "sube", 0.5))
    escena("frase:9", "".join(c))


# ═══════════════════════════════════════════════════════════════ 9 · la mesa
def cabezas_mesa(cx, cy, n, R, r=26, ll=False, rot=-90):
    return [(cx + R * math.cos(math.radians(rot + k * 360 / n)), cy + R * math.sin(math.radians(rot + k * 360 / n))) for k in range(n)]


def mesa(cx, cy, n, R, rm, ll=True, rcab=26):
    s = f'<circle cx="{cx}" cy="{cy}" r="{rm}" fill="none" stroke="#8d939a" stroke-width="6"/>'
    for x, y in cabezas_mesa(cx, cy, n, R):
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rcab}" fill="#fff"/>'
    return s


def escena_mesa():
    c = [an(mesa(540, 900, 12, 215, 140), "inicio", "entra", 0.5, 'data-visible="0"')]
    c.append(an(pill(540, 470, "UNA MESA", False), "detalle", "entra", 0.4))
    escena("frase:10", "".join(c))


def escena_mesa_parte():
    c = [an(mesa(540, 900, 12, 215, 140), "inicio", "entra", 0.1, 'data-visible="1"')]
    pts = cabezas_mesa(540, 900, 12, 215)
    for g in range(3):
        a0 = -90 + g * 120 - 15
        a1 = a0 + 90 + 30 - 15 + 15
        a0r, a1r = math.radians(-90 + g * 120), math.radians(-90 + g * 120 + 90)
        x0, y0 = 540 + 215 * math.cos(a0r), 900 + 215 * math.sin(a0r)
        x1, y1 = 540 + 215 * math.cos(a1r), 900 + 215 * math.sin(a1r)
        banda = f'<path d="M{x0:.1f} {y0:.1f} A215 215 0 0 1 {x1:.1f} {y1:.1f}" fill="none" stroke="#fff" stroke-opacity="0.25" stroke-width="72" stroke-linecap="round"/>'
        c.append(an(banda, f"=parte+{0.25 * g:.2f}", "entra", 0.45))
    c.append(an(pill(540, 470, "3–4 PERSONAS"), "tres", "crece", 0.45))
    c.append(an('<text class="mini" x="540" y="1290" text-anchor="middle">UNA CONVERSACIÓN</text>', "conversación", "sube", 0.4))
    escena("frase:11", "".join(c))


def escena_dos_mesas():
    izq = mesa(290, 900, 6, 150, 92, rcab=24)
    der = mesa(790, 900, 6, 150, 92, rcab=24)
    c = [an(izq, "frase:12", "empuja", 0.7, 'data-dir="-1,0" data-amp="0"'),
         an(der, "frase:12", "empuja", 0.7, 'data-dir="1,0" data-amp="0"')]
    c.append(an(pill(540, 470, "DIVIDIDAS EN DOS"), "divididas", "entra", 0.45))
    c.append(an('<path d="M540 760 V1040" stroke="#fff" stroke-width="5" stroke-dasharray="12 16"/>', "=divididas+0.3", "dibuja", 0.5))
    escena("frase:12", "".join(c))


# ═══════════════════════════════════════════════════════════════ 10 · cada semana
def escena_semana():
    c = [an(pill(540, 400, "TU CÍRCULO", False), "círculo", "entra", 0.4)]
    c.append(an(pill(540, 520, "CADA SEMANA"), "semana", "crece", 0.45))
    dias = "LMXJVSD"
    cuenta = [3, 2, 4, 1, 3, 5, 2]
    for i, d in enumerate(dias):
        x = 92 + i * 128
        c.append(an(f'<rect x="{x}" y="660" width="116" height="74" rx="22" fill="none" stroke="#fff" stroke-width="5"/>'
                    f'<text x="{x+58}" y="716" text-anchor="middle" font-size="46">{d}</text>', f"=semana+{0.08 * i:.2f}", "entra", 0.3))
    for i, n in enumerate(cuenta):
        x = 92 + i * 128
        bl = ""
        for j in range(n):
            y = 770 + j * 72
            if j == 0:
                bl += f'<rect x="{x}" y="{y}" width="116" height="58" rx="16" fill="#fff"/>'
            else:
                bl += f'<rect x="{x}" y="{y}" width="116" height="58" rx="16" fill="none" stroke="#fff" stroke-width="5"/>'
        c.append(an(bl, f"horas+{0.0 + 0.16 * i:.2f}", "crece", 0.4))
    c.append(an('<text class="mini" x="540" y="1250" text-anchor="middle">LAS HORAS QUE REPARTES</text>', "repartes-0.3", "sube", 0.5))
    escena("frase:13", "".join(c))


# ═══════════════════════════════════════════════════════════════ 11 · subió / bajó
def escena_sube_baja():
    c = []
    for i, r in enumerate(RADIOS):
        c.append(an(f'<path d="M{CX} {CY-r} A{r} {r} 0 1 1 {CX} {CY+r} A{r} {r} 0 1 1 {CX} {CY-r}" fill="none" stroke="#8d939a" stroke-width="5" stroke-linecap="round"/>',
                    f"frase:14+{0.08 * i:.2f}", "dibuja", 0.6))
    c.append(an(fig(CX, CY + 22, .6, ll=True), "frase:14", "entra", 0.4))
    c.append(an(pill(540, 400, "SUBIÓ DE CAPA"), "subió", "entra", 0.4))
    c.append(an(pill(540, 1400, "BAJÓ", False), "bajó", "entra", 0.4))
    # quien sube: parte de la tercera capa y baja hacia el centro de la pantalla (hacia el interior)
    c.append(an(fig(CX, 605 + 22, .55, ll=True), "frase:14", "pan", 0.1, 'data-dir="0,1" data-amp="30" data-visible="1"'))
    # quien baja: parte de la segunda capa y sale hacia la tercera
    c.append(an(fig(CX - 195, CY + 22, .55), "frase:14", "entra", 0.3, 'data-visible="1"'))
    c[-1] = an(fig(CX - 195, CY + 22, .55), "bajó-0.1", "pan", 0.1, 'data-dir="-1,0" data-amp="95" data-visible="1"')
    escena("frase:14", "".join(c))


# ═══════════════════════════════════════════════════════════════ 12 · el calendario
def escena_calendario():
    c = [an('<g transform="translate(540,1400) scale(.8)"><use href="#per"/></g>'
            '<path d="M470 1320 L610 1470 M610 1320 L470 1470" stroke="#ff4d4d" stroke-width="11" stroke-linecap="round"/>'
            '<text class="mini" x="540" y="1520" text-anchor="middle">TÚ</text>', "decidiste", "entra", 0.4)]
    cuerpo = '<path d="M250 600 H830 Q850 600 850 620 V1240 Q850 1260 830 1260 H250 Q230 1260 230 1240 V620 Q230 600 250 600 Z" fill="none" stroke="#fff" stroke-width="7"/>'
    c.append(an(cuerpo, "=decidió-0.1", "dibuja", 0.8))
    c.append(an('<path d="M230 620 Q230 600 250 600 H830 Q850 600 850 620 V710 H230 Z" fill="#fff"/>'
                '<line x1="340" y1="570" x2="340" y2="640" stroke="#fff" stroke-width="12" stroke-linecap="round"/>'
                '<line x1="740" y1="570" x2="740" y2="640" stroke="#fff" stroke-width="12" stroke-linecap="round"/>', "=decidió+0.3", "entra", 0.45))
    k = 0
    for r in range(5):
        for i in range(7):
            x, y = 280 + i * 86, 790 + r * 90
            lleno = (r, i) in [(0, 2), (1, 4), (2, 1), (2, 5), (3, 3), (4, 0), (4, 6), (1, 0)]
            if lleno:
                cel = f'<circle cx="{x}" cy="{y}" r="22" fill="#fff"/>'
            else:
                cel = f'<circle cx="{x}" cy="{y}" r="22" fill="none" stroke="#8d939a" stroke-width="4"/>'
            c.append(an(cel, f"=decidió+{0.45 + 0.011 * k:.3f}", "entra", 0.25))
            k += 1
    c.append(an(pill(540, 440, "TU CALENDARIO"), "calendario", "crece", 0.5))
    escena("frase:16", "".join(c))


# ═══════════════════════════════════════════════════════════════ ensamblado
CABECERA = '''<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><link rel="stylesheet" href="base.css">
<style>
  @font-face { font-family: "Disp7"; src: url("fuentes/disp7.woff") format("woff"); font-weight: 700; }
  #esc { background: #000; }
  text { font-family: "Display"; font-weight: 900; fill: #fff; }
  .neg { fill: #000; }
  .etq { font-family: "Disp7"; font-weight: 700; font-size: 30px; letter-spacing: 5px; }
  .mini { font-family: "Disp7"; font-weight: 700; font-size: 26px; letter-spacing: 4px; fill: #c9ced4; }
  .cifra { font-size: 300px; letter-spacing: -6px; }
</style></head>
<body><div id="esc">
<svg class="fondo" viewBox="0 0 1080 1920">
<defs>
  <pattern id="malla" width="34" height="34" patternUnits="userSpaceOnUse">
    <circle cx="1.5" cy="1.5" r="1.5" fill="#ffffff" opacity="0.085"/>
  </pattern>
  <filter id="halo" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <g id="per" fill="none" stroke="#fff" stroke-width="7">
    <circle cx="0" cy="-96" r="33"/>
    <path d="M-44 40 V-26 A44 44 0 0 1 44 -26 V40"/>
    <path d="M-44 40 H44"/>
  </g>
  <g id="perll" fill="#fff" stroke="none">
    <circle cx="0" cy="-96" r="36"/>
    <path d="M-46 40 V-26 A46 46 0 0 1 46 -26 V40 Z"/>
  </g>
</defs>
<rect width="1080" height="1920" fill="#000"/>
<rect width="1080" height="1920" fill="url(#malla)"/>
'''
PIE = '''</svg>
<script src="escena.js"></script>
</div></body></html>'''

a(CABECERA)
escena_multitud()
escena_150()
escena_5()
escena_dunbar()
escena_capas()
escena_tiempo()
escena_vinculo()
escena_se_va()
escena_mesa()
escena_mesa_parte()
escena_dos_mesas()
escena_semana()
escena_sube_baja()
escena_calendario()
a(PIE)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dunbar.html"), "w", encoding="utf-8").write("\n".join(out))
print("ok", sum(len(x) for x in out) // 1024, "KB")
