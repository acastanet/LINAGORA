"""Dessin du bouton de dictée et de l'icône : bouche rouge sur disque tricolore.

Exécuté directement (Pillow nécessaire), régénère les anciennes images et SVG
dans `archives/boutons-historiques`, ainsi que les icônes du logiciel.
"""
from math import ceil
from pathlib import Path
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageOps

# Repère des brouillons bouton-stt-*.svg : 256 unités ; chaque segment est une Bézier cubique.
LIPS = ((18, 122), (
    (48, 125, 63, 80, 99, 80),
    (111, 80, 122, 87, 128, 94),
    (135, 85, 146, 80, 158, 80),
    (193, 80, 208, 125, 238, 122),
    (210, 140, 190, 183, 128, 183),
    (67, 183, 47, 140, 18, 122),
))
MOUTH = ((18, 122), (
    (39, 131, 53, 122, 78, 128),
    (99, 132, 111, 137, 128, 137),
    (145, 137, 157, 132, 178, 128),
    (203, 122, 217, 131, 238, 122),
))
# Bouche ouverte : lèvres écartées, gorge noire et rangée de dents sous la lèvre du haut.
LIPS_OPEN = ((18, 124), (
    (46, 120, 62, 70, 99, 70),
    (111, 70, 122, 77, 128, 84),
    (134, 77, 145, 70, 157, 70),
    (194, 70, 210, 120, 238, 124),
    (212, 150, 190, 198, 128, 198),
    (66, 198, 44, 150, 18, 124),
))
INSIDE_OPEN = ((32, 124), (
    (60, 112, 90, 104, 128, 108),
    (166, 104, 196, 112, 224, 124),
    (196, 150, 166, 166, 128, 166),
    (90, 166, 60, 150, 32, 124),
))
TEETH_OPEN = ((32, 124), (
    (60, 112, 90, 104, 128, 108),
    (166, 104, 196, 112, 224, 124),
    (196, 124, 164, 128, 128, 128),
    (92, 128, 60, 124, 32, 124),
))
# Bouche entrouverte : fente avec un filet de dents (erreur) ou sans (attention).
INSIDE_AJAR = ((26, 123), (
    (56, 118, 92, 112, 128, 118),
    (164, 112, 200, 118, 230, 123),
    (200, 134, 164, 144, 128, 144),
    (92, 144, 56, 134, 26, 123),
))
TEETH_AJAR = ((26, 123), (
    (56, 118, 92, 112, 128, 118),
    (164, 112, 200, 118, 230, 123),
    (200, 124, 164, 126, 128, 128),
    (92, 126, 56, 124, 26, 123),
))
INSIDE_SLIT = ((26, 123), (
    (56, 122, 92, 126, 128, 128),
    (164, 126, 200, 122, 230, 123),
    (200, 130, 164, 140, 128, 140),
    (92, 140, 56, 130, 26, 123),
))
# Reflets : ellipses (cx, cy, rx, ry) sur la lèvre du bas puis sur les deux bosses du haut.
GLOSS_CLOSED = ((128, 162, 30, 6), (96, 93, 14, 5), (160, 93, 14, 5))
GLOSS_OPEN = ((128, 183, 26, 5), (96, 81, 14, 4), (160, 81, 14, 4))
MOUTHS = {
    'closed': dict(lips=LIPS, line=MOUTH, gloss=GLOSS_CLOSED),
    'open': dict(lips=LIPS_OPEN, inside=INSIDE_OPEN, teeth=TEETH_OPEN, gloss=GLOSS_OPEN),
    'ajar': dict(lips=LIPS, inside=INSIDE_AJAR, teeth=TEETH_AJAR, gloss=GLOSS_CLOSED),
    'slit': dict(lips=LIPS, inside=INSIDE_SLIT, gloss=GLOSS_CLOSED),
}
MIC_SCALE = .82  # le micro est réduit autour du haut de sa capsule (128, 138)…
MIC_TOP = 150    # …placé au bas de la bouche ouverte, il déborde sur la lèvre inférieure
MIC_SVG = ('<g fill="#080808" stroke="#FFFFFF" stroke-width="2.4" stroke-linejoin="round" '
           f'transform="translate(128 {MIC_TOP}) scale({MIC_SCALE}) translate(-128 -138)">'
           '<rect x="112" y="138" width="32" height="55" rx="16"/>'
           '<path d="M102 168 A4 4 0 0 1 106 172 V180 A22 22 0 0 0 150 180 V172 A4 4 0 0 1 158 172 '
           'V180 A30 30 0 0 1 132 209.73 V219 H141 A4 4 0 0 1 141 227 H115 A4 4 0 0 1 115 219 '
           'H124 V209.73 A30 30 0 0 1 98 180 V172 A4 4 0 0 1 102 168 Z"/></g>')
