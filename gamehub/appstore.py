"""Catálogo de AppImages oficiais dos emuladores standalone.

O hub prefere AppImage dentro do projeto (pasta ``cores/``): nada é instalado
no sistema. Nem todo emulador publica AppImage — nesse caso a UI mostra a
mensagem do catálogo ``NO_APPIMAGE`` com o link da fonte oficial.

Fontes: releases do GitHub (API pública) e do Gitea do Eden. O asset é
escolhido por regex — sempre a variante x86_64/amd64, sem debug/legacy.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

_GITHUB = "https://api.github.com/repos/{repo}/releases/latest"

# emu → fonte + regex do asset (sempre x86_64; $ = fim do nome)
APPIMAGES: dict[str, dict] = {
    "PCSX2": {"api": _GITHUB.format(repo="PCSX2/pcsx2"),
              "asset": r"linux-appimage-x64.*\.AppImage$"},
    "DuckStation": {"api": _GITHUB.format(repo="stenzek/duckstation"),
                    "asset": r"DuckStation-x64\.AppImage$"},
    "PPSSPP": {"api": _GITHUB.format(repo="hrydgard/ppsspp"),
               "asset": r"anylinux-x86_64\.AppImage$"},
    "Azahar": {"api": _GITHUB.format(repo="azahar-emu/azahar"),
               "asset": r"^azahar\.AppImage$"},
    "Eden": {"api": "https://git.eden-emu.dev/api/v1/repos/eden-emu/eden/releases/latest",
             "asset": r"amd64-clang-pgo\.AppImage$"},
    "Cemu": {"api": _GITHUB.format(repo="cemu-project/Cemu"),
             "asset": r"-x86_64\.AppImage$"},
    "xemu": {"api": _GITHUB.format(repo="xemu-project/xemu"),
             "asset": r"^xemu-[\w.]+-x86_64\.AppImage$"},
    "Vita3K": {"api": _GITHUB.format(repo="Vita3K/Vita3K"),
               "asset": r"x86_64\.AppImage$"},
    "Flycast": {"api": _GITHUB.format(repo="flyinghead/flycast"),
                "asset": r"x86_64-[\d.]+\.AppImage$"},
}

# emu sem AppImage oficial → (explicação curta, fonte oficial)
NO_APPIMAGE: dict[str, tuple[str, str]] = {
    "RPCS3": ("Builds oficiais em tar.gz — não há AppImage.",
              "https://rpcs3.net/download"),
    "shadPS4": ("Builds oficiais em .zip — não há AppImage.",
                "https://github.com/shadps4-emu/shadPS4/releases"),
    "Dolphin": ("Sem AppImage: builds .tar.xz ou Flatpak.",
                "https://dolphin-emu.org/download/"),
    "redream": ("Sem AppImage: binário .zip no site oficial.",
                "https://www.redream.net/download/"),
}

_UA = {"User-Agent": "GameHub"}


def _get_json(url: str):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def has_appimage(emu: str) -> bool:
    return emu in APPIMAGES


def no_appimage_note(emu: str) -> str:
    """Texto + fonte quando o emu não publica AppImage."""
    info, url = NO_APPIMAGE.get(emu, ("Não há AppImage oficial conhecido.", ""))
    return f"{info} {url}".strip()


def release_info(emu: str) -> dict | None:
    """Última release do emu → {tag, name, url, size} do AppImage x86_64."""
    spec = APPIMAGES.get(emu)
    if not spec:
        return None
    data = _get_json(spec["api"])
    rx = re.compile(spec["asset"], re.I)
    for a in data.get("assets", []):
        name = a.get("name", "")
        if rx.search(name) and not name.endswith(".zsync"):
            return {"tag": data.get("tag_name", ""),
                    "name": name,
                    "url": a.get("browser_download_url", ""),
                    "size": int(a.get("size") or 0)}
    return None


def download(emu: str, dest_dir: str, progress=None) -> str | None:
    """Baixa o AppImage oficial pra ``dest_dir`` (cores/). None = sem fonte.

    ``progress(texto)`` recebe status ("42%"); salva parcial em ``.part`` e
    renomeia no fim (nunca deixa arquivo meio-baixado no lugar).
    """
    info = release_info(emu)
    if not info or not info.get("url"):
        return None
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, info["name"])
    part = dest + ".part"
    req = urllib.request.Request(info["url"], headers=_UA)
    total = info.get("size", 0)
    done = 0
    last = -1
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(part, "wb") as f:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    pct = int(done * 100 / total)
                    if pct != last:
                        last = pct
                        progress(f"{pct}%")
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise
    os.replace(part, dest)
    os.chmod(dest, os.stat(dest).st_mode | 0o755)
    return dest
