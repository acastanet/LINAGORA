# Test de LinTO STT français

Mini-interface locale pour [linto_stt_fr_fastconformer_pc](https://huggingface.co/linagora/linto_stt_fr_fastconformer_pc). Elle accepte un enregistrement au microphone ou un fichier audio et affiche la transcription ponctuée.

Dans l'onglet « Microphone », démarrez l'enregistrement puis arrêtez-le : le micro est aussitôt remis à zéro et la transcription démarre automatiquement. Les fichiers temporaires de Gradio sont nettoyés automatiquement après utilisation (avec un délai d'environ une à deux minutes). Dans l'onglet « Fichier audio », utilisez le bouton « Transcrire ».

La transcription peut être corrigée directement dans la zone de texte, puis copiée avec l'icône de copie située dans cette zone.

Double-cliquez sur `lancer.bat` ou lancez `py -3.11 app.py` dans ce dossier. Le lanceur utilise Python 3.11 du système, indépendamment du `python` éventuellement présent en premier dans le PATH. Ouvrez l'adresse locale affichée dans le terminal si le navigateur ne s'ouvre pas automatiquement. Le modèle est téléchargé depuis Hugging Face lors de la première transcription, puis réutilisé depuis le cache. Une connexion Internet est donc nécessaire au premier essai. CUDA est utilisé si PyTorch le détecte, sinon le calcul se fait sur le processeur.

Python 3.11 doit contenir Gradio, PyTorch, librosa, soundfile et Transformers 5 ou supérieur, comme indiqué sur la fiche du modèle. Le script ne crée pas d'environnement et n'installe rien.

Le modèle a été entraîné sur des extraits allant jusqu'à 30 secondes ; commencer par un extrait court est conseillé. La qualité peut varier, notamment pour les conversations avec des voix superposées.

## Dictée vocale dans Windows

Double-cliquez sur **Dictee-LinTO.exe** : un bouton flottant rond de 56 × 56 pixels apparaît sans console noire. Il présente une bouche rouge sur un disque clair ou sombre, selon le thème des applications Windows. La bouche s'entrouvre au survol et s'ouvre à l'appui. Le modèle est chargé en arrière-plan une seule fois : la bouche est grisée et un arc gris tourne autour du bouton, puis les couleurs reviennent quand la dictée est prête. Ce lanceur local requiert Python 3.11 et les dépendances du logiciel déjà installées ; les anciens lanceurs restent utilisables.

1. Placez le curseur dans votre document ou votre champ de texte.
2. Cliquez sur la bouche : elle s'ouvre, un micro apparaît en bas et un anneau rouge pulse tant que le micro enregistre.
3. Cliquez à nouveau : la bouche reste ouverte et un arc rouge tourne pendant la transcription. Le texte est inséré automatiquement, puis la bouche se referme.

Le bouton reste au-dessus des fenêtres sans prendre leur focus. Déplacez-le par un glissement depuis n'importe quel point. **Ctrl+Alt+Espace** permet aussi de démarrer et arrêter. Un clic droit sur le bouton ou sur l'icône bouche près de l'horloge permet de lire l'état détaillé, copier la dernière transcription ou quitter. Windows peut placer cette icône dans les icônes masquées.

Les notifications jouent un do central doux (261,63 Hz), en PCM stéréo 48 kHz / 24 bits, avec une attaque et une extinction progressives. Le fichier `sons/do-doux.wav` est généré par `son_dictee.py` et inclus dans la version portable.

Si vous changez de fenêtre pendant la transcription, une pastille orange **!** apparaît : cliquez sur la bouche pour copier le résultat, puis collez-le vous-même dans votre document. Le clic droit précise **Texte à copier** ou **Réessayer** en cas d'erreur (pastille rouge) ; dans ce dernier cas, cliquez sur la bouche pour afficher le détail puis réessayer. La copie est également accessible par clic droit après une erreur d'insertion. Les diagnostics sont disponibles dans `donnees/dictee.log` et `donnees/dictee-console.log` ; la dernière transcription est gardée en mémoire, sans historique écrit par l'application.

Un nouveau lancement conserve l'instance et le modèle déjà ouverts. Pour passer de l'ancienne version en console à cette version, fermez l'ancienne console avant le premier lancement. Si Ctrl+Alt+Espace est occupé par une autre application, le bouton reste utilisable.

Vous pouvez créer sur votre Bureau un raccourci vers **Dictee-LinTO.exe** ; il reste lié à ce dossier, qui doit conserver son emplacement. Le démarrage automatique avec Windows n'est pas activé.

Les SVG du nouveau bouton sont dans `bouton/svg-guide` ; `bouton/svg-guide/generer_images.py` les rend sous forme de bandes PNG dans `bouton/clair` et `bouton/sombre`. Chaque bande contient des images de 56 × 56 : normal, survol et appui, ou étapes d'animation. La génération demande CairoSVG et Pillow ; l'application lit les PNG avec GDI+ et les affiche en transparence par pixel (`affichage_bouton.py`), sans nouvelle dépendance. L'icône Windows près de l'horloge et de `Dictee.exe` reste la bouche sur disque tricolore, dans `bouche-en-coeur.ico` ; `icone_dictee.py` permet toujours de régénérer cette icône et les anciennes ressources dans `archives/boutons-historiques`.

Python 3.11 et les dépendances existantes restent nécessaires (`sounddevice`, `numpy`, `psutil` et celles de l'application ci-dessus). L'interface utilise Tkinter et les API Windows, sans nouvelle dépendance Python. Le lanceur cherche d'abord Python dans `%LOCALAPPDATA%\Programs\Python\Python311`, puis utilise le lanceur `py -3.11` pour le trouver.

Le microphone par défaut de Windows est utilisé. L'insertion utilise SendInput en Unicode, sans presse-papiers (sauf copie explicite). Gardez le curseur au même endroit jusqu'à la fin et évitez de taper pendant l'insertion. Les applications lancées en administrateur peuvent refuser les entrées d'un script lancé sans ces droits.

Vérifications : `py -3.11 -m unittest test_dictee_windows -v` (Windows). `py -3.11 dictee_windows.py --preview` ouvre uniquement l'interface sans charger le modèle ni enregistrer de son.

## Version portable Windows x64

Le ZIP `release/Dictee-LinTO-Windows-x64-CPU-portable.zip` contient le dossier complet, l'exécutable, Python, les bibliothèques CPU et le modèle. Décompressez le ZIP entier dans un dossier accessible en écriture, puis lancez **Dictee.exe**. Conservez ses dossiers `_internal`, `modele` et `donnees` à côté. Le dossier entier peut être déplacé ; aucun Python installé ni aucune connexion réseau ne sont nécessaires à l'utilisation. La vitesse dépend du processeur du PC destinataire.

Le ZIP `release/Dictee-LinTO-Windows-x64-GPU-light.zip` contient le logiciel, un petit lanceur exécutable et le modèle, sans bibliothèques GPU. Il requiert sur le PC Python 3.11 64 bits, son lanceur `py` si Python n'est pas installé à l'emplacement usuel, les dépendances du logiciel déjà installées pour ce Python, une carte NVIDIA et PyTorch avec CUDA fonctionnel. Après extraction, lancez **Dictee-GPU.exe**. Cette version utilise obligatoirement le GPU et ne télécharge rien ; en cas de problème, lancez **Diagnostic-GPU.bat**. Son `LIRE-MOI.txt` détaille les prérequis.

Le moteur partagé est dans `moteur_dictee.py` : il n'importe pas Gradio. En mode portable CPU, il impose le modèle local, le fonctionnement hors ligne et le calcul sur processeur. Le lanceur GPU light impose le modèle local et CUDA. Le lancement Python ordinaire conserve le choix automatique CUDA/CPU. Si le dossier `modele` est présent dans le projet source, celui-ci est également réutilisé hors ligne.

Pour reconstruire sous Windows avec Python 3.11 x64 :

```powershell
py -3.11 -m venv .venv-portable
.\.venv-portable\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv-portable\Scripts\python.exe -m pip install -r requirements-portable.txt
.\.venv-portable\Scripts\python.exe construire_portable.py --model-source .\modele
```

Le dossier modèle doit contenir les six fichiers de la révision `b37566382e88e99f8625450081c3420d4e1a0c4b` du dépôt Hugging Face, ainsi que son attribution. Le script génère le dossier `dist/Dictee-LinTO-CPU`, le ZIP, son empreinte SHA-256 et la liste exacte des versions `requirements-portable.lock.txt`. La configuration PyInstaller est dans `Dictee.spec`. Les modèles et dépendances sont ignorés par Git.

Pour construire l'édition GPU light : `.\.venv-portable\Scripts\python.exe construire_gpu_light.py --model-source .\modele`. La construction du lanceur nécessite PyInstaller ; l'édition produite ne modifie pas l'environnement Python du destinataire.

Validation du paquet : `Dictee.exe --verifier-interface`, puis `Dictee.exe --diagnostic --audio chemin-vers-un-fichier.wav`. Pour contrôler le ZIP après extraction isolée : `.\.venv-portable\Scripts\python.exe verifier_portable.py --audio chemin-vers-un-fichier.wav`. Le diagnostic audio bloque les connexions réseau du processus et écrit son rapport dans `donnees/diagnostic.json`. Ces diagnostics ne font pas partie du ZIP de distribution. La distribution doit aussi être essayée sur les PC Windows x64 destinataires ; le test local ne remplace pas cet essai.

## Archives locales

Les anciens dessins et outils historiques sont conservés dans `archives`. Les anciens ZIP et leurs empreintes sont rangés dans `release/archives`. Les journaux, raccourcis propres à la machine et fichiers d'essai sont conservés dans `archives/local`, qui reste hors Git. Les modèles, paquets portables et données personnelles restent également hors Git.
