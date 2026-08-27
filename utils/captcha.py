import secrets
import string
import math


_CHARS = string.ascii_uppercase.replace('O', '').replace('I', '').replace('L', '') + string.digits.replace('0', '').replace('1', '')


def generate_captcha_text(length=5):
    return ''.join(secrets.choice(_CHARS) for _ in range(length))


def _randint(a, b):
    return a + secrets.randbelow(b - a + 1)


def _choice(seq):
    return secrets.choice(seq)


def _uniform(a, b):
    return a + secrets.randbelow(int((b - a) * 1000)) / 1000.0


def generate_captcha_svg(text, width=150, height=50):
    colors = ['#e74c3c', '#e67e22', '#27ae60', '#2980b9', '#8e44ad', '#c0392b', '#16a085']
    bg_color = '#e8e8e8'

    chars_svg = ''
    char_width = width / (len(text) + 1)
    for i, ch in enumerate(text):
        x = char_width * (i + 0.7)
        y = height / 2 + _randint(-8, 8)
        angle = _randint(-25, 25)
        font_size = _randint(20, 28)
        color = _choice(colors)
        dx = _uniform(-2, 2)
        dy = _uniform(-2, 2)
        chars_svg += f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{font_size}" font-weight="bold" fill="{color}" text-anchor="middle" dominant-baseline="central" transform="rotate({angle},{x},{y})" dx="{dx}" dy="{dy}">{ch}</text>'

    lines_svg = ''
    for _ in range(6):
        x1 = _randint(0, width)
        y1 = _randint(0, height)
        x2 = _randint(0, width)
        y2 = _randint(0, height)
        color = _choice(colors)
        stroke_width = _uniform(1, 2.5)
        lines_svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width:.1f}" opacity="0.6"/>'

    curves_svg = ''
    for _ in range(3):
        cx1 = _randint(0, width)
        cy1 = _randint(0, height)
        cx2 = _randint(0, width)
        cy2 = _randint(0, height)
        x = _randint(0, width)
        y = _randint(0, height)
        color = _choice(colors)
        curves_svg += f'<path d="M0,{_randint(0,height)} C{cx1},{cy1} {cx2},{cy2} {x},{y}" stroke="{color}" stroke-width="1.5" fill="none" opacity="0.5"/>'

    dots_svg = ''
    for _ in range(50):
        cx = _randint(0, width)
        cy = _randint(0, height)
        r = _uniform(1, 3)
        color = _choice(colors)
        dots_svg += f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{color}" opacity="0.35"/>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{bg_color}" rx="6"/>
  {dots_svg}
  {lines_svg}
  {curves_svg}
  {chars_svg}
</svg>'''