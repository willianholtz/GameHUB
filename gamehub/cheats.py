"""Cheats do RetroArch: descoberta, download e aplicação automática.

O RetroArch, ao abrir um conteúdo, procura sozinho
``<cheat_database_path>/<nome do core>/<rom>.cht`` e aplica os itens com
``cheat<i>_enable = true`` (desde que ``apply_cheats_after_load`` esteja
ligado) — sem abrir menu nenhum, mantendo o princípio do hub. O papel do
GameHub é garantir que esse arquivo exista com os itens marcados pelo
usuário.

Formato ``.cht`` = arquivo de configuração do próprio RetroArch:
``cheats = N`` + ``cheat<i>_desc/code/enable`` por item.

Fonte dos arquivos: ``libretro/libretro-database`` (``cht/<sistema>/<rom>.cht``),
a mesma base do updater oficial e a mesma convenção de nome das capas.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request

from .covers import _folders

# jsdelivr = CDN (rápido); raw.githubusercontent = original (fallback).
_URLS = (
    "https://cdn.jsdelivr.net/gh/libretro/libretro-database@master/"
    "cht/{folder}/{name}",
    "https://raw.githubusercontent.com/libretro/libretro-database/master/"
    "cht/{folder}/{name}",
)

# cache de library_name por core (retro_get_system_info é estável)
_LIB_CACHE: dict[str, str | None] = {}


class _SysInfo(ctypes.Structure):
    _fields_ = [
        ("library_name", ctypes.c_char_p),
        ("library_version", ctypes.c_char_p),
        ("valid_extensions", ctypes.c_char_p),
        ("need_fullpath", ctypes.c_bool),
        ("block_extract", ctypes.c_bool),
    ]


def library_name(cores_dir: str, core_id: str) -> str | None:
    """Nome real do core (``retro_get_system_info``) — é a pasta dos cheats.

    Ex.: ``snes9x-Z_libretro.so`` → ``Snes9x-Z``; ``fbneo`` → ``FinalBurn Neo``.
    É o mesmo nome que o RetroArch usa em saves/cheats, então bate sempre.
    """
    key = os.path.join(cores_dir, core_id)
    if key in _LIB_CACHE:
        return _LIB_CACHE[key]
    name = None
    path = os.path.join(cores_dir, f"{core_id}_libretro.so")
    if os.path.isfile(path):
        try:
            lib = ctypes.CDLL(path)
            lib.retro_get_system_info.argtypes = [ctypes.POINTER(_SysInfo)]
            info = _SysInfo()
            lib.retro_get_system_info(ctypes.byref(info))
            if info.library_name:
                name = info.library_name.decode("utf-8", "replace")
        except OSError:
            name = None
    _LIB_CACHE[key] = name
    return name


def cht_dir() -> str | None:
    """Pasta de cheats do RetroArch embutido (a que o auto-load lê)."""
    from . import ra_vendor
    home = ra_vendor.ra_home()
    if not home:
        return None
    return os.path.join(home, ".config", "retroarch", "cheats")


def game_file(rom_path: str) -> str:
    """Nome do .cht do jogo — mesma regra do RetroArch (stem + .cht)."""
    return os.path.splitext(os.path.basename(rom_path))[0] + ".cht"


def local_path(cores_dir: str, core_id: str, rom_path: str) -> str | None:
    """Caminho do .cht que o RetroArch vai ler pra este jogo (ou None)."""
    base = cht_dir()
    lib = library_name(cores_dir, core_id)
    if not base or not lib:
        return None
    return os.path.join(base, lib, game_file(rom_path))


def parse(text: str) -> list[dict]:
    """Lê um .cht → lista ``[{"i", "desc", "code", "enable"}]``."""
    total = 0
    fields: dict[int, dict[str, str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "cheats":
            try:
                total = max(total, int(value))
            except ValueError:
                pass
            continue
        if not key.startswith("cheat"):
            continue
        num, sep, field = key[5:].partition("_")
        if not sep or not num.isdigit():
            continue
        i = int(num)
        fields.setdefault(i, {})[field] = value
        total = max(total, i + 1)
    out: list[dict] = []
    for i in range(total):
        f = fields.get(i)
        if not f:
            continue
        out.append({
            "i": i,
            # o RetroArch cai pro código quando não há descrição
            "desc": f.get("desc") or f.get("code") or "?",
            "code": f.get("code", ""),
            "enable": f.get("enable", "false").lower() in ("true", "1"),
        })
    return out


def set_enabled(path: str, enabled) -> None:
    """Marca quais cheats ficam ligados, preservando o resto do arquivo.

    Só toca nas linhas ``cheat<i>_enable`` (mantém aspas/formatação originais);
    chaves ausentes são anexadas — a ordem não importa, o RetroArch lê por chave.
    """
    enabled = set(enabled)
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    wanted = {c["i"]: (c["i"] in enabled) for c in parse("\n".join(lines))}
    done: set[int] = set()
    for n, raw in enumerate(lines):
        line = raw.strip()
        if "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if not key.startswith("cheat"):
            continue
        num, sep, field = key[5:].partition("_")
        if sep != "_" or field != "enable" or not num.isdigit():
            continue
        i = int(num)
        if i not in wanted:
            continue
        quoted = '"' in line.split("=", 1)[1]
        value = "true" if wanted[i] else "false"
        lines[n] = (f'cheat{i}_enable = "{value}"' if quoted
                    else f"cheat{i}_enable = {value}")
        done.add(i)
    for i, on in wanted.items():
        if i not in done:
            lines.append(f'cheat{i}_enable = {"true" if on else "false"}')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _fetch_cht(folder: str, name: str) -> bytes | None:
    """Baixa um .cht da base oficial. None = não existe (404).

    Levanta a exceção de rede quando o servidor não respondeu com 404
    (aí o chamador mostra erro de conexão em vez de "sem cheat").
    """
    last_err: Exception | None = None
    answered_404 = False
    for tpl in _URLS:
        url = tpl.format(folder=urllib.parse.quote(folder),
                         name=urllib.parse.quote(name))
        req = urllib.request.Request(url, headers={"User-Agent": "GameHub"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                answered_404 = True
                continue
            last_err = e
        except urllib.error.URLError as e:
            last_err = e
    if answered_404:
        return None
    if last_err:
        raise last_err
    return None


def ensure(system: str, cores_dir: str, core_id: str,
           rom_path: str) -> str | None:
    """Garante o .cht do jogo na pasta do RetroArch. None = sem cheat.

    Ordem: já existe → cópia da base local (``~/.config/retroarch/cheats``,
    se o usuário tem os arquivos do updater) → download da base oficial.
    Pode levantar exceção de rede (``URLError``/``HTTPError``).
    """
    target = local_path(cores_dir, core_id, rom_path)
    if not target:
        return None
    if os.path.isfile(target):
        return target
    name = game_file(rom_path)
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    for folder in _folders(system):
        src = os.path.join(xdg, "retroarch", "cheats", folder, name)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(src, target)
            return target
    for folder in _folders(system):
        data = _fetch_cht(folder, name)
        if data is not None:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(data)
            return target
    return None
