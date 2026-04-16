#!/bin/bash
# Build maha-client as a single executable using PyInstaller.
# Output: client/dist/maha-client  (Linux/macOS)
#         client/dist/maha-client.exe  (Windows)
#
# Usage:
#   cd client && bash build.sh
#   bash client/build.sh       # from repo root

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== maha-client build ==="

# Install PyInstaller if not present
if ! python3 -m PyInstaller --version &>/dev/null 2>&1; then
    echo "[1/3] Installing build dependencies..."
    pip install -r requirements-build.txt --quiet
else
    echo "[1/3] PyInstaller found: $(python3 -m PyInstaller --version)"
fi

# Clean previous artefacts
echo "[2/3] Cleaning dist/ and build/..."
rm -rf dist/ build/

# Build
echo "[3/3] Running PyInstaller..."
python3 -m PyInstaller maha-client.spec --noconfirm

echo ""
echo "Build complete → dist/maha-client"
echo ""
echo "Run:"
echo "  ./dist/maha-client"
echo "  GATEWAY_URL=http://myserver:8000 ./dist/maha-client"
