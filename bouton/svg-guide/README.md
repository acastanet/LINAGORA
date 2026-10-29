# Boutons SVG du guide

Les dossiers `clair` et `sombre` contiennent chacun les huit états du visuel : repos, survol, écoute, écoute avec micro, désactivé, enregistrement, attention et erreur. Chaque fichier SVG est autonome, redimensionnable et doté d'un titre accessible. Les arcs représentent un instant fixe ; leur animation peut être ajoutée par l'application qui utilise les boutons.

Pour régénérer les fichiers après modification du dessin : `python bouton/svg-guide/generer.py`. Pour régénérer les bandes PNG utilisées par le bouton Windows : `python bouton/svg-guide/generer_images.py` (nécessite CairoSVG et Pillow pour la génération uniquement).

L'application sélectionne les bandes PNG dans `bouton/clair` ou `bouton/sombre` selon le thème des applications Windows. Le chargement affiche la bouche désactivée avec un arc gris ; la transcription affiche l'arc rouge tournant, et l'écoute avec microphone fait pulser l'anneau rouge.
