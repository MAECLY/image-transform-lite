"""Generate assets/icon.ico (Windows) and assets/icon.png (Linux) from assets/icon.icns.

Usage (from the repo root):
    python scripts/generate_platform_icons.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICNS = ASSETS / "icon.icns"
ICO = ASSETS / "icon.ico"
PNG = ASSETS / "icon.png"

ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
PNG_SIZE = 512


def load_largest(icns_path: Path) -> Image.Image:
    img = Image.open(icns_path)
    sizes = img.info.get("sizes") or []
    if sizes:
        # IcnsImagePlugin: load the biggest (w, h, scale) representation.
        w, _, scale = max(sizes, key=lambda s: s[0] * s[2])
        img.size = (w, w)
        img.load(scale)
    else:
        img.load()
    return img.convert("RGBA")


def main() -> None:
    src = load_largest(ICNS)
    print(f"Fuente: {ICNS.name} {src.size}")

    png = src.resize((PNG_SIZE, PNG_SIZE), Image.LANCZOS) if src.size != (PNG_SIZE, PNG_SIZE) else src
    png.save(PNG, format="PNG", optimize=True)
    print(f"Generado: {PNG.relative_to(ROOT)} {png.size}")

    base = src.resize((256, 256), Image.LANCZOS)
    base.save(ICO, format="ICO", sizes=ICO_SIZES)
    print(f"Generado: {ICO.relative_to(ROOT)} {[s[0] for s in ICO_SIZES]}")


if __name__ == "__main__":
    main()
