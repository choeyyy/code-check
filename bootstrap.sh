#!/usr/bin/env bash
# code-check bootstrap (Linux / macOS)
# Downloads only the setup skill so user can run /check-setup in Cursor.
# Usage: curl -sL https://raw.githubusercontent.com/choeyyy/code-check/main/bootstrap.sh | bash

set -euo pipefail

SKILL_DIR="${HOME}/.cursor/skills/check-setup"
SKILL_FILE="${SKILL_DIR}/SKILL.md"
RAW_URL="https://raw.githubusercontent.com/choeyyy/code-check/main/setup/SKILL.md"

if [ ! -d "${HOME}/.cursor" ]; then
    echo "[ERROR] Cursor directory not found. Please install Cursor first."
    exit 1
fi

if ! command -v git &>/dev/null; then
    echo "[ERROR] git is required. Please install git first."
    exit 1
fi

mkdir -p "${SKILL_DIR}"

if curl -sL -o "${SKILL_FILE}" "${RAW_URL}"; then
    echo ""
    echo "[ok] check-setup skill installed."
    echo ""
    echo "Next: open Cursor, type /check-setup to install the full plugin."
    echo ""
else
    echo "[ERROR] Failed to download setup skill."
    exit 1
fi
