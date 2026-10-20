"""Capas de jogos via Libretro Thumbnails (oficial, grátis, sem API key).

Baixa do **servidor oficial** ``thumbnails.libretro.com`` — o mesmo que o
RetroArch usa — e guarda no cache do projeto
(``cache/covers/<sistema>/<rom>.png``). Sistemas sem capa caem no
placeholder com gradiente (como já era).

O match não é mais "nome exato → URL" (isso perdia muito): o
:mod:`thumbindex` baixa o índice de nomes de cada sistema uma vez, e o
casamento vira local (normalizado + fuzzy), igual o RetroArch faz. Arcade é
caso aparte: a ROM é zip curto (``shocktr2.zip``) e a capa é nome longo
(``Shock Troopers 2 (World).png``) — resolve pelo ``.dat`` do FBNeo.

Ver ``thumbindex`` pro porquê do jsDelivr ter sido abandonado (espelho
defasado: 52 capas de PS2 lá, 8.501 aqui).
"""
from __future__ import annotations

import os
import re
import urllib.error
import urllib.parse
import urllib.request

from . import thumbindex
from .catalog import THUMB_SYSTEMS, THUMB_SYSTEM_ALIAS

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_DIR, "cache", "covers")
CDN = thumbindex.BASE

_PNG = b"\x89PNG\r\n\x1a\n"
_JPG = b"\xff\xd8\xff"

# Tags finais que a capa geralmente NÃO repete (revisão, disco, idioma,
# versão, beta…) — removidas uma a uma como fallback. A região ((USA),
# (Europe)…) é mantida, pois a capa costuma tê-la.
_NONREGION_TAIL = re.compile(
    r"\s*\((?:[Rr]ev\b[^)]*|[Dd]isc\b[^)]*|v\d[\d.]*|[A-Za-z]{2}(?:,[A-Za-z]{2})+"
    r"|[Bb]eta|[Pp]roto|[Dd]emo|[Aa]lt\d*|[Uu]nl)\)\s*$")


def _stem(rom_path: str) -> str:
    return os.path.splitext(os.path.basename(rom_path))[0]


def _candidates(stem: str) -> list[str]:
    """Nomes pra tentar, do mais exato pro mais limpo (fallback offline)."""
    out = [stem]
    s = stem
    for _ in range(3):
        m = _NONREGION_TAIL.search(s)
        if not m:
            break
        s = s[:m.start()].rstrip()
        out.append(s)
    # por último, só o título base (sem nenhuma tag final)
    base = re.sub(r"\s*\([^)]*\)\s*$", "", stem).strip()
    if base and base not in out:
        out.append(base)
    # dedup preservando ordem
    seen, res = set(), []
    for n in out:
        if n and n not in seen:
            seen.add(n)
            res.append(n)
    return res


def _folders(system: str) -> list[str]:
    """Pastas do servidor pra esse sistema (principal + aliases)."""
    name = THUMB_SYSTEMS.get(system)
    if not name:
        return []
    return [name] + list(THUMB_SYSTEM_ALIAS.get(system, ()))


def cover_name(system: str, rom_path: str) -> tuple[str, str] | None:
    """Resolve o nome real da capa via índice. ``(pasta, nome.png)`` ou None.

    É aqui que o match deixa de ser ingênuo: normaliza e faz fuzzy localmente
    (igual o RetroArch), em vez de bater URL exata e acumular 404.
    """
    stem = _stem(rom_path)
    if not stem:
        return None
    folders = _folders(system)
    if not folders:
        return None
    # arcade: zip curto -> descrição longa (dat do FBNeo)
    if system == "arcade":
        desc = thumbindex.arcade_desc(stem)
        if desc:
            for folder in folders:
                hit = thumbindex.match(folder, desc)
                if hit:
                    return folder, hit
        return None
    for folder in folders:
        hit = thumbindex.match(folder, stem)
        if hit:
            return folder, hit
    return None


def thumb_url(system: str, rom_path: str) -> str | None:
    """URL da capa se o sistema tiver capa automática (None se não tem).

    Sem rede: só diz se o sistema é coberto pelo Libretro (usado pra filtrar
    o lote). A resolução de fato é em :func:`cover_name`.
    """
    if _folders(system):
        return f"{CDN}/{urllib.parse.quote(_folders(system)[0])}/Named_Boxarts/"
    return None


