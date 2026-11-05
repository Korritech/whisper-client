# whisper-client

Dictée vocale locale pour macOS, dans n'importe quelle application. Tu maintiens **Option droite**
pour parler, et le texte est collé là où se trouve ton curseur au relâchement.

La transcription tourne sur ta machine avec le serveur [whisper-flow](https://github.com/dimastatz/whisper-flow) :
aucune donnée ne part sur Internet. Le client démarre et arrête ce serveur lui-même, et affiche son état dans
la barre de menus.

## Installation

Prérequis :

- macOS
- un accès à ce dépôt GitHub (il est privé)
- [Homebrew](https://brew.sh)
- les outils Xcode : `xcode-select --install`
- Python 3.12 ou 3.11 : `brew install python@3.12`

```bash
git clone https://github.com/Korritech/whisper-client.git
cd whisper-client
./install.sh
```

Le script installe PortAudio, clone `whisper-flow` à côté de `whisper-client`, crée les deux
environnements Python et télécharge le modèle Whisper `small` (environ 480 Mo). Compte quelques
minutes, surtout à cause de `torch`. Tu peux le relancer sans risque : il passe les étapes déjà faites.

Pour placer `whisper-flow` ailleurs, définis `WHISPER_FLOW_DIR` avant d'installer et de lancer.

### Permissions macOS

Cette étape ne peut pas être automatisée. Dans **Réglages Système → Confidentialité et sécurité**,
autorise ton app de terminal (Terminal, iTerm, VS Code...) dans :

- **Micro**
- **Accessibilité**
- **Surveillance de l'entrée**

Puis quitte complètement le terminal (Cmd+Q) et rouvre-le. Sans ces permissions, l'outil ne réagit
pas à la touche, sans afficher d'erreur.

## Utilisation

```bash
cd whisper-client
.venv/bin/python -m whisper_client
```

| Pastille | État |
|---|---|
| ⚪ | Le serveur démarre (chargement du modèle) |
| 🟢 | Prêt |
| 🔴 | Enregistrement en cours |
| 🟠 | Transcription |
| ⚠️ | Échec de la dernière dictée |

- Maintiens **Option droite** pendant que tu parles, puis relâche : le texte est collé dans l'app active.
- Un appui très bref est ignoré.
- Ton presse-papiers est restauré après le collage (texte uniquement).
- Pour arrêter : clic sur la pastille, puis **Quitter**. Le serveur s'arrête avec le client.

Réglages (modèle, langue, vocabulaire) : [whisper_client/config.py](whisper_client/config.py).
Pour plus de détails dans le terminal : `LOG_LEVEL=DEBUG .venv/bin/python -m whisper_client`.

## Développement

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest tests
```
