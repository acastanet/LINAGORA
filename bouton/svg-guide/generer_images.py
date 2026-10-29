"""Convertit les SVG du guide en bandes PNG pour le bouton Windows.

Nécessite CairoSVG et Pillow uniquement pour la génération, pas pour l'application.
"""
from io import BytesIO
from pathlib import Path
import math

import cairosvg
from PIL import Image

from generer import bouton

ROOT = Path(__file__).resolve().parent.parent
SIZE = 56


def render(svg):
    png = cairosvg.svg2png(bytestring=svg.encode('utf-8'), output_width=SIZE*4, output_height=SIZE*4)
    return Image.open(BytesIO(png)).convert('RGBA').resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def frames(theme):
    def image(etat):
        return render(bouton(theme, etat))

    ready = [image('repos'), image('survol'), image('ecoute')]
    result = {'ready': ready}
    for state, etat in (('recover', 'attention'), ('error', 'erreur')):
        im = image(etat)
        result[state] = [im, im, im]
    result['recording'] = []
    result['busy'] = []
    result['loading'] = []
    for i in range(16):
        opacity = .65 + .35 * (1 + math.cos(i * math.tau / 16)) / 2
        svg = bouton(theme, 'ecoute-micro').replace('stroke-dasharray="480 98"',
                                                      f'stroke-opacity="{opacity:.3f}" stroke-dasharray="480 98"')
        result['recording'].append(render(svg))
    for i in range(12):
        angle = -90 + i * 30
        svg = bouton(theme, 'enregistrement').replace('rotate(-90 100 100)', f'rotate({angle} 100 100)')
        result['busy'].append(render(svg))
        arc = (f'<circle cx="100" cy="100" r="92" fill="none" stroke="#90949b" '
               f'stroke-width="8" stroke-linecap="round" stroke-dasharray="125 453" '
               f'transform="rotate({angle} 100 100)"/>')
        result['loading'].append(render(bouton(theme, 'desactive').replace('</svg>', arc + '</svg>')))
    return result


if __name__ == '__main__':
    for theme in ('clair', 'sombre'):
        output = ROOT / theme
        output.mkdir(exist_ok=True)
        for state, images in frames(theme).items():
            strip = Image.new('RGBA', (SIZE, SIZE * len(images)))
            for i, image in enumerate(images):
                strip.paste(image, (0, SIZE*i))
            strip.save(output / f'{state}.png')
