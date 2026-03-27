"""Icon Proposal 2: Dark hexagonal with glow and orbiting arrows."""
from PIL import Image, ImageDraw, ImageFont
import math

size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background: dark gradient
for y in range(size):
    r = int(25 + (45 - 25) * y / size)
    g = int(25 + (25 - 25) * y / size)
    b = int(35 + (55 - 35) * y / size)
    draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

mask = Image.new("L", (size, size), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=100, fill=255)
img.putalpha(mask)
draw = ImageDraw.Draw(img)

# Central hexagon with glow
cx, cy = 256, 230
hex_r = 120
for i in range(3, 0, -1):
    pts = []
    for a in range(6):
        rad = math.radians(60 * a - 30)
        pts.append((cx + (hex_r + i * 15) * math.cos(rad), cy + (hex_r + i * 15) * math.sin(rad)))
    draw.polygon(pts, fill=(0, 120, 255, 20 + i * 8))

pts = []
for a in range(6):
    rad = math.radians(60 * a - 30)
    pts.append((cx + hex_r * math.cos(rad), cy + hex_r * math.sin(rad)))
draw.polygon(pts, fill=(0, 100, 220, 180), outline=(80, 180, 255, 255), width=3)

# Landscape inside hexagon
draw.polygon([(cx - 50, cy + 40), (cx - 10, cy - 30), (cx + 30, cy + 40)], fill=(80, 200, 255, 200))
draw.polygon([(cx + 5, cy + 40), (cx + 30, cy + 5), (cx + 55, cy + 40)], fill=(50, 160, 230, 200))
draw.ellipse([(cx + 25, cy - 45), (cx + 50, cy - 20)], fill=(255, 200, 60, 220))

# Orbiting arrows
for angle_offset in [0, 120, 240]:
    for t in range(0, 60, 2):
        aa = math.radians(angle_offset + 20 + t)
        x = cx + 155 * math.cos(aa)
        y = cy + 155 * math.sin(aa)
        alpha = int(255 * (t / 60))
        draw.ellipse([(x - 2.5, y - 2.5), (x + 2.5, y + 2.5)], fill=(80, 180, 255, alpha))
    ea = math.radians(angle_offset + 80)
    ex = cx + 155 * math.cos(ea)
    ey = cy + 155 * math.sin(ea)
    pa = math.radians(angle_offset + 80 + 90)
    draw.polygon([
        (ex + 10 * math.cos(ea), ey + 10 * math.sin(ea)),
        (ex + 10 * math.cos(pa), ey + 10 * math.sin(pa)),
        (ex - 10 * math.cos(pa), ey - 10 * math.sin(pa)),
    ], fill=(80, 180, 255, 230))

# Text
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
except Exception:
    font = font_sm = ImageFont.load_default()
draw.text((145, 380), "IMAGE", fill=(255, 255, 255, 240), font=font)
draw.text((280, 385), "TRANSFORM", fill=(80, 180, 255, 240), font=font_sm)
draw.text((185, 425), "L I T E", fill=(255, 255, 255, 120), font=font_sm)

img.save("icon_proposal_2.png")
print("Saved: icon_proposal_2.png")
