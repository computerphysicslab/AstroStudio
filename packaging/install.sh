#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_DIR/applications"
ICON_DIR="$DATA_DIR/icons/hicolor"

mkdir -p "$APPS_DIR" "$ICON_DIR/scalable/apps" "$DATA_DIR/mime/packages"
chmod +x "$PROJECT_ROOT/packaging/astro-studio"

sed "s|@EXEC@|$PROJECT_ROOT/packaging/astro-studio|" \
    "$PROJECT_ROOT/packaging/astro-studio.desktop" > "$APPS_DIR/astro-studio.desktop"
install -m 0644 "$PROJECT_ROOT/packaging/astro-studio.svg" \
    "$ICON_DIR/scalable/apps/astro-studio.svg"
install -m 0644 "$PROJECT_ROOT/packaging/astro-studio-mime.xml" \
    "$DATA_DIR/mime/packages/astro-studio-formats.xml"

if command -v inkscape >/dev/null 2>&1; then
    for size in 16 22 24 32 48 64 96 128 256; do
        mkdir -p "$ICON_DIR/${size}x${size}/apps"
        inkscape "$PROJECT_ROOT/packaging/astro-studio.svg" \
            --export-type=png \
            --export-filename="$ICON_DIR/${size}x${size}/apps/astro-studio.png" \
            --export-width="$size" --export-height="$size" >/dev/null 2>&1
    done
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi
if command -v update-mime-database >/dev/null 2>&1 && [ -d "$DATA_DIR/mime" ]; then
    update-mime-database "$DATA_DIR/mime" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_DIR" >/dev/null 2>&1 || true
fi

printf 'Astro Studio installed for %s\n' "$USER"
printf '  desktop entry: %s/astro-studio.desktop\n' "$APPS_DIR"
printf '  icon:          %s/scalable/apps/astro-studio.svg\n' "$ICON_DIR"
