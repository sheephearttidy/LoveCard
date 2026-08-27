import random
import string


_CHARS = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')


def generate_captcha_text(length=4):
    return ''.join(random.choices(_CHARS, k=length))


def generate_captcha_svg(text, width=120, height=40):
    colors = ['#e74c3c', '#e67e22', '#27ae60', '#2980b9', '#8e44ad', '#c0392b', '#16a085']
    bg_color = '#f0f0f0'
    char_color = random.choice(colors)

    chars_svg = ''
    char_width = width / (len(text) + 1)
    for i, ch in enumerate(text):
        x = char_width * (i + 0.7)
        y = height / 2 + random.randint(-6, 6)
        angle = random.randint(-20, 20)
        font_size = random.randint(18, 24)
        color = random.choice(colors)
        chars_svg += f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{font_size}" font-weight="bold" fill="{color}" text-anchor="middle" dominant-baseline="central" transform="rotate({angle},{x},{y})">{ch}</text>'

    lines_svg = ''
    for _ in range(4):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = random.choice(colors)
        lines_svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" opacity="0.5"/>'

    dots_svg = ''
    for _ in range(30):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        r = random.randint(1, 2)
        color = random.choice(colors)
        dots_svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.4"/>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{bg_color}" rx="6"/>
  {lines_svg}
  {dots_svg}
  {chars_svg}
</svg>'''