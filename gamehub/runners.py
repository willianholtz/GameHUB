"""Resolução e lançamento de jogos.

Modos por sistema (regras do hub):
- ``retroarch``: abre o RetroArch **direto no jogo** (sem menu), com o core
  escolhido pelo usuário. Fullscreen ou janela conforme a opção do sistema.
- ``standalone``: emulador próprio (AppImage em cores/ ou PATH).

Ordem de resolução:
1. Configuração do usuário (config/front.json)
2. Auto-detect
3. Nada → None (a UI explica)
"""
from __future__ import annotations

import os
import re
import shutil

from PySide6.QtCore import QProcess, QProcessEnvironment

from .catalog import EMULATORS, SYSTEMS
from .config import PROJECT_DIR
from .scanner import Game


def ra_core_id(cfg, sysid: str) -> str | None:
    """Core do RetroArch pro sistema (ex.: 'snes9x') — None se não é modo core.

    Checa a config do usuário, senão o fallback ``ra_core`` do catálogo;
    sistemas em modo standalone (ou sem core) retornam None.
    """
    emu = cfg["emulators"].get(sysid)
    if emu is not None and emu.get("mode") != "retroarch":
        return None
    core = (emu or {}).get("core") or SYSTEMS.get(sysid, {}).get("ra_core", "")
    return core if core and cfg.ra_core_file(core) else None


def _label(cfg, sysid: str, emu: dict) -> str:
    """Nome amigável do que vai rodar (ex.: 'Mesen (core)') se for core."""
    if emu.get("mode") == "retroarch":
        from .catalog import CORES
        return CORES.get(emu.get("core", ""), {}).get("name", "RetroArch")
    return emu.get("name") or SYSTEMS.get(sysid, {}).get("emu", "?")


def resolve(cfg, game: Game) -> tuple[list[str], str] | None:
    """Retorna (argv, nome do emulador) ou None."""
    sysid = game.system
    if sysid == "pc":
        return [game.path], "PC"

    emu = cfg["emulators"].get(sysid)
    if not emu:
        emu = cfg.detect_emulator(sysid)
        if emu:
            cfg["emulators"][sysid] = emu
            cfg.save()
    if not emu:
        return None

    if emu.get("mode") == "retroarch":
        return _resolve_retroarch(cfg, sysid, game, emu)
    return _resolve_standalone(cfg, sysid, game, emu)


def _resolve_retroarch(cfg, sysid: str, game: Game,
                       emu: dict) -> tuple[list[str], str] | None:
    """Core do RetroArch: -L core (fullscreen/janela) — nunca mostra o RA."""
    ra = cfg.ra_binary()
    core = emu.get("core") or SYSTEMS.get(sysid, {}).get("ra_core", "")
    core_path = cfg.ra_core_file(core)
    if not ra or not core_path:
        return None
    argv = [ra]
    # regra: o jogo abre fullscreen OU em janela, sem passar pelo menu
    # (no RetroArch, fullscreen = -f; janela = nenhuma flag)
    if emu.get("fullscreen", True):
        argv.append("-f")
    argv += ["-L", core_path]
    for a in (emu.get("args") or []):
        argv.append(a.replace("{game}", game.path))
    argv.append(game.path)
    return argv, _label(cfg, sysid, emu)


def _resolve_standalone(cfg, sysid: str, game: Game,
                        emu: dict) -> tuple[list[str], str] | None:
    """Emulador standalone com flag de fullscreen quando conhecida."""
    app = emu.get("app")
    if not app or not os.path.exists(app):
        det = cfg.detect_standalone(sysid)
        if not det:
            return None
        emu.update(det)
        app = det["app"]
    args = emu.get("args") or EMULATORS.get(emu.get("name", ""), {}).get(
        "args", ["{game}"])
    argv = [app]
    fs_args = EMULATORS.get(emu.get("name", ""), {}).get("fullscreen")
    if emu.get("fullscreen_sa") and fs_args:
        argv += list(fs_args)
    for a in args:
        argv.append(a.replace("{game}", game.path))
    return argv, _label(cfg, sysid, emu)


def portable_env(cfg, app: str, emu_name: str = "") -> dict[str, str] | None:
    """Env do sandbox quando o emulador roda de dentro de ``cores/``.

    Toda config/saves/cache do emulador vão pra
    ``<projeto>/emu-data/<emu>/home`` — nada é escrito no ``~/.config`` do
    sistema. Binários fora de ``cores/`` (PATH do sistema) não são
    afetados, e o RetroArch embutido cuida do próprio ``.home``.

    ``None`` = sem sandbox (fora do projeto ou RetroArch).
    """
    cores = os.path.abspath(os.path.expanduser(cfg.cores_dir()))
    app_abs = os.path.abspath(app)
    if not app_abs.startswith(cores + os.sep):
        return None
    if "retroarch" in os.path.basename(app_abs).lower():
        return None  # embutido usa .home vizinho — não interferir
    key = re.sub(r"[^a-z0-9._-]+", "_",
                 (emu_name or os.path.basename(app_abs)).lower())
    key = key.replace(".appimage", "").strip("._") or "emu"
    home = os.path.join(PROJECT_DIR, "emu-data", key, "home")
    for sub in ("", ".config", os.path.join(".local", "share"), ".cache"):
        os.makedirs(os.path.join(home, sub), exist_ok=True)
    return {
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "XDG_DATA_HOME": os.path.join(home, ".local", "share"),
        "XDG_CACHE_HOME": os.path.join(home, ".cache"),
    }


def build_command(cfg, game: Game) -> list[str] | None:
    """Comando final (com gamemoderun se habilitado)."""
    resolved = resolve(cfg, game)
    if not resolved:
        return None
    argv, _name = resolved
    cmd: list[str] = []
    if cfg["gamemode"] and shutil.which("gamemoderun"):
        cmd.append("gamemoderun")
    cmd.extend(argv)
    return cmd


def launch(cfg, game: Game, parent) -> tuple[QProcess, str] | None:
    """Soma o processo. Caller conecta finished (hide/show na UI)."""
    resolved = resolve(cfg, game)
    if not resolved or not os.path.exists(game.path):
        return None
    argv, name = resolved
    cmd: list[str] = []
    if cfg["gamemode"] and shutil.which("gamemoderun"):
        cmd.append("gamemoderun")
    cmd.extend(argv)
    proc = QProcess(parent)
    proc.setWorkingDirectory(os.path.dirname(game.path))
    env_map = portable_env(cfg, argv[0], name)
    if env_map:
        env = QProcessEnvironment.systemEnvironment()
        for k, v in env_map.items():
            env.insert(k, v)
        proc.setProcessEnvironment(env)
    proc.start(cmd[0], cmd[1:])
    return proc, name
