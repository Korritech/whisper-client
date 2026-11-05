#!/usr/bin/env bash
# Installs whisper-client and the whisper-flow server it drives, on macOS.
# Safe to run again: every step skips what is already in place.
set -euo pipefail

CLIENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="${WHISPER_FLOW_DIR:-$(dirname "$CLIENT_DIR")/whisper-flow}"
SERVER_REPO="https://github.com/dimastatz/whisper-flow.git"
SERVER_REF="${WHISPER_FLOW_REF:-b5d8ede}"   # the server commit this client was tested with
MODEL="small"

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[31mErreur : %s\033[0m\n' "$*" >&2; exit 1; }

step "Vérification du système"
[[ "$(uname)" == "Darwin" ]] || fail "ce programme ne fonctionne que sur macOS."
xcode-select -p >/dev/null 2>&1 \
    || fail "outils Xcode absents. Lance : xcode-select --install, puis relance ce script."
command -v brew >/dev/null 2>&1 \
    || fail "Homebrew absent. Installe-le depuis https://brew.sh, puis relance ce script."

PYTHON=""
for candidate in python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done
[[ -n "$PYTHON" ]] || fail "Python 3.12 ou 3.11 introuvable. Lance : brew install python@3.12"
echo "Python : $(command -v "$PYTHON") ($("$PYTHON" --version))"

step "PortAudio (micro)"
brew list portaudio >/dev/null 2>&1 || brew install portaudio

step "Serveur whisper-flow : $SERVER_DIR"
if [[ ! -d "$SERVER_DIR/.git" ]]; then
    git clone "$SERVER_REPO" "$SERVER_DIR"
    git -C "$SERVER_DIR" checkout --quiet "$SERVER_REF"
else
    echo "Déjà cloné, je n'y touche pas."
fi

if [[ ! -x "$SERVER_DIR/.venv/bin/python" ]]; then
    "$PYTHON" -m venv "$SERVER_DIR/.venv"
fi
"$SERVER_DIR/.venv/bin/pip" install --quiet --upgrade pip wheel
echo "Installation des dépendances du serveur (torch est volumineux, ça peut prendre plusieurs minutes)..."
"$SERVER_DIR/.venv/bin/pip" install --quiet -r "$SERVER_DIR/requirements.txt"

step "Modèle Whisper « $MODEL » (environ 480 Mo)"
if [[ ! -f "$SERVER_DIR/whisperflow/models/$MODEL.pt" ]]; then
    "$SERVER_DIR/.venv/bin/python" -c \
        "import whisper; whisper._download(whisper._MODELS['$MODEL'], '$SERVER_DIR/whisperflow/models', False)"
else
    echo "Déjà téléchargé."
fi

step "Client whisper-client : $CLIENT_DIR"
if [[ ! -x "$CLIENT_DIR/.venv/bin/python" ]]; then
    "$PYTHON" -m venv "$CLIENT_DIR/.venv"
fi
"$CLIENT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$CLIENT_DIR/.venv/bin/pip" install --quiet -e "$CLIENT_DIR"

step "Terminé"
cat <<EOF

Il reste une étape manuelle, que macOS n'autorise pas à automatiser :
dans Réglages Système > Confidentialité et sécurité, autorise ton app de terminal
(Terminal, iTerm, VS Code...) dans ces trois sections :
  - Micro
  - Accessibilité
  - Surveillance de l'entrée
Puis quitte complètement le terminal (Cmd+Q) et rouvre-le.

Pour lancer :
  cd "$CLIENT_DIR"
  .venv/bin/python -m whisper_client

Une pastille apparaît dans la barre de menus : ⚪ pendant le chargement, puis 🟢.
Maintiens Option droite pour dicter, relâche pour coller le texte.
EOF
