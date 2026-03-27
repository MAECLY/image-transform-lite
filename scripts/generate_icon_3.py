"""Icon Proposal 3: Coral-to-purple gradient with geometric T and thumbnails."""
from PIL import Image, ImageDraw, ImageFont
import math

size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background: warm coral-to-purple gradient
for y in range(size):
    t = y / size
    r = int(255 * (1 - t * 0.4))
    g = int(90 * (1 - t * 0.3))
    b = int(120 + (180 - 120) * t)
    draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

mask = Image.new("L", (size, size), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=100, fill=255)
img.putalpha(mask)
draw = ImageDraw.Draw(img)

cx, cy = 256, 220

# Large T shape
draw.rounded_rectangle([(cx - 110, cy - 80), (cx + 110, cy - 30)], radius=10, fill=(255, 255, 255, 230))
draw.rounded_rectangle([(cx - 28, cy - 50), (cx + 28, cy + 100)], radius=10, fill=(255, 255, 255, 230))

# Thumbnails
thumb_size = 50
draw.rounded_rectangle([(70, 100), (70 + thumb_size, 100 + thumb_size)], radius=6,
                        fill=(255, 255, 255, 100), outline=(255, 255, 255, 180), width=2)
draw.polygon([(80, 140), (95, 115), (110, 140)], fill=(255, 255, 255, 140))

draw.rounded_rectangle([(390, 100), (390 + thumb_size, 100 + thumb_size)], radius=6,
                        fill=(255, 255, 255, 100), outline=(255, 255, 255, 180), width=2)
draw.polygon([(430, 140), (415, 115), (400, 140)], fill=(255, 255, 255, 140))

draw.rounded_rectangle([(400, 325), (400 + 35, 325 + 35)], radius=4,
                        fill=(255, 255, 255, 100), outline=(255, 255, 255, 180), width=2)
draw.polygon([(408, 350), (418, 335), (428, 350)], fill=(255, 255, 255, 140))

# Rotated thumbnail (bottom-left)
rot_cx, rot_cy = 95, 330
corners_rot = []
for ddx, ddy in [(-20, -15), (20, -15), (20, 15), (-20, 15)]:
    rad = math.radians(15)
    rx = ddx * math.cos(rad) - ddy * math.sin(rad) + rot_cx
    ry = ddx * math.sin(rad) + ddy * math.cos(rad) + rot_cy
    corners_rot.append((rx, ry))
draw.polygon(corners_rot, fill=(255, 255, 255, 100), outline=(255, 255, 255, 180))

# Dotted connecting lines
for sx, sy in [(120, 125), (390, 125), (120, 340), (400, 345)]:
    dx = cx - sx
    dy = cy - sy
    dist = math.sqrt(dx * dx + dy * dy)
    for t_step in range(0, int(dist), 12):
        px = sx + dx * t_step / dist
        py = sy + dy * t_step / dist
        draw.ellipse([(px - 1.5, py - 1.5), (px + 1.5, py + 1.5)], fill=(255, 255, 255, 80))

# Text
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
except Exception:
    font = font_sm = ImageFont.load_default()
draw.text((128, 400), "Transform", fill=(255, 255, 255, 240), font=font)
draw.text((210, 448), "L I T E", fill=(255, 255, 255, 150), font=font_sm)

img.save("icon_proposal_3.png")
print("Saved: icon_proposal_3.png")
