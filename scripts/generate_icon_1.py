"""Icon Proposal 1: Blue gradient with overlapping image frames and transform arrow."""
from PIL import Image, ImageDraw, ImageFont
import math

size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background: blue gradient
for y in range(size):
    r = int(0 + (30 - 0) * y / size)
    g = int(100 + (60 - 100) * y / size)
    b = int(255 + (200 - 255) * y / size)
    draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

# Round corners mask
mask = Image.new("L", (size, size), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=100, fill=255)
img.putalpha(mask)
draw = ImageDraw.Draw(img)

# Frame 1 (back, rotated)
cx, cy = 230, 240
frame_w, frame_h = 180, 140
angle = -12
corners = []
for dx, dy in [(-frame_w // 2, -frame_h // 2), (frame_w // 2, -frame_h // 2),
               (frame_w // 2, frame_h // 2), (-frame_w // 2, frame_h // 2)]:
    rad = math.radians(angle)
    rx = dx * math.cos(rad) - dy * math.sin(rad) + cx
    ry = dx * math.sin(rad) + dy * math.cos(rad) + cy
    corners.append((rx, ry))
draw.polygon(corners, fill=(255, 255, 255, 60), outline=(255, 255, 255, 120))

# Mountains in frame 1
mx, my = cx - 20, cy + 10
draw.polygon([(mx - 30, my + 25), (mx, my - 20), (mx + 30, my + 25)], fill=(255, 255, 255, 80))
draw.polygon([(mx + 10, my + 25), (mx + 30, my - 5), (mx + 50, my + 25)], fill=(255, 255, 255, 60))

# Frame 2 (front, straight)
cx2, cy2 = 290, 260
draw.rounded_rectangle(
    [(cx2 - frame_w // 2, cy2 - frame_h // 2), (cx2 + frame_w // 2, cy2 + frame_h // 2)],
    radius=12, fill=(255, 255, 255, 200), outline=(255, 255, 255, 255), width=3,
)

# Mountains + sun in frame 2
mx2, my2 = cx2 - 10, cy2 + 15
draw.polygon([(mx2 - 40, my2 + 30), (mx2, my2 - 30), (mx2 + 40, my2 + 30)], fill=(100, 180, 255, 200))
draw.polygon([(mx2 + 15, my2 + 30), (mx2 + 35, my2 - 10), (mx2 + 55, my2 + 30)], fill=(60, 140, 220, 200))
draw.ellipse([(cx2 + 30, cy2 - 50), (cx2 + 60, cy2 - 20)], fill=(255, 220, 80, 220))

# Transform arrow (circular)
arrow_cx, arrow_cy = 370, 150
arrow_r = 40
for a in range(30, 300, 3):
    rad = math.radians(a)
    x = arrow_cx + arrow_r * math.cos(rad)
    y = arrow_cy + arrow_r * math.sin(rad)
    draw.ellipse([(x - 3, y - 3), (x + 3, y + 3)], fill=(255, 255, 255, 230))

a_rad = math.radians(300)
ax = arrow_cx + arrow_r * math.cos(a_rad)
ay = arrow_cy + arrow_r * math.sin(a_rad)
draw.polygon([(ax, ay - 12), (ax + 16, ay + 4), (ax - 4, ay + 8)], fill=(255, 255, 255, 230))

# Text
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
except Exception:
    font = ImageFont.load_default()
draw.text((120, 390), "TRANSFORM", fill=(255, 255, 255, 220), font=font)

img.save("icon_proposal_1.png")
print("Saved: icon_proposal_1.png")