def _urls(system: str, rom_path: str) -> list[str]:
    """URLs candidatas em ordem: resolução por índice → exato → fallbacks."""
    folders = _folders(system)
    if not folders:
        return []
    stem = _stem(rom_path)
    base = f"{CDN}/{{}}/Named_Boxarts/"
    out: list[str] = []
    hit = cover_name(system, rom_path)
    if hit:
        out.append(base.format(urllib.parse.quote(hit[0]))
                   + urllib.parse.quote(hit[1]))
    # fallback offline (sem índice): tenta nomes candidatos em todas as pastas
    for folder in folders:
        b = base.format(urllib.parse.quote(folder))
        for name in _candidates(stem):
            u = b + urllib.parse.quote(name) + ".png"
            if u not in out:
                out.append(u)
    return out


def cover_path(system: str, rom_path: str) -> str:
    """Caminho local no cache da capa."""
    return os.path.join(CACHE_DIR, system, _stem(rom_path) + ".png")


def has_cover(system: str, rom_path: str) -> bool:
    return os.path.isfile(cover_path(system, rom_path))


def _fetch(url: str, timeout: int) -> bytes | None:
    """Baixa uma URL e devolve os bytes, validando que é imagem real."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            data = r.read()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError,
            TimeoutError):
        return None
    if len(data) < 500:
        return None
    if not (data.startswith(_PNG) or data.startswith(_JPG)):
        return None
    return data


def download(game, cfg=None, timeout: int = 25) -> bool:
    """Baixa a capa pro cache. Libretro (índice) → ScreenScraper (fallback).

    True se baixou (ou já tinha).

    Com o índice disponível, tenta **só o nome resolvido** (1 requisição, não
    4~8 às cegas). Sem índice (offline, primeira vez), cai nos candidatos
    antigos — comportamento antigo preservado.
    """
    if has_cover(game.system, game.path):
        return True
    dest = cover_path(game.system, game.path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    # 1) Libretro: índice resolve o nome certo → 1 GET
    hit = cover_name(game.system, game.path)
    if hit:
        url = (f"{CDN}/{urllib.parse.quote(hit[0])}/Named_Boxarts/"
               f"{urllib.parse.quote(hit[1])}")
        data = _fetch(url, timeout)
        if data:
            with open(dest, "wb") as f:
                f.write(data)
            return True
    elif _folders(game.system) and thumbindex.index(_folders(game.system)[0]):
        # índice carregado e NÃO achou nome → miss definitivo, não insiste
        pass
    else:
        # offline / sem índice: tenta os candidatos clássicos
        for url in _urls(game.system, game.path):
            data = _fetch(url, timeout)
            if data:
                with open(dest, "wb") as f:
                    f.write(data)
                return True

    # 2) ScreenScraper (busca difusa por nome) — se configurado
    if cfg is not None:
        from . import screenscraper
        if screenscraper.configured(cfg):
            ss_url = screenscraper.boxart_url(cfg, game.system, game.path,
                                              timeout=timeout)
            if ss_url:
                data = _fetch(ss_url, timeout)
                if data:
                    with open(dest, "wb") as f:
                        f.write(data)
                    return True
    return False


def download_many(games, cfg=None, progress=None, stop_flag=None) -> int:
    """Baixa capas de vários jogos. Retorna quantas deram certo.

    ``cfg`` habilita o ScreenScraper como fallback. ``progress(i, total,
    title)`` opcional; ``stop_flag`` (callable) aborta.
    """
    from . import screenscraper
    use_ss = cfg is not None and screenscraper.configured(cfg)
    games = [g for g in games if not has_cover(g.system, g.path)
             and (thumb_url(g.system, g.path)
                  or (use_ss and g.system in screenscraper.SYSTEM_ID))]
    total = len(games)
    if not games:
        return 0

    # pré-carrega o índice de cada sistema (1 requisição por sistema, não
    # uma por jogo) — aí o match é local e rápido
    folders: list[str] = []
    for g in games:
        for f in _folders(g.system):
            if f not in folders:
                folders.append(f)
    if progress:
        progress(0, total, "índice de capas")
    thumbindex.warmup(folders)
    if stop_flag and stop_flag():
        return 0

    ok = 0
    for i, g in enumerate(games, 1):
        if stop_flag and stop_flag():
            break
        if progress:
            progress(i, total, g.title)
        if download(g, cfg):
            ok += 1
    return ok
