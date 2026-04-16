#!/bin/bash
# setup.sh: One-time repository setup after cloning.
#
# Run this script once after cloning to activate git hooks
# and install development dependencies.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Repository Setup ==="

# 1. Activate git hooks
echo "[1/2] Configuring git hooks..."
git -C "$REPO_ROOT" config core.hooksPath .githooks
chmod +x "$REPO_ROOT/.githooks/pre-commit"
chmod +x "$REPO_ROOT/.githooks/commit-msg"
echo "      Git hooks activated (.githooks/)"

# 2. Install dev dependencies
echo "[2/2] Installing development dependencies..."
if command -v pip >/dev/null 2>&1; then
    pip install -r "$REPO_ROOT/client/requirements-dev.txt" --quiet
    echo "      Dependencies installed."
else
    echo "      WARNING: pip not found. Install manually:"
    echo "      pip install -r client/requirements-dev.txt"
fi

echo ""
echo "Setup complete."
echo "  - pre-commit hook: runs pytest before each commit"
echo "  - commit-msg hook: enforces Linux kernel commit format"
