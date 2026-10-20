"""Navegação por controle (gamepad) na interface do GameHub.

Lê ``/dev/input/js*`` direto (API de joystick do Linux — sem dependência) e
converte em ações da grade: mover seleção, jogar, voltar, abrir config.

Mapeamento (Xbox no Linux):
- D-pad / analógico esquerdo → mover seleção (com auto-repeat ao segurar)
- A (✕)  → jogar
- B (◯)  → voltar / limpar seleção
- Start  → configurações

Se não houver controle, a thread simplesmente não faz nada (não quebra nada).
"""
from __future__ import annotations

import os
import select
import struct
import threading
import time

from PySide6.QtCore import QThread, Signal

# linux/joystick.h
JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80
_FMT = struct.Struct("IhBB")   # time(u32), value(s16), type(u8), number(u8)

_AXIS_THRESHOLD = 16000
_REPEAT_DELAY = 0.30   # espera antes de começar a repetir
_REPEAT_RATE = 0.09    # intervalo da repetição

BTN_A, BTN_B, BTN_X, BTN_Y = 0, 1, 2, 3
BTN_SELECT, BTN_START, BTN_GUIDE = 6, 7, 8
# d-pad pode vir como botões (11..14) — (dx, dy)
BTN_DPAD = {11: (0, -1), 12: (0, 1), 13: (-1, 0), 14: (1, 0)}


def find_joystick() -> str | None:
    """Primeiro controle encontrado em /dev/input/js*, ou None."""
    for n in range(4):
        p = f"/dev/input/js{n}"
        if os.path.exists(p):
            return p
    return None


def controller_name() -> str | None:
    """Nome legível do controle (via device name), se houver."""
    dev = find_joystick()
    if not dev:
        return None
    try:
        with open("/proc/bus/input/devices", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        # procura o nome do joystick ( heuristic: linha "Handlers=... jsN" )
        for block in txt.split("\n\n"):
            if f" {os.path.basename(dev)}" in block or f"js" in block:
                for line in block.splitlines():
                    if line.startswith("N: Name="):
                        return line.split("=", 2)[-1].strip().strip('"')
    except OSError:
        pass
    return os.path.basename(dev)


class GamepadThread(QThread):
    move = Signal(int, int)   # (dx, dy) mover seleção na grade
    activate = Signal()       # A → jogar
    back = Signal()           # B → voltar/limpar
    menu = Signal()           # Start → configurações

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = threading.Event()
        self._dev = find_joystick()

    def run(self) -> None:
        if not self._dev:
            return
        try:
            fd = os.open(self._dev, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            return
        held = (0, 0)
        next_repeat = 0.0
        try:
            while not self._stop.is_set():
                # poll curto quando segurando direção (pro auto-repeat)
                timeout = 0.02 if held != (0, 0) else 0.25
                r, _, _ = select.select([fd], [], [], timeout)
                now = time.monotonic()
                if r:
                    try:
                        data = os.read(fd, _FMT.size)
                    except OSError:
                        break
                    if len(data) < _FMT.size:
                        break
                    _, value, etype, number = _FMT.unpack(data)
                    etype &= ~JS_EVENT_INIT
                    if etype == JS_EVENT_BUTTON:
                        self._button(number, value)
                    elif etype == JS_EVENT_AXIS:
                        prev = held
                        held = self._axis(number, value, held)
                        if held != prev and held != (0, 0):
                            self.move.emit(*held)
                            next_repeat = now + _REPEAT_DELAY
                # auto-repeat enquanto a direção está segurada
                if held != (0, 0) and now >= next_repeat:
                    self.move.emit(*held)
                    next_repeat = now + _REPEAT_RATE
        finally:
            os.close(fd)

    def _button(self, number: int, value: int) -> None:
        if value != 1:            # só no instante do pressionar
            return
        if number == BTN_A:
            self.activate.emit()
        elif number == BTN_B:
            self.back.emit()
        elif number == BTN_START:
            self.menu.emit()
        elif number in BTN_DPAD:
            self.move.emit(*BTN_DPAD[number])

    def _axis(self, number: int, value: int, held):
        # analógico esquerdo (0=x,1=y) e hat/d-pad (6=x,7=y)
        dx, dy = held
        if number in (0, 6):
            if value > _AXIS_THRESHOLD:
                dx = 1
            elif value < -_AXIS_THRESHOLD:
                dx = -1
            else:
                dx = 0
        elif number in (1, 7):
            if value > _AXIS_THRESHOLD:
                dy = 1
            elif value < -_AXIS_THRESHOLD:
                dy = -1
            else:
                dy = 0
        return (dx, dy)

    def stop(self) -> None:
        self._stop.set()
