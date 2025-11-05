"""image_utils.py

Utility image processing functions used by the example endpoints.
Add functions here for each "phase" and operation you need (brightness, contrast,
segmentation, display-correction, etc.). Keep these small and testable.
"""
from PIL import Image, ImageEnhance, ImageOps
from PIL import ImageFilter
import io
from typing import Optional, Tuple
import random
import math


def process_image(img: Image.Image, phase: str, operation: str) -> Image.Image:
    """Process a PIL Image and return a new PIL Image.

    Parameters
    - img: PIL.Image.Image - input image
    - phase: str - logical phase (e.g., "phase1", "phase2") or feature group
    - operation: str - operation name (e.g., "brightness_increase")

    This function is intentionally simple. Extend with better parameter
    parsing and more operations as needed.
    """
    # Normalize inputs
    phase = (phase or "").lower()
    operation = (operation or "").lower()

    # Example operations. Replace or expand with project-specific logic.
    if "brightness" in operation:
        # choose a factor based on operation keyword
        factor = 1.5 if "increase" in operation else 0.7
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    if "contrast" in operation:
        factor = 1.5 if "increase" in operation else 0.7
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    if "segmentation" in operation:
        # crude segmentation: convert to grayscale and threshold
        gray = img.convert("L")
        # simple global threshold
        thresh = 128
        return gray.point(lambda p: 255 if p > thresh else 0).convert("RGB")

    if "display" in operation or "autocorrect" in operation or "display-correction" in operation:
        # use autocontrast as a basic display correction
        return ImageOps.autocontrast(img)

    # Default: no-op (return original copy)
    return img.copy()


def image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    """Convert a PIL Image to raw bytes in memory.

    Returns bytes in the requested format (PNG by default).
    """
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    """Return a new image with brightness adjusted by factor (>1 brighter, <1 darker)."""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(float(factor))


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    """Return a new image with contrast adjusted by factor (>1 more contrast)."""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(float(factor))


