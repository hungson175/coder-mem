#!/bin/bash
# Install script for coder-mem command

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"

echo "Installing 'coder-mem' command globally..."
echo ""

# Create ~/.local/bin if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Create symlink to the main launcher
ln -sf "$SCRIPT_DIR/coder-mem" "$INSTALL_DIR/coder-mem"
echo "[SUCCESS] coder-mem installed to $INSTALL_DIR/coder-mem"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "[INFO] Add $INSTALL_DIR to your PATH by adding this line to your shell config:"
    echo ""
    if [ -f "$HOME/.zshrc" ]; then
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
        echo "  source ~/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "  source ~/.bashrc"
    else
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "  # Add this to your shell configuration file"
    fi
else
    echo "You can now run 'coder-mem' from any directory!"
fi

echo ""
echo "Usage:"
echo "  coder-mem                    # Run in current directory"
echo "  coder-mem /path/to/project   # Run in specified directory"
echo "  coder-mem --help             # Show help"
echo ""
echo "Use /model command inside the tool to switch LLM providers"
