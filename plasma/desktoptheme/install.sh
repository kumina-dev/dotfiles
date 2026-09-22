#!/usr/bin/env bash

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/KumiOS"
TARGET_DIR="$HOME/.local/share/plasma/desktoptheme/KumiOS"

rm -rf "$TARGET_DIR"
mkdir -p "$(dirname "$TARGET_DIR")"

cp -r "$SOURCE_DIR" "$TARGET_DIR"

echo "Installed KumiOS Plasma Style to:"
echo "  $TARGET_DIR"
