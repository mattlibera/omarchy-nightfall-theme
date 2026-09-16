<p align="center">
  <img src="banner-rounded.png" alt="Nightfall" />
</p>

# Nightfall

An [Omarchy](https://omarchy.org) theme inspired by the colors of the night sky — purple, cyan, and teal accents over a deep `#1c1e26` background.

Originally a JetBrains theme by [@coeiico](https://github.com/coeiico/jetbrains-nightfall-theme) (now maintained by me); this is the port to Omarchy.

## What's included

- **Palette** (`colors.toml`) — drives auto-theming for terminals (Alacritty, Ghostty, Kitty, Foot), Obsidian, Chromium, waybar, mako, walker, hyprland/hyprlock, and more
- **Neovim** (`neovim.lua`) — references [`nightfall.nvim`](https://github.com/mattlibera/nightfall.nvim) via LazyVim. Omarchy only trusts `.lua` from a theme it didn't clone from git, so installing this theme the normal way (`omarchy theme install`) does **not** load `nightfall.nvim` — Neovim instead falls back to Omarchy's generic `colors.toml`-driven theme. See [Full Neovim experience](#full-neovim-experience) below to get the real thing.
- **btop** (`btop.theme`) — system monitor colors with a teal → yellow → red gradient
- **VS Code** (`vscode.json`) — points at [`qatoqat.nightfall-theme`](https://marketplace.visualstudio.com/items?itemName=qatoqat.nightfall-theme)
- **Icons** (`icons.theme`) — `Yaru-purple`
- **Wallpapers** (`backgrounds/`) — seven original wallpapers generated with `wallpapers/generate.py`
- **Unlock logo** (`unlock.png`) — OMARCHY in rainbow palette

## Screenshots

<p align="center">
  <img src="images/desktop.png" alt="Nightfall desktop" />
</p>

| **Neovim** | **btop** |
| :---: | :---: |
| <img src="images/neovim.png" alt="Neovim" /> | <img src="images/btop.png" alt="btop" /> |
| **Lazygit** | **Fastfetch** |
| <img src="images/lazygit.png" alt="Lazygit" /> | <img src="images/fastfetch.png" alt="Fastfetch" /> |

## Install

```bash
omarchy theme install https://github.com/mattlibera/omarchy-nightfall-theme.git
```

This gets you everything except the real Neovim colorscheme — see below.

## Full Neovim experience

Omarchy strips `.lua` files from any theme it installs from a git repo (it
won't run a stranger's Lua at startup), so `omarchy theme install` alone will
render Neovim with a generic, `colors.toml`-driven approximation rather than
[`nightfall.nvim`](https://github.com/mattlibera/nightfall.nvim) itself. To get
the real thing, install this theme from a plain download instead of a git
clone, so Omarchy treats it as trusted and keeps `neovim.lua`:

```bash
curl -L -o /tmp/nightfall-theme.zip \
  https://github.com/mattlibera/omarchy-nightfall-theme/archive/refs/heads/master.zip
rm -rf ~/.config/omarchy/themes/nightfall
unzip -q /tmp/nightfall-theme.zip -d /tmp
mv /tmp/omarchy-nightfall-theme-master ~/.config/omarchy/themes/nightfall
omarchy theme set nightfall
```

Then restart Neovim (or run `:Lazy sync`) so it picks up `nightfall.nvim`.

This trades the usual git-clone safety net for the full theme — you're
choosing to trust this repo's `neovim.lua` to run directly. It also means
`omarchy theme update` won't track it, since that command only pulls themes
it recognizes as git clones; re-run the steps above to pick up updates.

## Wallpapers

The seven wallpapers in `backgrounds/` are generated procedurally — nebula, flow field, geometry, aurora, starfield, topographic, and mesh gradient. Regenerate or add your own with:

```bash
python wallpapers/generate.py
```

Requires `numpy`, `pillow`, and `scipy`.
