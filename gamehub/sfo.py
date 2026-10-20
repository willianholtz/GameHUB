"""Leitura de PARAM.SFO (PSF) do PS4/PS3."""
from __future__ import annotations

import struct


def read_sfo_title(path: str) -> str | None:
    """Lê o campo TITLE de um param.sfo/PARAM.SFO. None se falhar."""
    try:
        with open(path, "rb") as f:
            d = f.read()
        if d[:4] != b"\x00PSF":
            return None
        key_off, data_off, n = struct.unpack("<III", d[8:20])
        for i in range(n):
            ko, _fmt, ln, _ml, off = struct.unpack("<HHIII", d[20 + i * 16: 36 + i * 16])
            k = d[key_off + ko: d.index(b"\x00", key_off + ko)].decode("utf-8", "replace")
            if k == "TITLE":
                raw = d[data_off + off: data_off + off + ln]
                return raw.rstrip(b"\x00").decode("utf-8", "replace") or None
    except (OSError, struct.error, ValueError):
        return None
    return None