# Hauteur du repère placée au centre du disque : la bouche ne bouge pas d'un état à l'autre.
ART_CENTER_Y = 134

BLUE = '#1F45B5'
WHITE = '#FFFFFF'
FLAG_RED = '#E4262F'
RED = '#E8303A'
LIP_TOP = '#F4464F'
LIP_BOTTOM = '#C8142A'
INK = '#1A0508'
THROAT = '#140608'
MIC = '#080808'
BORDER = (255, 255, 255, 150)
HOVER = (161, 161, 170, 220)
GREY = '#A1A1AA'
GREY_TOP = '#F4F4F5'
GREY_BOTTOM = '#D4D4D8'
AMBER = '#F07A0A'
DARK_RED = '#D7142B'

S = 8  # suréchantillonnage avant réduction
BUTTON = 56
CENTER = (28, 27.5)  # la marge du bas reçoit l'ombre
RADIUS = 22
# Normal, survol, appui : bordure, ombre (décalage, flou, opacité) et bouche.
VARIANTS = (
    dict(border=BORDER, shadow=(1.5, 2.0, 70)),
    dict(border=HOVER, border_width=1.6, shadow=(2.2, 2.8, 95)),
    dict(border=HOVER, shadow=(.6, 1.0, 60), pressed=True, mouth='open'),
)


def points(shape, steps=20):
    """Échantillonne les Bézier pour Pillow."""
    start, curves = shape
    result = [start]
    for x1, y1, x2, y2, x3, y3 in curves:
        x0, y0 = start
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            result.append((u**3*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t**3*x3,
                           u**3*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t**3*y3))
        start = (x3, y3)
    return result


def svg_path(shape, closed=True):
    start, curves = shape
    return f'M {start[0]} {start[1]} ' + ' '.join(
        'C ' + ' '.join(str(n) for n in curve) for curve in curves) + (' Z' if closed else '')


def art_scale(radius):
    # Les lèvres (220 unités de large) couvrent 95 % du diamètre.
    return .95 * 2 * radius / 220


def mix(color, other, t):
    a, b = ImageColor.getrgb(color), ImageColor.getrgb(other)
    return '#' + ''.join(f'{round(x + (y-x)*t):02X}' for x, y in zip(a, b))


def fill(image, color, mask):
    layer = Image.new('RGBA', image.size, color)
    layer.putalpha(mask)
    image.alpha_composite(layer)


def draw_mic(draw, f):
    def box(x0, y0, x1, y1):
        return ((128 + (x0-128)*MIC_SCALE)*f, (MIC_TOP + (y0-138)*MIC_SCALE)*f,
                (128 + (x1-128)*MIC_SCALE)*f, (MIC_TOP + (y1-138)*MIC_SCALE)*f)
    k = MIC_SCALE * f
    draw.rounded_rectangle(box(112, 138, 144, 193), radius=16*k, fill=255)
    draw.arc(box(98, 150, 158, 210), 0, 180, fill=255, width=round(8*k))
    for x in (98, 150):
        draw.rectangle(box(x, 172, x+8, 181), fill=255)
        draw.ellipse(box(x, 168, x+8, 176), fill=255)
    draw.rectangle(box(124, 205, 132, 220), fill=255)
    draw.rounded_rectangle(box(111, 219, 145, 227), radius=4*k, fill=255)


