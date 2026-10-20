"""Ícones de emuladores e sistemas — gerados em vetor + ícones reais dos consoles.

Badges de emulador: arredondado com a cor da marca + uma letra/label curta
(grid de jogos). Ícones de sistema: PNG vetorial de verdade por console
(``assets/systems/<sysid>.png`` — ver CREDITS.txt: KyleBing CC-BY 4.0,
Controllercons SIL OFL 1.1), usados na barra lateral e em
Configurações → Emuladores.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QLinearGradient, QPaintDevice,
                           QPainter, QPen, QPixmap)

# emulador → (label curta, cor de base da marca)
_EMU_STYLE: dict[str, tuple[str, str]] = {
    "shadPS4": ("4", "#6f5af6"),     # roxo/azul
    "RPCS3": ("3", "#2f6fd6"),       # azul
    "PCSX2": ("2", "#3aa0e0"),       # azul claro
    "DuckStation": ("PS", "#2fb58f"),  # verde-água
    "PPSSPP": ("P", "#4a86d8"),      # azul
    "Eden": ("E", "#3fb950"),        # verde
    "Azahar": ("A", "#e0763a"),      # laranja
    "Dolphin": ("D", "#2ec5e0"),     # ciano
    "Cemu": ("C", "#4f8ff7"),        # azul
    "xemu": ("X", "#57c24a"),        # verde
    "redream": ("r", "#e05548"),     # vermelho
    "RetroArch": ("RA", "#c64f9e"),  # magenta
    "PC": ("PC", "#8b97ab"),         # cinza p/ nativo
}

# cache: (nome, px, devicePixelRatio) → QPixmap
_cache: dict[tuple[str, int, float], QPixmap] = {}


def _round_rect(painter: QPainter, rect: QRectF, color: QColor,
                radius: float) -> None:
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, color.lighter(118))
    grad.setColorAt(1.0, color.darker(112))
    painter.setBrush(grad)
    painter.setPen(QPen(color.darker(160), 1))
    painter.drawRoundedRect(rect, radius, radius)


def emulator_icon(name: str, px: int = 32,
                  device: QPaintDevice | None = None) -> QPixmap:
    """Badge do emulador ( QPixmap quadrado, px × px, com DPI correto)."""
    dpr = float(device.devicePixelRatioF()) if device is not None else 1.0
    key = (name, px, dpr)
    if key in _cache:
        return _cache[key]
    label, base = _EMU_STYLE.get(name, (name[:1].upper() or "?", "#5b6b85"))
    size = max(8, int(px * dpr))
    pm = QPixmap(size, size)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    m = max(1.0, size * 0.06)
    _round_rect(p, QRectF(m, m, size - 2 * m, size - 2 * m),
                QColor(base), size * 0.24)
    # label centralizada
    f = QFont()
    f.setBold(True)
    f.setPixelSize(int(size * (0.52 if len(label) <= 2 else 0.42)))
    p.setFont(f)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, label)
    p.end()
    _cache[key] = pm
    return pm


def emulator_color(name: str) -> QColor:
    return QColor(_EMU_STYLE.get(name, ("", "#5b6b85"))[1])


def emulator_label(name: str) -> str:
    return _EMU_STYLE.get(name, (name, "#5b6b85"))[0]


def system_icon(sysid: str, px: int = 32,
                device: QPaintDevice | None = None,
                white: bool = False) -> QPixmap:
    """Ícone real do console (assets/systems/<sysid>.png), caixa quadrada.

    Escala suave mantendo a proporção, centralizado. Se o PNG não existir,
    cai no badge do emulador (nunca quebra a UI).
    """
    dpr = float(device.devicePixelRatioF()) if device is not None else 1.0
    key = ("__sys__", sysid, px, dpr, white)
    if key in _cache:
        return _cache[key]
    from .config import PROJECT_DIR
    sub = "white" if white else ""
    path = os.path.join(PROJECT_DIR, "assets", "systems", sub, f"{sysid}.png")
    size = max(8, int(px * dpr))
    if os.path.isfile(path):
        src = QPixmap(path)
        pm = QPixmap(size, size)
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.transparent)
        scaled = src.scaled(size, size, Qt.KeepAspectRatio,
                            Qt.SmoothTransformation)
        p = QPainter(pm)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap((size - scaled.width()) // 2,
                     (size - scaled.height()) // 2, scaled)
        p.end()
    else:
        from .catalog import SYSTEMS
        pm = emulator_icon(SYSTEMS.get(sysid, {}).get("emu", "?"), px, device)
    _cache[key] = pm
    return pm


def all_icon(px: int = 32, device: QPaintDevice | None = None) -> QPixmap:
    """Ícone do item "Todos" — grade de 4 quadradinhos (padrão apps/grid)."""
    dpr = float(device.devicePixelRatioF()) if device is not None else 1.0
    key = ("__all__", px, dpr)
    if key in _cache:
        return _cache[key]
    size = max(8, int(px * dpr))
    pm = QPixmap(size, size)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _round_rect(p, QRectF(0, 0, size, size), QColor("#33405e"), size * 0.24)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#9fc1ff"))
    m = size * 0.27
    d = size * 0.20
    g = size * 0.09
    for dx in (0.0, d + g):
        for dy in (0.0, d + g):
            p.drawRoundedRect(QRectF(m + dx, m + dy, d, d), size * 0.05,
                              size * 0.05)
    p.end()
    _cache[key] = pm
    return pm
