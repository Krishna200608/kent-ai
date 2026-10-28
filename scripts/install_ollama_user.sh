#!/usr/bin/env bash
# ==============================================================================
# Kent-AI: Non-Root / User-Space Ollama Installation Script
# Useful for shared University / College GPU clusters where users do not have sudo.
# ==============================================================================

set -euo pipefail

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64) ARCH_TAG="amd64" ;;
    aarch64|arm64) ARCH_TAG="arm64" ;;
    *) echo "[✗] Unsupported architecture: ${ARCH}"; exit 1 ;;
esac

INSTALL_DIR="${HOME}/.local"
BIN_DIR="${INSTALL_DIR}/bin"
ARCHIVE_NAME="ollama-linux-${ARCH_TAG}.tar.zst"
LOCAL_ARCHIVE="${HOME}/${ARCHIVE_NAME}"
DOWNLOAD_URL="https://ollama.com/download/${ARCHIVE_NAME}"

echo "=================================================================="
echo "  KENT-AI: NON-ROOT USER-SPACE OLLAMA INSTALLER"
echo "=================================================================="
echo "Target Directory : ${INSTALL_DIR}"
echo "Binary Location  : ${BIN_DIR}/ollama"
echo "Architecture     : ${ARCH_TAG}"

# 1. Create target directories
mkdir -p "${BIN_DIR}" "${INSTALL_DIR}/lib"

# 2. Check for required extraction tools
if ! command -v tar &>/dev/null; then
    echo "[✗] Error: tar is required but not installed."
    exit 1
fi

if ! command -v zstd &>/dev/null; then
    echo "[✗] Error: zstd is required to extract .tar.zst archives."
    echo "    Please ask your system admin to install zstd, or extract locally."
    exit 1
fi

# 3. Check if archive exists locally (e.g. uploaded via scp) or download it
if [ -f "${LOCAL_ARCHIVE}" ] && [ "$(stat -c%s "${LOCAL_ARCHIVE}" 2>/dev/null || stat -f%z "${LOCAL_ARCHIVE}")" -gt 1000000000 ]; then
    echo "[✓] Found complete archive at ${LOCAL_ARCHIVE}. Skipping download."
else
    echo "[*] Downloading Ollama bundle (~1.4 GB) with resume support..."
    echo "    From: ${DOWNLOAD_URL}"
    echo "    To  : ${LOCAL_ARCHIVE}"
    curl -C - -L --progress-bar "${DOWNLOAD_URL}" -o "${LOCAL_ARCHIVE}"
fi

# 4. Extract archive to ~/.local
echo "[*] Extracting ${LOCAL_ARCHIVE} into ${INSTALL_DIR}..."
tar --zstd -xf "${LOCAL_ARCHIVE}" -C "${INSTALL_DIR}"

# 5. Ensure PATH includes ~/.local/bin in ~/.bashrc
if ! grep -q 'export PATH=.*\.local/bin' "${HOME}/.bashrc" 2>/dev/null; then
    echo "[*] Adding ${BIN_DIR} to PATH in ~/.bashrc..."
    echo '' >> "${HOME}/.bashrc"
    echo '# Kent-AI: User-space local binaries (Ollama, etc.)' >> "${HOME}/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
fi

export PATH="${BIN_DIR}:${PATH}"

# 6. Verify Installation
if command -v ollama &>/dev/null; then
    echo "=================================================================="
    echo "[✓] Ollama successfully installed to user space!"
    echo "    Version: $(ollama --version 2>&1 || true)"
    echo "=================================================================="
    echo "To clean up disk space, you can remove the archive:"
    echo "    rm -f ${LOCAL_ARCHIVE}"
    echo ""
    echo "Next steps:"
    echo "  1. Reload your shell PATH:"
    echo "     source ~/.bashrc"
    echo "  2. Start the Ollama background daemon:"
    echo "     nohup ollama serve > logs/ollama.log 2>&1 &"
    echo "  3. Pull LLaMA 3 8B:"
    echo "     ollama pull llama3:8b"
    echo "=================================================================="
else
    echo "[✗] Installation failed or ollama executable not found at ${BIN_DIR}/ollama"
    exit 1
fi
