# Test de LinTO STT français

Mini-interface locale pour [linto_stt_fr_fastconformer_pc](https://huggingface.co/linagora/linto_stt_fr_fastconformer_pc). Elle accepte un enregistrement au microphone ou un fichier audio et affiche la transcription ponctuée.

Dans l'onglet « Microphone », démarrez l'enregistrement puis arrêtez-le : le micro est aussitôt remis à zéro et la transcription démarre automatiquement. Les fichiers temporaires de Gradio sont nettoyés automatiquement après utilisation (avec un délai d'environ une à deux minutes). Dans l'onglet « Fichier audio », utilisez le bouton « Transcrire ».

La transcription peut être corrigée directement dans la zone de texte, puis copiée avec l'icône de copie située dans cette zone.

Double-cliquez sur `lancer.bat` ou lancez `py -3.11 app.py` dans ce dossier. Le lanceur utilise Python 3.11 du système, indépendamment du `python` éventuellement présent en premier dans le PATH. Ouvrez l'adresse locale affichée dans le terminal si le navigateur ne s'ouvre pas automatiquement. Le modèle est téléchargé depuis Hugging Face lors de la première transcription, puis réutilisé depuis le cache. Une connexion Internet est donc nécessaire au premier essai. CUDA est utilisé si PyTorch le détecte, sinon le calcul se fait sur le processeur.

Python 3.11 doit contenir Gradio, PyTorch, librosa, soundfile et Transformers 5 ou supérieur, comme indiqué sur la fiche du modèle. Le script ne crée pas d'environnement et n'installe rien.

Le modèle a été entraîné sur des extraits allant jusqu'à 30 secondes ; commencer par un extrait court est conseillé. La qualité peut varier, notamment pour les conversations avec des voix superposées.

## Dictée vocale dans Windows (POC)

Dans ce dossier, lancez `py -3.11 dictee.py` et attendez le message « Prêt ». Le modèle est chargé une seule fois au démarrage, sur CUDA si disponible. Réduisez la console, cliquez dans une zone de texte, puis appuyez sur **Ctrl+Alt+Espace** pour démarrer l'enregistrement. Parlez, puis appuyez à nouveau sur **Ctrl+Alt+Espace** pour l'arrêter. La transcription est insérée à la position du curseur après traitement. Les bips et la console indiquent les étapes ; fermez la console ou utilisez Ctrl+C pour arrêter le script.

Vous pouvez aussi double-cliquer sur `lancer-dictee.bat` : il arrête les instances précédentes de ce script avant de le relancer. Ce lanceur utilise `psutil`, déjà présent dans l'environnement Python 3.11.

Le script utilise le microphone par défaut de Windows et nécessite `sounddevice` dans le Python 3.11 existant (`py -3.11 -m pip install sounddevice` si nécessaire), en plus des dépendances de l'application ci-dessus. L'insertion utilise SendInput en Unicode, sans presse-papiers. Gardez la même fenêtre et le curseur au même endroit jusqu'à la fin : si la fenêtre active a changé, le texte est affiché dans la console au lieu d'être inséré. Les applications lancées en administrateur peuvent refuser les entrées d'un script lancé sans ces droits. Si le raccourci est déjà utilisé, Windows refusera son enregistrement.
