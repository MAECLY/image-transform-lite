from PIL import Image, ImageOps, ImageEnhance


def flip_image(img: Image.Image, direction: str) -> Image.Image:
    if direction.lower() in ("h", "horizontal"):
        return ImageOps.mirror(img)
    elif direction.lower() in ("v", "vertical"):
        return ImageOps.flip(img)
    raise ValueError(f"flip direction must be horizontal|vertical, got {direction}")


def rotate_image(img: Image.Image, degrees: int) -> Image.Image:
    img_rgba = img.convert("RGBA")
    rotated = img_rgba.rotate(
        degrees, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0)
    )
    return rotated


def safe_square_crop(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        # No alpha channel — do a simple center square crop
        w, h = img.size
        side = min(w, h)
        cx, cy = w // 2, h // 2
        left = cx - side // 2
        top = cy - side // 2
        return img.crop((left, top, left + side, top + side))

    w, h = img.size
    cx, cy = w // 2, h // 2
    side = min(w, h)

    def crop_center(s: int) -> Image.Image:
        left = int(cx - s / 2)
        top = int(cy - s / 2)
        return img.crop((left, top, left + s, top + s))

    def corners_opaque(s: int) -> bool:
        c = crop_center(s)
        alpha = c.split()[-1]
        px = alpha.load()
        n = s - 1
        return all(px[x, y] > 0 for x, y in [(0, 0), (0, n), (n, 0), (n, n)])

    s = side if side % 2 == 0 else side - 1
    while s > 10 and not corners_opaque(s):
        s -= 2

    return crop_center(s)


def resize_image(
    img: Image.Image, mode: str, percentage: int = 100,
    width: int = 0, height: int = 0, keep_aspect: bool = True,
) -> Image.Image:
    if mode == "percentage":
        if percentage == 100:
            return img
        new_w = int(img.width * percentage / 100)
        new_h = int(img.height * percentage / 100)
        return img.resize((new_w, new_h), Image.LANCZOS)

    # mode == "dimensions"
    if width <= 0 and height <= 0:
        return img
    if keep_aspect:
        if width > 0 and height > 0:
            ratio = min(width / img.width, height / img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
        elif width > 0:
            ratio = width / img.width
            new_w = width
            new_h = int(img.height * ratio)
        else:
            ratio = height / img.height
            new_w = int(img.width * ratio)
            new_h = height
    else:
        new_w = width if width > 0 else img.width
        new_h = height if height > 0 else img.height

    return img.resize((new_w, new_h), Image.LANCZOS)


def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    if factor == 1.0:
        return img
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    return ImageEnhance.Brightness(rgb).enhance(factor)


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    if factor == 1.0:
        return img
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    return ImageEnhance.Contrast(rgb).enhance(factor)


def adjust_sharpness(img: Image.Image, factor: float) -> Image.Image:
    if factor == 1.0:
        return img
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    return ImageEnhance.Sharpness(rgb).enhance(factor)
