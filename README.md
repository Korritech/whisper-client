# whisper-client

Client de dictée vocale qui s'appuie sur le serveur [whisper-flow](../whisper-flow).
Le serveur transcrit l'audio en streaming ; ce client capture le micro, envoie l'audio au serveur
et injecte le texte dans l'application qui a le focus.

## Prérequis

- Le serveur whisper-flow lancé : `./run.sh -run-server` (port 8181)
- PortAudio : `brew install portaudio`
- Sur macOS, donner l'accès **Accessibilité** et **Surveillance de l'entrée** au terminal
  (Réglages Système → Confidentialité et sécurité)

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```
