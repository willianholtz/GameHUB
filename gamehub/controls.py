"""Detecção de controles/gamepads conectados ao PC (regra 8).

Lê /proc/bus/input/devices e identifica entradas que parecem gamepads
(pela linha Name= e pela presença de um handler js*). Não depende de
nenhum Python extra — só leitura de /proc.
"""
from __future__ import annotations

import os
import re

# Padrões que indicam um controle de jogo (não teclado/mouse).
_PAD_RX = re.compile(
    r"xbox|dualshock|dualsense|playstation|ps[345] controller|"
    r"pro controller|joy-?con|8bitdo|logitech f|gamesir|stadia|"
    r"gamepad|game controller|fightstick|retro flag|saitek",
    re.I)


def detect_gamepads() -> list[str]:
    """Retorna nomes dos controles detectados ([] se nenhum)."""
    path = "/proc/bus/input/devices"
    if not os.path.isfile(path):
        return _fallback_by_id()
    pads: list[str] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return _fallback_by_id()
    for block in text.split("\n\n"):
        name = ""
        has_js = False
        for line in block.splitlines():
            if line.startswith("N: Name="):
                name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("H: Handlers=") and re.search(r"\bjs\d", line):
                has_js = True
        if not name:
            continue
        if has_js or _PAD_RX.search(name):
            if name not in pads:
                pads.append(name)
    return pads or _fallback_by_id()


def _fallback_by_id() -> list[str]:
    """Fallback: olha /dev/input/by-id por nomes de joystick."""
    d = "/dev/input/by-id"
    out: list[str] = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        low = fn.lower()
        if low.endswith("-event-joystick") or "joystick" in low or "gamepad" in low:
            clean = re.sub(r"[-_]", " ", fn)
            clean = re.sub(r"\s*(event|joystick|if0\d+)\s*", " ", clean,
                           flags=re.I).strip()
            if clean and clean not in out:
                out.append(clean)
    return out
