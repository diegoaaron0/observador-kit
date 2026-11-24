from PIL import Image, ImageDraw
import math
W, H, CX, CY = 1080, 1920, 540, 860
def lienzo(): im = Image.new("L", (W, H), 0); return im, ImageDraw.Draw(im)

# Teléfono con mensaje en visto (✓✓)
im, d = lienzo()
d.rounded_rectangle([CX-220, CY-400, CX+220, CY+400], radius=60, fill=255)
d.rounded_rectangle([CX-190, CY-330, CX+190, CY+330], radius=20, fill=0)
d.rounded_rectangle([CX-60, CY-375, CX+60, CY-355], radius=10, fill=0)
d.rounded_rectangle([CX-40, CY-210, CX+165, CY-90], radius=34, fill=255)      # mi mensaje
d.polygon([(CX+140, CY-100), (CX+180, CY-80), (CX+150, CY-120)], fill=255)
for k in range(3): d.ellipse([CX+5+k*45, CY-165, CX+30+k*45, CY-140], fill=0)  # "..."
for dx in (0, 34):                                                            # ✓✓
    d.line([(CX+60+dx, CY-45), (CX+82+dx, CY-22), (CX+128+dx, CY-75)], fill=255, width=12, joint="curve")
im.save("telefono_visto.png")

# Piano (teclado)
im, d = lienzo()
x0, x1, y0, y1 = CX-400, CX+400, CY-170, CY+170
d.rectangle([x0, y0, x1, y1], fill=255)
n = 10; kw = (x1-x0)/n
for i in range(n):
    d.rectangle([x0+i*kw+6, y0+6, x0+(i+1)*kw-6, y1-6], fill=0)
    d.rectangle([x0+i*kw+18, y0+18, x0+(i+1)*kw-18, y1-18], fill=255)
for i in [1,2,4,5,6,8,9]:
    xb = x0+i*kw; d.rectangle([xb-24, y0, xb+24, y0+200], fill=255)
im.save("piano.png")

# Electrocardiograma
im, d = lienzo()
pts = [(CX-460, CY), (CX-200, CY), (CX-160, CY-40), (CX-130, CY), (CX-90, CY), (CX-60, CY+60), (CX-20, CY-260), (CX+20, CY+120),
       (CX+55, CY), (CX+120, CY), (CX+170, CY-70), (CX+220, CY), (CX+460, CY)]
d.line(pts, fill=255, width=18, joint="curve")
im.save("ecg.png")

# Fuego
im, d = lienzo()
def llama(cx, base, h, w):
    pts = []
    for k in range(41):
        t = k/40*math.pi
        x = cx + w*math.sin(t)*(1-0.15*math.cos(t))
        y = base - h*(1-math.cos(t))/2
        pts.append((x, y))
    pts += [(cx - w*math.sin(t)*(1-0.15*math.cos(t)), base - h*(1-math.cos(t))/2) for t in [k/40*math.pi for k in range(40, -1, -1)]]
    d.polygon(pts, fill=255)
llama(CX, CY+300, 620, 230)
d.polygon([(CX-80, CY-100), (CX, CY-330), (CX+60, CY-120)], fill=255)
im2, d2 = lienzo()
im = im
d.ellipse([CX-110, CY+20, CX+110, CY+280], fill=0)                            # hueco interior
d.polygon([(CX-70, CY+120), (CX, CY-60), (CX+70, CY+120)], fill=0)
d.rectangle([CX-300, CY+320, CX+300, CY+345], fill=255)                       # brasas
for k in range(-2, 3): d.ellipse([CX+k*110-40, CY+300, CX+k*110+40, CY+360], fill=255)
im.save("fuego.png")
