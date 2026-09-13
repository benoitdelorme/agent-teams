#!/bin/sh
# Puts `teams` on your PATH as a symlink to this checkout. Run it once; `git pull` upgrades in place.
# Usage: ./install.sh [target-dir]   (default: ~/.local/bin, or /usr/local/bin when writable and ~/.local/bin absent)
set -e
here="$(cd "$(dirname "$0")" && pwd)"
target="${1:-}"
if [ -z "$target" ]; then
  if [ -d "$HOME/.local/bin" ] || [ ! -w /usr/local/bin ]; then target="$HOME/.local/bin"; else target=/usr/local/bin; fi
fi
mkdir -p "$target"
[ -d "$target" ] || { echo "install.sh: $target must be a directory" >&2; exit 1; }
target="$(cd "$target" && pwd)"
ln -sfn "$here/bin/teams" "$target/teams"
echo "linked $target/teams -> $here/bin/teams"
case ":$PATH:" in
  *":$target:"*) echo "ok: $target is on your PATH. Try: teams --help" ;;
  *) echo "add it to your PATH, e.g. in ~/.zshrc:  export PATH=\"$target:\$PATH\"" ;;
esac