def rotate_image(img: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    """Rotate the image by `angle` degrees. expand=True grows the canvas if needed."""
    return img.rotate(float(angle), expand=bool(expand))


def to_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale (RGB output)."""
    return img.convert("L").convert("RGB")


def blur_image(img: Image.Image, radius: float = 2.0) -> Image.Image:
    """Apply Gaussian blur with the given radius."""
    return img.filter(ImageFilter.GaussianBlur(radius=float(radius)))


def sharpen_image(img: Image.Image) -> Image.Image:
    """Apply a sharpening filter to the image."""
    return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))


def apply_mask(img: Image.Image, mask_img: Image.Image) -> Image.Image:
    """Apply a mask image to img. The mask should be grayscale or have alpha channel.

    Areas where mask is black will become transparent/empty; white will be kept.
    Returns an RGB image where masked-out areas are filled with black.
    """
    # Normalize mask to single-channel L
    mask = mask_img.convert("L").resize(img.size)
    # Create a black background and composite
    background = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(img, background, mask)


def segmentation_simple(img: Image.Image, method: str = "threshold", threshold: int = 128) -> Image.Image:
    """Simple segmentation examples. Returns an RGB image where segments are binary.

    - method='threshold' does a global grayscale threshold.
    """
    method = (method or "").lower()
    if method == "threshold":
        gray = img.convert("L")
        t = int(threshold)
        seg = gray.point(lambda p: 255 if p > t else 0)
        return seg.convert("RGB")

    if method == "kmeans":
        # simple k-means on RGB colors; returns segmented image with cluster colors
        return kmeans_segmentation(img, k=4)

    if method == "watershed":
        # approximate watershed by seeding from kmeans and smoothing boundaries
        return watershed_like_segmentation(img, k=6, iterations=4)

    # default fallback: return original
    return img.copy()


def _closest_center_index(color, centers):
    # color and centers are (r,g,b)
    best = 0
    best_d = None
    for i, c in enumerate(centers):
        d = (color[0]-c[0])**2 + (color[1]-c[1])**2 + (color[2]-c[2])**2
        if best_d is None or d < best_d:
            best_d = d
            best = i
    return best


def kmeans_segmentation(img: Image.Image, k: int = 4, max_iters: int = 10, sample_limit: int = 10000) -> Image.Image:
    """Perform a lightweight k-means clustering on pixel colors and return an RGB image

    This implementation uses pure Python to avoid extra dependencies. For large
    images we sample pixels to estimate cluster centers and then assign all
    pixels to the nearest center.
    """
    img_rgb = img.convert("RGB")
    pixels = list(img_rgb.getdata())
    n = len(pixels)

    # sampling for speed
    if n > sample_limit:
        step = max(1, n // sample_limit)
        sample = pixels[::step]
    else:
        sample = pixels[:]

    # initialize centers by random samples
    random.shuffle(sample)
    centers = [tuple(sample[i % len(sample)]) for i in range(k)]

    for _it in range(max_iters):
        clusters = [[] for _ in range(k)]
        for px in sample:
            idx = _closest_center_index(px, centers)
            clusters[idx].append(px)

        new_centers = []
        changed = False
        for cl in clusters:
            if not cl:
                # reinitialize empty cluster
                new_centers.append(tuple(sample[random.randrange(len(sample))]))
                changed = True
                continue
            r = sum(p[0] for p in cl) / len(cl)
            g = sum(p[1] for p in cl) / len(cl)
            b = sum(p[2] for p in cl) / len(cl)
            nc = (int(r), int(g), int(b))
            if nc != centers[len(new_centers)]:
                changed = True
            new_centers.append(nc)

        centers = new_centers
        if not changed:
            break

    # assign every pixel to nearest center
    assigned = [centers[_closest_center_index(px, centers)] for px in pixels]
    out = Image.new("RGB", img_rgb.size)
    out.putdata(assigned)
    return out


def watershed_like_segmentation(img: Image.Image, k: int = 6, iterations: int = 3) -> Image.Image:
    """A lightweight 'watershed-like' segmentation.

    We seed regions with k-means clusters then perform several majority-vote
    smoothing passes so boundaries become more region-like. This is not a
    true watershed algorithm but behaves similarly for user-facing segmentation.
    """
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    pixels = list(img_rgb.getdata())

    # get initial labels from kmeans (we reuse centers)
    # run a sampled kmeans to get centers, then build label array
    # reuse kmeans sample logic but return centers only
    # quick centers estimation
    sample_limit = 8000
    n = len(pixels)
    if n > sample_limit:
        step = max(1, n // sample_limit)
        sample = pixels[::step]
    else:
        sample = pixels[:]
    random.shuffle(sample)
    centers = [tuple(sample[i % len(sample)]) for i in range(k)]

    # one-pass refine on sample
    for _ in range(6):
        clusters = [[] for _ in range(k)]
        for px in sample:
            clusters[_closest_center_index(px, centers)].append(px)
        new_centers = []
        for cl in clusters:
            if not cl:
                new_centers.append(centers[len(new_centers)])
                continue
            r = sum(p[0] for p in cl) / len(cl)
            g = sum(p[1] for p in cl) / len(cl)
            b = sum(p[2] for p in cl) / len(cl)
            new_centers.append((int(r), int(g), int(b)))
        centers = new_centers

    # assign labels for all pixels
    labels = [ _closest_center_index(px, centers) for px in pixels ]

    # smoothing: majority vote in 3x3 neighborhood
    def idx(x, y):
        return y * w + x

    for _it in range(iterations):
        new_labels = labels[:]
        for y in range(h):
            for x in range(w):
                counts = [0] * k
                for yy in range(max(0, y-1), min(h, y+2)):
                    for xx in range(max(0, x-1), min(w, x+2)):
                        counts[labels[idx(xx, yy)]] += 1
                # pick majority
                maj = max(range(k), key=lambda i: counts[i])
                new_labels[idx(x, y)] = maj
        labels = new_labels

    # map labels to center colors
    assigned = [centers[l] for l in labels]
    out = Image.new("RGB", img_rgb.size)
    out.putdata(assigned)
    return out


def color_adjust(img: Image.Image, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0, hue: float = 0.0, intensity: float = 0.0) -> Image.Image:
    """Adjust brightness, contrast, saturation and hue/intensity.

    Parameters:
    - brightness: multiplicative brightness factor (1.0 = no change)
    - contrast: multiplicative contrast factor (1.0 = no change)
    - saturation: multiplicative color/saturation factor (1.0 = no change)
    - hue: hue shift in degrees (-180..180). Positive rotates hue forward.
    - intensity: percent change to intensity/brightness (-100..100). This is applied as a multiplicative factor (1 + intensity/100).

    The function applies brightness/contrast/saturation via PIL enhancers, then applies a hue rotation
    by converting to HSV and shifting the H channel. Intensity is combined with brightness as a multiplier.
    """
    out = img

    # combine brightness with intensity slider (intensity is percent, e.g., -50..50)
    try:
        intensity_factor = 1.0 + float(intensity) / 100.0
    except Exception:
        intensity_factor = 1.0

    effective_brightness = float(brightness) * intensity_factor

    if effective_brightness != 1.0:
        out = ImageEnhance.Brightness(out).enhance(effective_brightness)
    if float(contrast) != 1.0:
        out = ImageEnhance.Contrast(out).enhance(float(contrast))
    if float(saturation) != 1.0:
        out = ImageEnhance.Color(out).enhance(float(saturation))

    # apply hue shift if requested (convert to HSV, adjust H channel)
    try:
        h_shift = int(float(hue) / 360.0 * 255.0) if float(hue) != 0.0 else 0
        if h_shift != 0:
            hsv = out.convert('HSV')
            h, s, v = hsv.split()

            # operate on raw bytes without external dependencies (slower but portable)
            h_vals = list(h.getdata())
            h_vals = [((int(v) + h_shift) % 256) for v in h_vals]
            h = Image.new('L', h.size)
            h.putdata(h_vals)

            hsv = Image.merge('HSV', (h, s, v))
            out = hsv.convert('RGB')
    except Exception:
        # if numpy isn't available or something fails, skip hue shift gracefully
        pass

    return out


def saturation_correction_autocorrect(img: Image.Image) -> Image.Image:
    """Basic display-based saturation correction: autocontrast + slight color boost."""
    out = ImageOps.autocontrast(img)
    out = ImageEnhance.Color(out).enhance(1.1)
    return out


def apply_saturation_adjustment(img: Image.Image, percent: float) -> Image.Image:
    """Adjust saturation by percent (-100..inf). Positive increases saturation.

    Uses PIL's ImageEnhance.Color which multiplies colorfulness by a factor.
    percent=10 -> factor=1.10
    """
    try:
        factor = 1.0 + float(percent) / 100.0
    except Exception:
        factor = 1.0
    return ImageEnhance.Color(img).enhance(factor)


def apply_gamma_correction(img: Image.Image, gamma: float = 2.2) -> Image.Image:
    """Apply gamma correction to an RGB image.

    Uses a lookup table to map 0..255 through the gamma curve. This implementation
    performs out = 255 * ((in/255) ** (1/gamma)), which brightens/darkens pixels
    according to the provided gamma value.
    """
    if gamma is None or gamma <= 0:
        return img
    inv_gamma = 1.0 / float(gamma)
    lut = [min(255, max(0, int(((i / 255.0) ** inv_gamma) * 255.0 + 0.5))) for i in range(256)]
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()
    r = r.point(lut)
    g = g.point(lut)
    b = b.point(lut)
    return Image.merge("RGB", (r, g, b))


def kelvin_to_rgb(kelvin: float) -> Tuple[float, float, float]:
    """Convert a color temperature in Kelvin to an approximate RGB multiplier.

    Returns normalized multipliers in range 0..1 for R, G, B.
    Uses the algorithm from Tanner Helland (good approximation for 1000K..40000K).
    """
    temp = float(kelvin) / 100.0
    if temp <= 66:
        red = 255
        green = 99.4708025861 * math.log(temp) - 161.1195681661
        if temp <= 19:
            blue = 0
        else:
            blue = 138.5177312231 * math.log(temp - 10) - 305.0447927307
    else:
        red = 329.698727446 * ((temp - 60) ** -0.1332047592)
        green = 288.1221695283 * ((temp - 60) ** -0.0755148492)
        blue = 255

    def clamp255(x):
        try:
            return max(0, min(255, int(x)))
        except Exception:
            return 0

    r = clamp255(red) / 255.0
    g = clamp255(green) / 255.0
    b = clamp255(blue) / 255.0
    return (r, g, b)


def apply_color_temperature(img: Image.Image, kelvin: float = 6500.0) -> Image.Image:
    """Apply a color temperature adjustment by scaling R/G/B channels.

    Uses a per-channel lookup table so the operation remains fast in pure-PIL.
    """
    r_mult, g_mult, b_mult = kelvin_to_rgb(kelvin)
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()
    r_lut = [min(255, int(i * r_mult + 0.5)) for i in range(256)]
    g_lut = [min(255, int(i * g_mult + 0.5)) for i in range(256)]
    b_lut = [min(255, int(i * b_mult + 0.5)) for i in range(256)]
    r = r.point(r_lut)
    g = g.point(g_lut)
    b = b.point(b_lut)
    return Image.merge("RGB", (r, g, b))


def calibrate_display(img: Image.Image, display_type: str) -> Image.Image:
    """Calibrate an image's saturation, gamma and color temperature for a display.

    display_type (case-insensitive) choices and saturation adjustments:
      - lcd / LCD: +10%
      - led backlit / LED Backlit: +15%
      - oled / OLED: -7%
      - qled / QLED: -3%
      - e-paper / E-Paper: 0%

    The function applies saturation adjustment, then gamma correction (gamma=2.2),
    and finally sets color temperature to 6500K for consistent white point.
    """
    dt = (display_type or "").strip().lower()
    # accept some common aliases
    aliases = {
        "lcd": "lcd",
        "led backlit": "led backlit",
        "led": "led backlit",
        "led-backlit": "led backlit",
        "oled": "oled",
        "qled": "qled",
        "e-paper": "e-paper",
        "epaper": "e-paper",
        "e_paper": "e-paper",
    }
    dt = aliases.get(dt, dt)

    sat_map = {
        "lcd": 10.0,
        "led backlit": 15.0,
        "oled": -7.0,
        "qled": -3.0,
        "e-paper": 0.0,
    }

    if dt not in sat_map:
        raise ValueError(f"Unsupported display type: {display_type}")

    sat_percent = sat_map[dt]

    out = apply_saturation_adjustment(img, sat_percent)
    out = apply_gamma_correction(out, 2.2)
    out = apply_color_temperature(out, 6500.0)
    return out
