"""Scanner da biblioteca: varre todas as pastas configuradas por sistema.

Suporta múltiplas pastas por sistema e três modos:
- files:      arquivos por extensão (recursivo, pasta oculta pulada)
- folder_sfo: pastas com sce_sys/param.sfo (PS4)
- folder_ps3: pastas do RPCS3 (PKG ou dump PS3_GAME) **e** .iso PS3ISO —
              ícone/título como o RPCS3 puxa (ICON0.PNG/PARAM.SFO), com
              busca case-insensitive (Linux não perdoa EBOOT.BIN vs eboot.bin)
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field

from .catalog import SYSTEMS
from . import covers
from . import gamelist
from . import iso9660
from .sfo import read_sfo_title, title_from_bytes

MAX_DEPTH = 5
COVER_EXTS = (".png", ".jpg", ".jpeg", ".webp")


@dataclass
class Game:
    id: str
    title: str
    system: str
    path: str        # caminho "lançável" (arquivo ou eboot)
    dir: str         # pasta do jogo
    icon: str | None = None
    tags: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)  # gamelist.xml (gênero, nota…)


def _gid(system: str, path: str) -> str:
    return hashlib.sha1(f"{system}|{path}".encode()).hexdigest()[:12]


def _clean_title(stem: str) -> str:
    return stem.replace("_", " ").strip()


def _find_cover(rom_path: str) -> str | None:
    """Capa local: <rom>.png/.jpg na mesma pasta ou folder.png."""
    stem = os.path.splitext(rom_path)[0]
    folder = os.path.dirname(rom_path)
    for cand in (stem, os.path.join(folder, "folder")):
        for ext in COVER_EXTS:
            p = cand + ext
            if os.path.isfile(p):
                return p
    return None


def _scan_files(system: str, root: str, exts: list[str]) -> list[Game]:
    games: list[Game] = []
    exts = [e.lower() for e in exts]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if dirpath.count(os.sep) - root.count(os.sep) >= MAX_DEPTH:
            dirnames[:] = []
            continue
        stems_with_cue = {os.path.splitext(f)[0].lower() for f in filenames
                          if f.lower().endswith(".cue")}
        for fn in filenames:
            low = fn.lower()
            ext = os.path.splitext(low)[1]
            if ext not in exts:
                continue
            # PS1: prefere .cue sobre .bin solto do mesmo disco
            if ext == ".bin" and os.path.splitext(fn)[0].lower() in stems_with_cue:
                continue
            full = os.path.join(dirpath, fn)
            # capa: local ao lado da ROM → cache baixado → None (placeholder)
            icon = _find_cover(full)
            if not icon and covers.has_cover(system, full):
                icon = covers.cover_path(system, full)
            games.append(Game(
                id=_gid(system, full),
                title=_clean_title(os.path.splitext(fn)[0]),
                system=system,
                path=full,
                dir=dirpath,
                icon=icon,
            ))
    return games


def _scan_folder_sfo(system: str, root: str) -> list[Game]:
    """PS4: pastas com sce_sys/param.sfo (ignora updates -patch)."""
    games: list[Game] = []
    for entry in sorted(os.listdir(root)):
        gdir = os.path.join(root, entry)
        sfo = os.path.join(gdir, "sce_sys", "param.sfo")
        if not os.path.isdir(gdir) or entry.endswith("-patch") or not os.path.isfile(sfo):
            continue
        eboot = os.path.join(gdir, "eboot.bin")
        icon = os.path.join(gdir, "sce_sys", "icon0.png")
        games.append(Game(
            id=_gid(system, gdir),
            title=read_sfo_title(sfo) or entry,
            system=system,
            path=eboot if os.path.isfile(eboot) else gdir,
            dir=gdir,
            icon=icon if os.path.isfile(icon) else None,
        ))
    return games


def _case_find(directory: str, name: str) -> str | None:
    """Acha ``name`` dentro de ``directory`` ignorando maiúsculas/minúsculas."""
    try:
        entries = os.listdir(directory)
    except OSError:
        return None
    low = name.lower()
    for e in entries:
        if e.lower() == low:
            return os.path.join(directory, e)
    return None


def _ps3_layout(gdir: str) -> tuple[str, str] | None:
    """Acha o USRDIR/eboot.bin: PKG (na raiz) ou dump de disco (PS3_GAME/).

    Cada componente é procurado case-insensitive (EBOOT.BIN/eboot.bin…).
    Devolve (base, eboot) onde a base guarda PARAM.SFO e ICON0.PNG.
    """
    disc = _case_find(gdir, "PS3_GAME")
    for base in (gdir, disc):
        if not base or not os.path.isdir(base):
            continue
        usrd = _case_find(base, "USRDIR")
        if not usrd:
            continue
        eboot = _case_find(usrd, "eboot.bin")
        if eboot and os.path.isfile(eboot):
            return base, eboot
    return None


def _ps3_iso_icon(iso: str) -> str | None:
    """ICON0.PNG de dentro da iso → cache local (cache/ps3/<hash>.png)."""
    cache = os.path.join(os.path.dirname(covers.CACHE_DIR), "ps3")
    icon = os.path.join(cache, hashlib.sha1(iso.encode()).hexdigest()[:16] + ".png")
    if os.path.isfile(icon):
        return icon
    for inner in ("/PS3_GAME/ICON0.PNG", "/ICON0.PNG"):
        png = iso9660.read_file(iso, inner)
        if png and png[:4] == b"\x89PNG":
            os.makedirs(cache, exist_ok=True)
            tmp = icon + ".part"
            with open(tmp, "wb") as f:
                f.write(png)
            os.replace(tmp, icon)
            return icon
    return None


def _scan_folder_ps3(system: str, root: str) -> list[Game]:
    """RPCS3: pastas (PKG ou dump PS3_GAME) + .iso (PS3ISO), tudo case-insensitive."""
    games: list[Game] = []
    for entry in sorted(os.listdir(root)):
        gdir = os.path.join(root, entry)
        # .iso: título e ícone saem de dentro da própria imagem (PS3_GAME/)
        if os.path.isfile(gdir) and entry.lower().endswith(".iso"):
            sfo = iso9660.read_file(gdir, "/PS3_GAME/PARAM.SFO", max_mb=1)
            if sfo is None:
                sfo = iso9660.read_file(gdir, "/PARAM.SFO", max_mb=1)
            title = title_from_bytes(sfo) if sfo else None
            games.append(Game(
                id=_gid(system, gdir),
                title=title or _clean_title(os.path.splitext(entry)[0]),
                system=system,
                path=gdir,
                dir=os.path.dirname(gdir),
                icon=_ps3_iso_icon(gdir),
            ))
            continue
        if not os.path.isdir(gdir):
            continue
        found = _ps3_layout(gdir)
        if not found:
            continue
        base, eboot = found
        sfo = _case_find(base, "PARAM.SFO")
        icon = _case_find(base, "ICON0.PNG")
        title = read_sfo_title(sfo) if sfo else None
        games.append(Game(
            id=_gid(system, eboot),
            title=title or entry,
            system=system,
            path=eboot,
            dir=gdir,
            icon=icon if icon and os.path.isfile(icon) else None,
        ))
    return games


def scan(cfg) -> list[Game]:
    """Biblioteca completa a partir da config."""
    games: list[Game] = []
    for sysid, dirs in cfg.all_rom_dirs().items():
        sysdef = SYSTEMS.get(sysid)
        if not sysdef:
            continue
        kind = sysdef["kind"]
        for root in dirs:
            root = os.path.expanduser(root)
            if not os.path.isdir(root):
                continue
            if kind == "files":
                found = _scan_files(sysid, root, sysdef["ext"])
            elif kind == "folder_sfo":
                found = _scan_folder_sfo(sysid, root)
            elif kind == "folder_ps3":
                found = _scan_folder_ps3(sysid, root)
            else:
                found = []
            if found:
                gamelist.apply(found, root)  # gamelist.xml → meta/título
            games.extend(found)
    # jogos PC manuais
    for item in cfg["pc_games"]:
        p = item.get("path", "")
        if os.path.isfile(p):
            games.append(Game(
                id=_gid("pc", p),
                title=item.get("name") or os.path.basename(p),
                system="pc",
                path=p,
                dir=os.path.dirname(p),
                icon=_find_cover(p) or (item.get("icon") if os.path.isfile(item.get("icon", "")) else None),
            ))
    games.sort(key=lambda g: g.title.lower())
    return games
