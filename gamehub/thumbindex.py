"""Índice de nomes do servidor oficial de thumbnails do Libretro.

Por que existe este módulo:

1. O CDN antigo (jsDelivr/GitHub) estava **defasado**: 52 capas de PS2 lá
   contra **8.501** no servidor oficial, 168 vs 1.752 de PSP, 17 vs 1.345 de
   Xbox. E não dá pra listar pasta por lá (403), só bater URL às cegas.
2. Sem índice, o match é "stem exato → URL" e qualquer variação de nome
   (``Resident Evil 2 - Dual Shadow Ver. (USA)`` vs ``Resident Evil 2 (USA)``)
   vira 404. Com o índice em cache, o match vira **local**: normalizado +
   fuzzy, igual o RetroArch faz.
3. Arcade é caso aparte: a capa é ``Shock Troopers 2 (World).png`` mas a ROM é
   ``shocktr2.zip`` — nome curto. Só o ``.dat`` oficial do FBNeo resolve
   (``zip → descrição``), aí sim casamos a descrição com o índice.

Tudo fica em ``cache/thumbindex/`` (gitignorado). Rede só na primeira vez de
cada sistema (TTL de 30 dias); offline, o cache velho continua valendo e, se
não houver cache nenhum, o chamador cai no comportamento antigo de URL direta.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import time
import urllib.parse
import urllib.request

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_DIR, "cache", "thumbindex")
BASE = "https://thumbnails.libretro.com"

INDEX_TTL = 30 * 24 * 3600      # 30 dias
ARCADE_TTL = 30 * 24 * 3600
ARCADE_DAT = ("https://raw.githubusercontent.com/libretro/FBNeo/master/dats/"
              "FinalBurn%20Neo%20(ClrMame%20Pro%20XML,%20Arcade%20only).dat")

_PNG = re.compile(r"\.[Pp][Nn][Gg]$")

# caches em memória (a janela vive uma vez; disco cuida do resto)
_idx_mem: dict[str, dict[str, str] | None] = {}
_pre_mem: dict[str, dict[str, list[str]]] = {}
_arc_mem: dict[str, str] | None = None


def _norm(name: str) -> str:
    """Chave de comparação: sem extensão, sem tags (…), sem pontuação."""
    s = _PNG.sub("", name)
    s = re.sub(r"\([^)]*\)", " ", s)          # (USA) (Disc 1) (Rev 1)…
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)      # pontuação, acentos, _ e :
    return " ".join(s.lower().split())


def _index_path(folder: str) -> str:
    return os.path.join(CACHE_DIR, urllib.parse.quote(folder, safe="") + ".json")


def _fetch_listing(folder: str, timeout: int = 150) -> list[str] | None:
    """Lista os .png de uma pasta do servidor (índice HTML do Apache)."""
    url = f"{BASE}/{urllib.parse.quote(folder, safe='')}/Named_Boxarts/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", "replace")
    except (OSError, TimeoutError, ValueError):
        return None
    out = []
    for href in re.findall(r'href="([^"]+)"', html):
        name = urllib.parse.unquote(href)
        if not name.endswith(".png") or "/" in name or name.startswith("."):
            continue
        out.append(name)
    return out or None


def _load(folder: str) -> dict[str, str] | None:
    """Índice normalizado → nome real, com cache em disco (TTL)."""
    path = _index_path(folder)
    now = time.time()
    try:
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        if now - blob.get("ts", 0) < INDEX_TTL:
            return blob["files"]
    except (OSError, ValueError, KeyError):
        pass
    files = _fetch_listing(folder)
    if files is None:
        # rede falhou: usa cache velho se existir
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)["files"]
        except (OSError, ValueError, KeyError):
            return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "files": files}, f, ensure_ascii=False)
    return files


def index(folder: str) -> dict[str, str] | None:
    """Índice em memória (normalizado → nome real)."""
    if folder not in _idx_mem:
        files = _load(folder)
        if files is None:
            _idx_mem[folder] = None
        else:
            idx: dict[str, str] = {}
            for name in files:                 # primeiro vence (ordem do servidor)
                idx.setdefault(_norm(name), name)
            _idx_mem[folder] = idx
    return _idx_mem[folder]


def _prefixes(folder: str) -> dict[str, list[str]]:
    """Bucket por prefixo de 4 chars — reduz a busca fuzzy de 8k a ~dezenas."""
    if folder not in _pre_mem:
        idx = index(folder) or {}
        pre: dict[str, list[str]] = {}
        for key in idx:
            pre.setdefault(key[:4], []).append(key)
        _pre_mem[folder] = pre
    return _pre_mem[folder]


def match(folder: str, stem: str) -> str | None:
    """Melhor nome de capa pro stem da ROM, ou None.

    Exato normalizado primeiro (rápido, cobre a maioria); fuzzy só entre
    candidatos do mesmo prefixo, com corte alto pra não errar capa.
    """
    idx = index(folder)
    if not idx:
        return None
    key = _norm(stem)
    if not key:
        return None
    hit = idx.get(key)
    if hit:
        return hit
    pre = _prefixes(folder)
    cand: list[str] = []
    toks = key.split()
    for sig in {key[:4], toks[0][:4] if toks else ""} | {t[:4] for t in toks if len(t) >= 5}:
        cand.extend(pre.get(sig, []))
    if not cand:
        return None
    best = difflib.get_close_matches(key, cand, n=1, cutoff=0.88)
    return idx[best[0]] if best else None


# ---------- arcade (zip curto → descrição longa) ----------

def _load_arcade() -> dict[str, str] | None:
    global _arc_mem
    if _arc_mem is not None:
        return _arc_mem
    path = os.path.join(CACHE_DIR, "arcade_map.json")
    now = time.time()
    try:
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        if now - blob.get("ts", 0) < ARCADE_TTL:
            _arc_mem = blob["map"]
            return _arc_mem
    except (OSError, ValueError, KeyError):
        pass
    try:
        req = urllib.request.Request(ARCADE_DAT, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=240) as r:
            xml = r.read().decode("utf-8", "replace")
    except (OSError, TimeoutError, ValueError):
        return _arc_mem if _arc_mem is not None else None
    amap: dict[str, str] = {}
    for name, body in re.findall(
            r'<game name="([^"]+)"[^>]*>(.*?)</game>', xml, re.S):
        m = re.search(r"<description>(.*?)</description>", body, re.S)
        if not m:
            continue
        import html as _html
        desc = _html.unescape(m.group(1)).strip()
        amap[os.path.splitext(name)[0]] = desc
    if not amap:
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "map": amap}, f, ensure_ascii=False)
    _arc_mem = amap
    return _arc_mem


def arcade_desc(zip_stem: str) -> str | None:
    """``shocktr2`` → ``Shock Troopers 2 (World)`` (None se não mapeado)."""
    amap = _load_arcade()
    return amap.get(zip_stem) if amap else None


def warmup(folders: list[str], progress=None, total_hint: int = 0) -> None:
    """Pré-carrega índices antes do lote, com aviso no status."""
    for i, folder in enumerate(folders, 1):
        if progress and folder:
            progress(i, total_hint or len(folders), f"índice: {folder}")
        index(folder)
