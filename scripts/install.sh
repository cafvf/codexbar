#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if ! command -v uv >/dev/null 2>&1; then
  echo "CodexBar: uv is required for installation." >&2
  exit 2
fi

: "${HOME:?CodexBar: HOME is required for user-local installation}"

ORIGINAL_XDG_DATA_HOME=${XDG_DATA_HOME-}

export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CONFIG_HOME="$HOME/.config"
export UV_TOOL_DIR="$HOME/.local/share/uv/tools"
export UV_TOOL_BIN_DIR="$HOME/.local/bin"

mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$UV_TOOL_BIN_DIR"

uv tool install --force --with 'PySide6>=6.8' "$ROOT"
BIN_DIR=$(uv tool dir --bin)
"$BIN_DIR/codexbar" desktop install

echo
echo "CodexBar installed in canonical user-local locations:"
echo "  Tool: $UV_TOOL_DIR"
echo "  Launcher: $UV_TOOL_BIN_DIR/codexbar"
echo "  Desktop data: $XDG_DATA_HOME"
echo "  Config: $XDG_CONFIG_HOME"
echo "  Autostart: disabled (opt-in)"
echo
echo "Start it with:"
echo "  $BIN_DIR/codexbar --gui"
echo "Enable autostart explicitly with:"
echo "  $BIN_DIR/codexbar desktop autostart enable"

case "$ORIGINAL_XDG_DATA_HOME" in
  "$HOME"/snap/*)
    echo
    echo "Note: a Snap-scoped XDG_DATA_HOME was detected:"
    echo "  $ORIGINAL_XDG_DATA_HOME"
    echo "Any earlier CodexBar tool installed there is separate from this canonical install."
    echo "After validating this install, remove the legacy copy with:"
    echo "  XDG_DATA_HOME='$ORIGINAL_XDG_DATA_HOME' uv tool uninstall codexbar"
    ;;
esac
