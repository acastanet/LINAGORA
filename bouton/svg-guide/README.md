# Boutons SVG du guide

Les dossiers `clair` et `sombre` contiennent chacun les huit états du visuel : repos, survol, écoute, écoute avec micro, désactivé, enregistrement, attention et erreur. Chaque fichier SVG est autonome, redimensionnable et doté d'un titre accessible. Les illustrations montrent la bouche sur fond transparent, sans disque ni anneau.

Pour régénérer les fichiers après modification du dessin : `python bouton/svg-guide/generer.py`. Pour régénérer les bandes PNG utilisées par le bouton Windows : `python bouton/svg-guide/generer_images.py` (nécessite CairoSVG et Pillow pour la génération uniquement).

L'application sélectionne les bandes PNG dans `bouton/clair` ou `bouton/sombre` selon le thème des applications Windows. Le chargement affiche une bouche grise pulsante ; l’écoute fait pulser la bouche rouge et la transcription la bouche bordeaux. L’orange signale un texte à récupérer et le rouge foncé une erreur.
