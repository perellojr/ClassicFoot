#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "[ClassicFoot] Build macOS iniciado..."

pick_python_with_tk() {
  local candidates=(
    "/usr/local/bin/python3.12"
    "/usr/local/bin/python3.11"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "python3"
  )
  for py in "${candidates[@]}"; do
    if ! command -v "$py" >/dev/null 2>&1; then
      continue
    fi
    if "$py" - <<'PY' >/dev/null 2>&1
import sys
if sys.version_info < (3, 10):
    raise SystemExit(1)
import tkinter
import _tkinter
PY
    then
      echo "$py"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(pick_python_with_tk || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "[ClassicFoot] Nenhum Python 3.10+ com tkinter foi encontrado."
  echo "Instale Python oficial (python.org) 3.11/3.12 e rode novamente."
  exit 1
fi

echo "[ClassicFoot] Python selecionado: $PYTHON_BIN"

BUILD_VENV=".venv_gui_build"
if [[ ! -d "$BUILD_VENV" ]]; then
  "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi
# shellcheck disable=SC1091
source "$BUILD_VENV/bin/activate"

if ! python -m pip show pyinstaller >/dev/null 2>&1; then
  python -m pip install pyinstaller
fi
python -m pip show colorama >/dev/null 2>&1 || python -m pip install -r requirements.txt

rm -rf build dist

pyinstaller \
  --noconfirm \
  --windowed \
  --name ClassicFoot \
  launcher_gui.py

# Limpa metadados e re-assina ad-hoc (evita erro de assinatura no macOS)
xattr -cr dist/ClassicFoot.app || true
codesign --force --deep --sign - dist/ClassicFoot.app
codesign --verify --deep --strict dist/ClassicFoot.app

echo
echo "[ClassicFoot] Build concluído."
echo "App: $ROOT_DIR/dist/ClassicFoot.app"
