# Curl Folder
A tool for curl that lets you easily install things.

## Installation
To install, run this command:
```bash
mkdir -p "$HOME/.local/bin" && curl -sSL "https://raw.githubusercontent.com/MeltingReactor/curlFolder/refs/heads/main/main.py" -o "$HOME/.local/bin/curlFolder" && chmod +x "$HOME/.local/bin/curlFolder" && for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do [ -f "$rc" ] && ! grep -q "curlFolder" "$rc" && echo -e '\nexport PATH="$HOME/.local/bin:$PATH"' >> "$rc"; done
```
Now, curlFolder is available in your path. For changes to take effect, restart your terminal.
