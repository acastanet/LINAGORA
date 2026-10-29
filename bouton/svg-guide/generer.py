"""Génère les boutons autonomes correspondant au guide visuel fourni."""
from pathlib import Path

DESTINATION = Path(__file__).resolve().parent
ETATS = {
    "repos": "Repos",
    "survol": "Survol",
    "ecoute": "Écoute",
    "ecoute-micro": "Écoute avec microphone",
    "desactive": "Désactivé",
    "enregistrement": "Enregistrement en cours",
    "attention": "Attention",
    "erreur": "Erreur",
}


def bouton(theme, etat):
    sombre = theme == "sombre"
    levres = {"desactive": "#bcbec0", "enregistrement": "#8c2440",
              "attention": "#df7200", "erreur": "#a00022"}.get(etat, "#ff172d")
    trait = "#760a19" if etat != "desactive" else "#77797c"
    ouvert = etat in {"ecoute", "ecoute-micro", "enregistrement", "attention", "erreur"}
    titre = ETATS[etat]
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200" role="img" aria-labelledby="titre">',
        f'  <title id="titre">{titre} — thème {theme}</title>',
        '  <defs><linearGradient id="bouche" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#08080c"/><stop offset="1" stop-color="#4a0010"/></linearGradient></defs>',
        f'  <path d="M 17 103 C 31 91 52 62 70 55 C 82 50 93 55 100 62 C 107 55 118 50 130 55 C 149 63 168 91 183 103 C 165 122 147 151 100 153 C 53 151 35 122 17 103 Z" fill="{levres}"/>',
    ]
    if ouvert:
        pieces += [
            '  <path d="M 17 103 C 43 98 58 84 76 82 C 87 81 93 84 100 84 C 107 84 113 81 124 82 C 142 84 157 98 183 103 C 154 112 138 127 100 127 C 62 127 46 112 17 103 Z" fill="url(#bouche)"/>',
            '  <path d="M 57 91 C 65 87 70 83 78 82 C 87 81 93 84 100 84 C 107 84 113 81 122 82 C 130 83 135 87 143 91 C 129 94 116 95 100 95 C 84 95 71 94 57 91 Z" fill="#fff"/>',
        ]
    elif etat == "survol":
        pieces.append('  <path d="M 17 103 C 45 102 58 94 79 96 C 88 97 94 99 100 99 C 106 99 112 97 121 96 C 142 94 155 102 183 103 C 154 107 139 120 100 120 C 61 120 46 107 17 103 Z" fill="#250008"/>')
    else:
        pieces.append(f'  <path d="M 17 103 C 42 105 55 100 73 102 C 86 104 93 109 100 109 C 107 109 114 104 127 102 C 145 100 158 105 183 103" fill="none" stroke="{trait}" stroke-width="4.5" stroke-linecap="round"/>')
    pieces.append('  <path d="M 59 72 C 64 67 69 64 75 64" fill="none" stroke="#fff" stroke-opacity=".62" stroke-width="6" stroke-linecap="round"/>')
    pieces.append('</svg>')
    return "\n".join(pieces) + "\n"


if __name__ == "__main__":
    for theme in ("clair", "sombre"):
        dossier = DESTINATION / theme
        dossier.mkdir(exist_ok=True)
        for etat in ETATS:
            (dossier / f"{etat}.svg").write_text(bouton(theme, etat), encoding="utf-8")
