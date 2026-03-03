from PIL import Image, ImageDraw, ImageFilter
import os
import math

W = 1200
H = 1800

os.makedirs("static/backgrounds", exist_ok=True)
os.makedirs("static/frames", exist_ok=True)


def gradient_bg(color1, color2, filename, diagonal=False):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        if diagonal:
            t = min(1.0, (y / H + (0 / W)) / 1.2)
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    img.save(f"static/backgrounds/{filename}")
    print(f"✓ {filename}")


def bg_navy_modern():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(10 + 8 * t)
        g = int(15 + 20 * t)
        b = int(40 + 40 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Subtle geometric accent - thin lines
    for i in range(3):
        x = W // 4 + i * W // 4
        draw.line([(x, H * 2 // 3), (x, H - 80)], fill=(255, 255, 255, 30), width=1)

    # Soft circle accent top right
    for radius in [300, 400, 500]:
        draw.ellipse([W - radius, -radius, W + radius//2, radius//2],
                     outline=(255, 255, 255, 10), width=1)

    img = img.filter(ImageFilter.GaussianBlur(0.5))
    img.save("static/backgrounds/navy_modern.jpg")
    print("✓ navy_modern.jpg")


def bg_cream_minimal():
    img = Image.new("RGB", (W, H), (245, 240, 232))
    draw = ImageDraw.Draw(img)

    # Very subtle warm gradient
    for y in range(H):
        t = y / H
        r = int(245 - 10 * t)
        g = int(240 - 12 * t)
        b = int(232 - 15 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Thin geometric lines - minimalist accent
    line_color = (200, 190, 175)
    draw.line([(80, 80), (80, H - 80)], fill=line_color, width=1)
    draw.line([(80, 80), (W - 80, 80)], fill=line_color, width=1)

    img.save("static/backgrounds/cream_minimal.jpg")
    print("✓ cream_minimal.jpg")


def bg_sage_green():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(100 + 15 * t)
        g = int(130 + 10 * t)
        b = int(110 + 10 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    img.save("static/backgrounds/sage_green.jpg")
    print("✓ sage_green.jpg")


def bg_charcoal():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        v = int(28 + 18 * t)
        draw.line([(0, y), (W, y)], fill=(v, v, v))

    # Subtle radial light from top center
    for r in range(600, 0, -20):
        alpha = max(0, int(8 * (1 - r / 600)))
        draw.ellipse([W//2 - r, -r//2, W//2 + r, r], fill=(alpha + 28, alpha + 28, alpha + 28))

    img.save("static/backgrounds/charcoal.jpg")
    print("✓ charcoal.jpg")


def bg_soft_blue():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(210 - 40 * t)
        g = int(225 - 30 * t)
        b = int(245 - 20 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    img.save("static/backgrounds/soft_blue.jpg")
    print("✓ soft_blue.jpg")


# ─── FRAMES ─────────────────────────────────────────────────────────────────

def frame_thin_white():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 32  # margin
    t = 3   # thickness

    # Outer border
    draw.rectangle([m, m, W - m, H - m], outline=(255, 255, 255, 220), width=t)
    # Inner border subtle
    draw.rectangle([m + 12, m + 12, W - m - 12, H - m - 12], outline=(255, 255, 255, 80), width=1)

    # Corner accents
    corner = 60
    corners = [(m, m), (W - m, m), (m, H - m), (W - m, H - m)]
    offsets = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for (cx, cy), (ox, oy) in zip(corners, offsets):
        draw.line([(cx, cy), (cx + ox * corner, cy)], fill=(255, 255, 255, 255), width=3)
        draw.line([(cx, cy), (cx, cy + oy * corner)], fill=(255, 255, 255, 255), width=3)

    img.save("static/frames/frame_white_elegant.png")
    print("✓ frame_white_elegant.png")


def frame_gold_minimal():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 40
    gold = (212, 175, 55, 255)
    gold_soft = (212, 175, 55, 120)

    # Double border
    draw.rectangle([m, m, W - m, H - m], outline=gold, width=3)
    draw.rectangle([m + 14, m + 14, W - m - 14, H - m - 14], outline=gold_soft, width=1)

    # Corner ornament
    size = 80
    for cx, cy, ox, oy in [(m, m, 1, 1), (W-m, m, -1, 1), (m, H-m, 1, -1), (W-m, H-m, -1, -1)]:
        draw.line([(cx, cy), (cx + ox * size, cy)], fill=gold, width=3)
        draw.line([(cx, cy), (cx, cy + oy * size)], fill=gold, width=3)
        # Small dot at corner
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=gold)

    img.save("static/frames/frame_gold_minimal.png")
    print("✓ frame_gold_minimal.png")


def frame_modern_accent():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    white_soft = (255, 255, 255, 140)
    m = 40

    # Only corner L-shapes, no full border — modern asymmetric
    size = 120
    thick = 4

    # Top-left
    draw.rectangle([m, m, m + size, m + thick], fill=white)
    draw.rectangle([m, m, m + thick, m + size], fill=white)

    # Top-right
    draw.rectangle([W - m - size, m, W - m, m + thick], fill=white)
    draw.rectangle([W - m - thick, m, W - m, m + size], fill=white)

    # Bottom-left
    draw.rectangle([m, H - m - thick, m + size, H - m], fill=white)
    draw.rectangle([m, H - m - size, m + thick, H - m], fill=white)

    # Bottom-right
    draw.rectangle([W - m - size, H - m - thick, W - m, H - m], fill=white)
    draw.rectangle([W - m - thick, H - m - size, W - m, H - m], fill=white)

    # Thin bottom strip accent
    draw.rectangle([m, H - m - 60, W - m, H - m - 58], fill=white_soft)

    img.save("static/frames/frame_modern_accent.png")
    print("✓ frame_modern_accent.png")


print("=== Membuat backgrounds ===")
bg_navy_modern()
bg_cream_minimal()
bg_sage_green()
bg_charcoal()
bg_soft_blue()

print("\n=== Membuat frames ===")
frame_thin_white()
frame_gold_minimal()
frame_modern_accent()

print("\n✅ Semua asset selesai!")