def draw_art(f, mouth='closed', mic=False, grey=False):
    """Bouche (et micro) à f pixels par unité du repère 256."""
    shapes = MOUTHS[mouth]
    side = ceil(256 * f)
    image = Image.new('RGBA', (side, side))
    scaled = lambda shape: [(x*f, y*f) for x, y in points(shape, 48)]
    lips = scaled(shapes['lips'])
    top, bottom, ink = (GREY_TOP, GREY_BOTTOM, GREY) if grey else (LIP_TOP, LIP_BOTTOM, INK)
    # Lèvres en dégradé, plus claires en haut, puis reflets flous.
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).polygon(lips, fill=255)
    shade = ImageOps.colorize(Image.linear_gradient('L').resize(image.size), top, bottom,
                              blackpoint=80, whitepoint=190).convert('RGBA')
    shade.putalpha(mask)
    image.alpha_composite(shade)
    gloss = Image.new('L', image.size)
    for x, y, rx, ry in shapes['gloss']:
        ImageDraw.Draw(gloss).ellipse(((x-rx)*f, (y-ry)*f, (x+rx)*f, (y+ry)*f), fill=150)
    fill(image, WHITE, ImageChops.multiply(gloss.filter(ImageFilter.GaussianBlur(3*f)), mask))
    draw = ImageDraw.Draw(image)
    # Les traits fins des brouillons gardent au moins 0,7 pixel une fois réduits.
    if 'inside' in shapes:
        inside = scaled(shapes['inside'])
        draw.polygon(inside, fill=GREY if grey else THROAT)
        if 'teeth' in shapes:
            draw.polygon(scaled(shapes['teeth']), fill=WHITE)
        draw.line(inside + inside[:1], fill=ink, width=round(max(2*f, .5*S)), joint='curve')
    else:
        draw.line(scaled(shapes['line']), fill=ink, width=round(max(2.6*f, .6*S)), joint='curve')
    draw.line(lips + lips[:1], fill=ink, width=round(max(3.1*f, .7*S)), joint='curve')
    if mic:
        mask = Image.new('L', image.size)
        draw_mic(ImageDraw.Draw(mask), f)
        outline = 2*round(max(1.2*f, .8*S)) + 1
        fill(image, WHITE, mask.filter(ImageFilter.MaxFilter(outline)))
        fill(image, MIC, mask)
    return image


def draw_flag(side, faded=False, pressed=False):
    """Disque tricolore de `side` pixels, éclairé par le haut (par le bas s'il est enfoncé)."""
    colors = [mix(c, WHITE, .55) if faded else c for c in (BLUE, WHITE, FLAG_RED)]
    face = Image.new('RGBA', (side, side), colors[1])
    draw = ImageDraw.Draw(face)
    draw.rectangle((0, 0, side/3, side), fill=colors[0])
    draw.rectangle((2*side/3, 0, side, side), fill=colors[2])
    light = Image.linear_gradient('L').resize((side, side))
    if pressed:
        light = ImageOps.flip(light)
    fill(face, WHITE, light.point(lambda v: round(max(0, 128 - v) * .6)))
    fill(face, '#000000', light.point(lambda v: round(max(0, v - 128) * .35)))
    mask = Image.new('L', (side, side))
    ImageDraw.Draw(mask).ellipse((0, 0, side-1, side-1), fill=255)
    face.putalpha(mask)
    return face


