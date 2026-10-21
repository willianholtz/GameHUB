"""Leitor mínimo de ISO9660 — só leitura, sem dependências.

Usado pra puxar ícone e título de PS3 **de dentro do .iso** (formato
PS3ISO da comunidade — makeps3iso/genps3iso gravam camada ISO9660 com
``/PS3_GAME/{PARAM.SFO,ICON0.PNG}``), como o RPCS3 faz ao montar a iso.

Dump bruto só-UDF (sem camada ISO9660) devolve ``None``: o jogo aparece
mesmo assim e a capa automática (ScreenScraper) cobre o ícone.
"""
from __future__ import annotations

import struct

SEC = 2048
_PVD_LBA = 16


def _u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def _record(buf: bytes, off: int) -> dict | None:
    """Um directory record (ECMA-119) → {name, extent, size, flags}."""
    if off + 34 > len(buf):
        return None
    ln = buf[off]
    if ln < 34 or off + ln > len(buf):
        return None
    rec = buf[off:off + ln]
    name_len = rec[32]
    if 33 + name_len > ln:
        return None
    raw = rec[33:33 + name_len]
    if raw in (b"\x00", b"\x01"):
        name = "." if raw == b"\x00" else ".."
    else:
        name = raw.decode("latin-1", "replace")
    return {
        "name": name.split(";")[0],
        "extent": _u32(rec, 2),
        "size": _u32(rec, 10),
        "flags": rec[25],
    }


def _dir_entries(f, rec: dict, max_sectors: int = 128) -> dict[str, dict]:
    """Entradas do diretório {nome.lower() → rec}, alinhadas a setor.

    Tolera escritores que gravam ``size = 0`` (lê setor a setor até o
    primeiro byte nulo) e respeita padding de fim de setor.
    """
    out: dict[str, dict] = {}
    extent, size = rec["extent"], rec["size"]
    f.seek(extent * SEC)
    n_sectors = max(1, -(-size // SEC)) if size else max_sectors
    n_sectors = min(n_sectors, max_sectors)
    data = f.read(n_sectors * SEC)
    for s in range(0, len(data), SEC):
        chunk = data[s:s + SEC]
        if not chunk or chunk[0] == 0:
            break
        off = 0
        while off < len(chunk):
            ln = chunk[off]
            if ln == 0:
                break  # padding de fim de setor → próximo setor
            e = _record(chunk, off)
            if e is None or ln % 2:
                break
            off += ln
            if e["name"] not in (".", ".."):
                out[e["name"].lower()] = e
        if size and (s // SEC) + 1 >= n_sectors:
            break
    return out


def read_file(iso: str, inner: str, max_mb: int = 8) -> bytes | None:
    """Bytes de ``inner`` (ex.: ``/PS3_GAME/ICON0.PNG``) dentro do ``iso``.

    ``None`` se o arquivo não existir, a iso não for ISO9660 ou algo
    estourar limite de sanidade — nunca lança exceção.
    """
    try:
        comps = [c for c in inner.replace("\\", "/").split("/") if c]
        if not comps:
            return None
        with open(iso, "rb") as f:
            pvd = f.read(((_PVD_LBA + 1) * SEC))[_PVD_LBA * SEC:]
            if len(pvd) < SEC or pvd[0] != 1 or pvd[1:6] != b"CD001":
                return None  # sem camada ISO9660 (ex.: dump só-UDF)
            root = _record(pvd, 156)
            if not root or not root["flags"] & 0x02:
                return None
            cur = root
            for comp in comps:
                nxt = _dir_entries(f, cur).get(comp.lower())
                if nxt is None:
                    return None
                cur = nxt
            if cur["size"] > max_mb * 1024 * 1024:
                return None
            f.seek(cur["extent"] * SEC)
            return f.read(cur["size"])
    except (OSError, struct.error, ValueError, IndexError):
        return None
