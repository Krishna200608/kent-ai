#!/usr/bin/env bash
# ==============================================================================
# Kent-AI: Setup Repertory Database (repertory.sqlite)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

mkdir -p data/raw data/raw/kent_public_edition

DB_DEST="data/raw/repertory.sqlite"
DB_BUNDLE="data/raw/kent_public_edition/repertory.sqlite"
ZIP_PATH="${HOME}/kent_public_edition.zip"
DOWNLOAD_URL="https://github.com/su4532/kent-repertory-explorer/releases/download/v1.0.0/kent_public_edition.zip"

echo "=================================================================="
echo "  KENT-AI: REPERTORY DATABASE SETUP"
echo "=================================================================="

if [ -f "${DB_DEST}" ] && [ "$(stat -c%s "${DB_DEST}" 2>/dev/null || stat -f%z "${DB_DEST}")" -gt 50000000 ]; then
    echo "[✓] repertory.sqlite already exists and is healthy at ${DB_DEST}."
else
    # Check if zip is available or download it
    if [ ! -f "${ZIP_PATH}" ] || [ "$(stat -c%s "${ZIP_PATH}" 2>/dev/null || stat -f%z "${ZIP_PATH}")" -lt 80000000 ]; then
        echo "[*] Downloading kent_public_edition.zip (~89 MB)..."
        curl -L -C - --progress-bar "${DOWNLOAD_URL}" -o "${ZIP_PATH}"
    fi

    echo "[*] Extracting repertory.sqlite from ${ZIP_PATH}..."
    unzip -j -o "${ZIP_PATH}" "*repertory.sqlite" -d "data/raw/"
fi

# Ensure hardlink in kent_public_edition/
if [ ! -f "${DB_BUNDLE}" ]; then
    ln -f "${DB_DEST}" "${DB_BUNDLE}" || cp -f "${DB_DEST}" "${DB_BUNDLE}"
fi

echo "[✓] Database located: $(ls -lh ${DB_DEST})"

# Verify with Python
if [ -d ".venv" ]; then
    .venv/bin/python -c "from src.data.kent_db import KentDB; db = KentDB(); print('[✓] Verified SQLite connection. Total MIND rubrics:', len(db.get_mind_rubrics()))"
fi

echo "=================================================================="
echo "[✓] Repertory Database is ready for case generation!"
echo "=================================================================="
