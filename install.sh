#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="https://raw.githubusercontent.com/fugtailer/nvidia-sandbox-agent/main"

echo "[sandbox] Starting installation..."

# Detect OS
OS="$(uname -s)"
if [[ "$OS" == "Linux" ]]; then
  DIST="linux"
elif [[ "$OS" == "Darwin" ]]; then
  DIST="macos"
else
  echo "[sandbox] Unsupported OS: $OS" >&2
  exit 1
fi

# Ensure git, python3, pip
command -v git >/dev/null 2>&1 || { echo "[sandbox] Installing git..."; if [[ "$DIST" == "linux" ]]; then sudo apt-get update && sudo apt-get install -y git || sudo yum install -y git; else brew install git; fi }
command -v python3 >/dev/null 2>&1 || { echo "[sandbox] Installing python3..."; if [[ "$DIST" == "linux" ]]; then sudo apt-get install -y python3 python3-venv python3-pip || sudo yum install -y python3 python3-venv python3-pip; else brew install python; fi }

# Create install directory
INSTALL_DIR="$HOME/.nvidia-sandbox-agent"
mkdir -p "$INSTALL_DIR"

# Copy files from repo raw
echo "[sandbox] Downloading files..."
curl -fsS "$REPO_RAW_BASE/sandbox-cli.py" -o "$INSTALL_DIR/sandbox-cli.py"
curl -fsS "$REPO_RAW_BASE/requirements.txt" -o "$INSTALL_DIR/requirements.txt"
curl -fsS "$REPO_RAW_BASE/config.example.json" -o "$INSTALL_DIR/config.example.json"
curl -fsS "$REPO_RAW_BASE/README.md" -o "$INSTALL_DIR/README.md"

# Install Python deps into venv
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$INSTALL_DIR/requirements.txt"

# Create sandbox executable
BIN_PATH="/usr/local/bin/sandbox"
echo "[sandbox] Writing launcher to $BIN_PATH (may require sudo)"
LAUNCHER="#!/usr/bin/env bash\nsource \"$INSTALL_DIR/venv/bin/activate\"\npython \"$INSTALL_DIR/sandbox-cli.py\" \"$@\"\n"
if [[ -w "/usr/local/bin" ]]; then
  printf "%s" "$LAUNCHER" > "$BIN_PATH"
  chmod +x "$BIN_PATH"
else
  echo "$LAUNCHER" | sudo tee "$BIN_PATH" >/dev/null
  sudo chmod +x "$BIN_PATH"
fi

echo "[sandbox] Installed to $INSTALL_DIR and launcher at $BIN_PATH"

echo "[sandbox] Installation complete. Run 'sandbox --help' to get started."