def draw_button(size=BUTTON, *, mouth='closed', mic=False, grey=False, border=BORDER,
                shadow=(1.5, 2.0, 70), pressed=False, ring=None, halo=None, arc=None, badge=None,
                center=CENTER, radius=RADIUS, border_width=1.0):
    """Bouton de `size` pixels ; les cotes sont exprimées pour un bouton de 56."""
    k = size * S / BUTTON
    image = Image.new('RGBA', (size*S, size*S))
    cx, cy, r = center[0]*k, (center[1] + (1 if pressed else 0))*k, radius*k

    def disc(extra=0, dy=0):
        return (cx-r-extra*k, cy+dy*k-r-extra*k, cx+r+extra*k, cy+dy*k+r+extra*k)

    if halo is not None:
        # Pulsation : un halo rouge s'élargit en s'estompant (halo de 0 à 1).
        mask = Image.new('L', image.size)
        ImageDraw.Draw(mask).ellipse(disc(1.5 + 3*halo), fill=round(110*(1-halo)))
        fill(image, RED, mask.filter(ImageFilter.GaussianBlur(.8*k)))
    if shadow:
        dy, blur, alpha = shadow
        mask = Image.new('L', image.size)
        ImageDraw.Draw(mask).ellipse(disc(0, dy), fill=alpha)
        fill(image, '#000000', mask.filter(ImageFilter.GaussianBlur(blur*k)))
    image.alpha_composite(draw_flag(round(2*r), grey, pressed), (round(cx-r), round(cy-r)))
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).ellipse(disc(), outline=border[3], width=round(border_width*k))
    fill(image, border[:3], mask)
    f = art_scale(radius) * k
    image.alpha_composite(draw_art(f, mouth, mic, grey), (round(cx-128*f), round(cy-ART_CENTER_Y*f)))
    draw = ImageDraw.Draw(image)
    if ring:
        draw.ellipse(disc(1), outline=ring, width=round(2.2*k))
    if arc:
        start, color = arc
        draw.arc(disc(1), start, start+100, fill=color, width=round(2.2*k))
    if badge:
        bx, by, br = cx + .72*r, cy - .72*r, 7.5*k
        draw.ellipse((bx-br-1.2*k, by-br-1.2*k, bx+br+1.2*k, by+br+1.2*k), fill=WHITE)
        draw.ellipse((bx-br, by-br, bx+br, by+br), fill=badge)
        draw.rounded_rectangle((bx-.15*br, by-.62*br, bx+.15*br, by+.18*br), radius=.15*br, fill=WHITE)
        draw.ellipse((bx-.17*br, by+.32*br, bx+.17*br, by+.66*br), fill=WHITE)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def button_frames():
    """Images de chaque état : normal/survol/appui, ou animation."""
    static = {'ready': {}, 'recover': {'badge': AMBER, 'mouth': 'slit'},
              'error': {'badge': DARK_RED, 'mouth': 'ajar'}}
    frames = {name: [draw_button(**{**options, **variant}) for variant in VARIANTS]
              for name, options in static.items()}
    frames['recording'] = [draw_button(mouth='open', mic=True, ring=RED, halo=i/16) for i in range(16)]
    frames['loading'] = [draw_button(grey=True, arc=(30*i - 90, GREY)) for i in range(12)]
    frames['busy'] = [draw_button(mouth='open', arc=(30*i - 90, RED)) for i in range(12)]
    return frames


def icon(size):
    return draw_button(size, shadow=None, center=(28, 28), radius=27,
                       border_width=max(1, BUTTON/size))


