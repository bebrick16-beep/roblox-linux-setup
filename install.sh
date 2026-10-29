#!/usr/bin/env bash
set -euo pipefail

APP=space.bigrat.mocktail
THEME=RobloxLegacy
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.var/app/$APP/config/mocktail"
CONFIG="$CONFIG_DIR/config.yaml"
ICONS="$HOME/.local/share/icons/$THEME"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

[[ $EUID -eq 0 ]] && { echo "Run this as your user, not root."; exit 1; }

command -v flatpak >/dev/null || {
  echo "flatpak is required: sudo pacman -S flatpak"
  exit 1
}

say "Installing Mocktail from Flathub"
flatpak remote-add --if-not-exists --user flathub \
  https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y --user flathub "$APP"

say "Allowing PipeWire inside the sandbox"
flatpak override --user --filesystem=xdg-run/pipewire-0 "$APP"

say "Installing the roblox launcher"
mkdir -p "$BIN_DIR"
install -m 755 "$DIR/files/roblox" "$BIN_DIR/roblox"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) warn "$BIN_DIR is not in PATH. Add: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

say "Applying Mocktail config"
mkdir -p "$CONFIG_DIR"
if [[ -f "$CONFIG" ]]; then
  cp -a "$CONFIG" "$CONFIG.bak.$(date +%s)"
  sed -i -E 's/^([[:space:]]*multithreaded_rendering:[[:space:]]*).*/\1true/' "$CONFIG"
  sed -i -E 's/^([[:space:]]*physics_worker_mode:[[:space:]]*).*/\1throughput/' "$CONFIG"
else
  install -m 600 "$DIR/files/mocktail-config.yaml" "$CONFIG"
fi

say "Building the $THEME cursor theme"
if python3 "$DIR/scripts/build-cursors.py"; then
  :
else
  warn "Cursors skipped. Start the game once (run 'roblox'), then rerun this script."
fi

if command -v plasma-apply-cursortheme >/dev/null 2>&1 && [[ -d "$ICONS" ]]; then
  say "Applying the cursor theme in KDE Plasma"
  plasma-apply-cursortheme "$THEME" || warn "Set it manually: System Settings > Appearance > Cursors"
  command -v kwriteconfig6 >/dev/null 2>&1 && \
    kwriteconfig6 --file kdeglobals --group Mouse --key cursorSize 24 || true
fi

say "Done"
cat <<'EOF'

Next steps:
  1. Run `roblox` and log in (Quick login is easiest).
  2. If the cursor was skipped, close Roblox and run `./install.sh` once more.
  3. Optional: sudo ./scripts/enable-turbo.sh   (higher FPS, more heat)

KDE screenshot shortcut: System Settings > Shortcuts > Spectacle >
  "Capture Entire Screen" -> F10.
EOF
