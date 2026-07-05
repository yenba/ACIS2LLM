#!/usr/bin/env bash
# Download the static uv binary into src-tauri resources (skips if present).
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/src-tauri/resources/uv"
if [[ -x "$DEST/uv" ]]; then
  echo "uv already present at $DEST/uv"
  exit 0
fi
mkdir -p "$DEST"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz" \
  | tar -xz -C "$TMP"
mv "$TMP"/uv-aarch64-apple-darwin/uv "$DEST/uv"
chmod +x "$DEST/uv"
echo "uv installed to $DEST/uv"
