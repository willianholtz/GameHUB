"""Metadados por jogo via ``gamelist.xml`` (padrão EmulationStation/ES-DE).

Formato:

    <gameList>
      <game>
        <path>./sub/Jogo.sfc</path>
        <name>Nome Bonito</name>
        <desc>Descrição…</desc>
        <genre>Ação</genre>
        <rating>0.85</rating>   <!-- 0..1 -->
      </game>
    </gameList>

O XML mora na pasta raiz da ROM; o ``<path>`` é relativo a ela. Qualquer
XML quebrado vira ``{}`` — a biblioteca nunca falha por causa disso.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

_META_TAGS = ("name", "desc", "genre")


def _norm(path: str) -> str:
    """``"./sub/Jogo.sfc"`` → ``"sub/jogo.sfc"`` (barras, sem ./, minúsculas)."""
    p = path.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/").lower()


def load(root: str) -> dict[str, dict]:
    """``gamelist.xml`` de ``root`` → ``{caminho → {name, desc, genre, rating}}``."""
    f = os.path.join(root, "gamelist.xml")
    if not os.path.isfile(f):
        return {}
    try:
        tree = ET.parse(f)
    except (ET.ParseError, OSError, ValueError):
        return {}
    out: dict[str, dict] = {}
    for g in tree.getroot().iter("game"):
        el = g.find("path")
        if el is None or not (el.text or "").strip():
            continue
        meta: dict = {}
        for tag in _META_TAGS:
            t = g.find(tag)
            if t is not None and (t.text or "").strip():
                meta[tag] = t.text.strip()
        r = g.find("rating")
        if r is not None:
            try:
                meta["rating"] = max(0.0, min(1.0, float((r.text or "").strip())))
            except ValueError:
                pass  # nota lixo: só ignora, o resto do meta vale
        out[_norm(el.text)] = meta
    return out


def apply(games: list, root: str) -> None:
    """Preenche ``game.meta`` (e o título, quando o gamelist tem ``<name>``)."""
    meta_map = load(root)
    if not meta_map:
        return
    for g in games:
        # caminho lançável (arquivos) ou a pasta do jogo (PS3/PS4)
        for key in (g.path, g.dir):
            m = meta_map.get(_norm(os.path.relpath(key, root)))
            if m:
                g.meta.update(m)
                if m.get("name"):
                    g.title = m["name"]
                break
