#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
  echo "CodexBar: uv is required to remove the installed tool." >&2
  exit 2
fi

: "${HOME:?CodexBar: HOME is required for user-local uninstall}"

export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CONFIG_HOME="$HOME/.config"
export UV_TOOL_DIR="$HOME/.local/share/uv/tools"
export UV_TOOL_BIN_DIR="$HOME/.local/bin"

BIN_DIR=$(uv tool dir --bin)
if [ -x "$BIN_DIR/codexbar" ]; then
  "$BIN_DIR/codexbar" desktop uninstall
fi
uv tool uninstall codexbar

echo "CodexBar canonical user-local installation removed."