def svg(view, center, radius, title, mouth='closed', mic=False, shadow=False, stroke=BORDER,
        stroke_width=1):
    f = art_scale(radius)
    x, y = center
    n = lambda v: f'{v:.4g}'
    shapes = MOUTHS[mouth]
    effect = target = ''
    if shadow:
        effect = ('\n    <filter id="ombre" x="-20%" y="-20%" width="140%" height="150%">'
                  '<feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#000000" flood-opacity=".27"/></filter>')
        target = ' filter="url(#ombre)"'
    if isinstance(stroke, tuple):
        stroke = '#{:02X}{:02X}{:02X}" stroke-opacity="{:.2g}'.format(*stroke[:3], stroke[3]/255)
    third = 2*radius/3
    inside = []
    if 'inside' in shapes:
        inside.append(f'    <path d="{svg_path(shapes["inside"])}" fill="{THROAT}" stroke="{INK}" '
                      'stroke-width="2" stroke-linejoin="round"/>')
        if 'teeth' in shapes:
            inside.append(f'    <path d="{svg_path(shapes["teeth"])}" fill="{WHITE}"/>')
    else:
        inside.append(f'    <path d="{svg_path(shapes["line"], closed=False)}" fill="none" stroke="{INK}" '
                      'stroke-width="2.6" stroke-linecap="round"/>')
    gloss = [f'<ellipse cx="{gx}" cy="{gy}" rx="{rx}" ry="{ry}"/>' for gx, gy, rx, ry in shapes['gloss']]
    return '\n'.join((
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{view}" height="{view}" viewBox="0 0 {view} {view}" '
        'role="img" aria-labelledby="titre">',
        f'  <title id="titre">{title}</title>',
        '  <defs>',
        f'    <clipPath id="disque"><circle cx="{x}" cy="{y}" r="{radius}"/></clipPath>',
        '    <linearGradient id="relief" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" '
        'stop-opacity=".3"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" '
        'stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".17"/>'
        '</linearGradient>',
        f'    <linearGradient id="levres" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{LIP_TOP}"/>'
        f'<stop offset="1" stop-color="{LIP_BOTTOM}"/></linearGradient>',
        f'    <filter id="flou"><feGaussianBlur stdDeviation="3"/></filter>{effect}',
        '  </defs>',
        f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="{WHITE}"{target}/>',
        '  <g clip-path="url(#disque)">',
        f'    <rect x="{n(x-radius)}" y="{n(y-radius)}" width="{n(third)}" height="{2*radius}" fill="{BLUE}"/>',
        f'    <rect x="{n(x-radius+2*third)}" y="{n(y-radius)}" width="{n(third)}" height="{2*radius}" '
        f'fill="{FLAG_RED}"/>',
        f'    <rect x="{n(x-radius)}" y="{n(y-radius)}" width="{2*radius}" height="{2*radius}" fill="url(#relief)"/>',
        '  </g>',
        f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>',
        f'  <g transform="translate({n(x-128*f)} {n(y-ART_CENTER_Y*f)}) scale({n(f)})">',
        f'    <path d="{svg_path(shapes["lips"])}" fill="url(#levres)"/>',
        f'    <g fill="#FFFFFF" fill-opacity=".6" filter="url(#flou)">{"".join(gloss)}</g>',
        *inside,
        f'    <path d="{svg_path(shapes["lips"])}" fill="none" stroke="{INK}" stroke-width="3.1" '
        'stroke-linejoin="round"/>',
        *(['    ' + MIC_SVG] if mic else []),
        '  </g>',
        '</svg>',
        ''))


def preview(frames, zoom=2):
    """Planche de tous les états, sur fond clair puis sombre, dans l'ordre de la maquette."""
    picks = [*frames['ready'], frames['recording'][0], frames['loading'][0], frames['busy'][3],
             frames['recover'][0], frames['error'][0]]
    cell = BUTTON*zoom + 16
    sheet = Image.new('RGBA', (len(picks)*cell + 16, 2*cell))
    draw = ImageDraw.Draw(sheet)
    for row, background in enumerate(('#F4F4F5', '#18181B')):
        draw.rectangle((0, row*cell, sheet.width, (row+1)*cell), fill=background)
        for i, frame in enumerate(picks):
            large = frame.resize((BUTTON*zoom, BUTTON*zoom), Image.Resampling.LANCZOS)
            sheet.alpha_composite(large, (16 + i*cell, row*cell + 8))
    return sheet


if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    output = folder / 'archives' / 'boutons-historiques'
    output.mkdir(parents=True, exist_ok=True)
    frames = button_frames()
    for name, images in frames.items():
        strip = Image.new('RGBA', (BUTTON, BUTTON*len(images)))
        for i, image in enumerate(images):
            strip.paste(image, (0, i*BUTTON))
        strip.save(output / f'{name}.png')
    (output / 'ready.svg').write_text(
        svg(BUTTON, CENTER, RADIUS, 'Dictée LinTO — prête', shadow=True), encoding='utf-8', newline='\n')
    (output / 'recording.svg').write_text(
        svg(BUTTON, CENTER, RADIUS, 'Dictée LinTO — enregistrement', mouth='open', mic=True, shadow=True,
            stroke=RED, stroke_width=2.2), encoding='utf-8', newline='\n')
    (folder / 'dictee.svg').write_text(
        svg(128, (64, 64), 61, 'Dictée LinTO — Bouche en cœur', stroke_width=2), encoding='utf-8', newline='\n')
    preview(frames).save(output / 'bouton-dictee.png')
    icon(256).save(folder / 'dictee.png')
    sizes = (16, 20, 24, 32, 48, 64, 128, 256)
    icon(256).save(folder / 'bouche-en-coeur.ico', format='ICO', sizes=[(s, s) for s in sizes],
                   append_images=[icon(s) for s in sizes[:-1]])
