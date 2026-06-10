#!/usr/bin/env python3
"""Genera los iconos PNG de la PWA: rueda de timon sobre fondo azul oscuro."""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), '..')
ICON_DIR = os.path.join(ROOT, 'icons')

BG = (11, 18, 32)        # --bg
ACCENT = (79, 140, 255)  # --accent
WHITE = (232, 237, 247)


def rounded_bg(draw, size, radius):
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)


def helm(draw, cx, cy, r, width):
    """Rueda de timon: aro exterior, 8 radios con empunaduras y buje central."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ACCENT, width=width)
    handle_r = r * 0.16
    hub_r = r * 0.30
    for i in range(8):
        ang = math.radians(i * 45)
        dx, dy = math.cos(ang), math.sin(ang)
        draw.line([cx + dx * hub_r * 0.8, cy + dy * hub_r * 0.8,
                   cx + dx * (r + handle_r * 1.7), cy + dy * (r + handle_r * 1.7)],
                  fill=ACCENT, width=width)
        hx, hy = cx + dx * (r + handle_r * 1.7), cy + dy * (r + handle_r * 1.7)
        draw.ellipse([hx - handle_r, hy - handle_r, hx + handle_r, hy + handle_r], fill=ACCENT)
    draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill=BG, outline=ACCENT, width=width)
    dot = hub_r * 0.42
    draw.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=WHITE)


def make_icon(size, path, maskable=False):
    scale = 4  # supersampling para bordes suaves
    s = size * scale
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rounded_bg(draw, s, radius=0 if maskable else s // 5)
    # zona segura maskable: el contenido debe caber en el 80% central
    wheel_r = s * (0.215 if maskable else 0.26)
    helm(draw, s / 2, s / 2, wheel_r, width=max(scale, int(s * 0.028)))
    img = img.resize((size, size), Image.LANCZOS)
    img.save(path)
    print(f'{path}: {size}x{size}')


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    make_icon(180, os.path.join(ICON_DIR, 'icon-180.png'))
    make_icon(192, os.path.join(ICON_DIR, 'icon-192.png'))
    make_icon(512, os.path.join(ICON_DIR, 'icon-512.png'))
    make_icon(512, os.path.join(ICON_DIR, 'icon-512-maskable.png'), maskable=True)


if __name__ == '__main__':
    main()
