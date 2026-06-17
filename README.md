# Curl Folder
A tool for curl that lets you easily install things.

## Installation
To install, run this command:
```bash
sudo -v && (if ! command -v python3 &>/dev/null; then echo "Installing Python..."; if command -v apt-get &>/dev/null; then sudo apt-get update && sudo apt-get install -y python3; elif command -v dnf &>/dev/null; then sudo dnf install -y python3; elif command -v pacman &>/dev/null; then sudo pacman -Sy --noconfirm python; elif command -v zypper &>/dev/null; then sudo zypper install -y python3; fi; fi) && mkdir -p "$HOME/.local/bin" && curl -sSL "https://githubusercontent.com" -o "$HOME/.local/bin/curlFolder.py" && echo -e '#!/bin/sh\npython3 "$HOME/.local/bin/curlFolder.py" "$@"' > "$HOME/.local/bin/curlFolder" && chmod +x "$HOME/.local/bin/curlFolder" && for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do [ -f "$rc" ] && ! grep -q "curlFolder" "$rc" && echo -e '\nexport PATH="$HOME/.local/bin:$PATH"' >> "$rc"; done && echo "Installation complete! Please restart your terminal or run: source ~/.zshrc (or ~/.bashrc)"
```
Now, curlFolder is available in your path. For changes to take effect, restart your terminal.
