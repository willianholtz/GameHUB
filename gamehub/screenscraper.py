"""ScreenScraper.fr — segunda fonte de capas (busca por NOME, difusa).

Diferente do Libretro (match exato por nome de arquivo), o ScreenScraper faz
busca por nome + sistema e devolve capa mesmo quando o nome da ROM diverge.
Requer **credenciais de desenvolvedor** gratuitas (devid/devpassword) — não
tem modo anônimo. É usado como fallback: Libretro primeiro (livre), ScreenScraper
preenche os buracos quando configurado.

Endpoint: https://www.screenscraper.fr/api2/jeuInfos.php
Mapeamento systemeid numérico: oficial (ref. EmulationStation).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.screenscraper.fr/api2/jeuInfos.php"
SOFTNAME = "GameHub"

# system_id (do nosso catálogo) → systemeid do ScreenScraper
SYSTEM_ID: dict[str, int] = {
    "ps4": 210, "ps3": 59, "ps2": 58, "ps1": 57, "psp": 61,
    "switch": 225, "3ds": 17, "wii": 16, "wiiu": 18, "gc": 13,
    "n64": 14, "nds": 15, "famicom": 3, "fds": 106,
    "gba": 12, "gbc": 10, "gb": 9, "vb": 11, "snes": 4, "nes": 3,
    "genesis": 1, "ms": 2, "gg": 21, "mdcd": 20, "dc": 23, "saturn": 22,
    "pce": 31, "tgcd": 114, "sgx": 31, "lynx": 28,
    "a26": 26, "a52": 40, "vectrex": 102, "msx": 113,
    "wswan": 45, "ngp": 25, "neogeo": 142, "3do": 29,
    "arcade": 75, "xbox": 32,
}

# mídias de capa, em ordem de preferência (2D frontal > 3D > screenshot)
_MEDIA_PREF = ("box2D", "boxArt", "screenshot")
_REGION_PREF = ("us", "wor", "eu", "jp", "cus")


def configured(cfg) -> bool:
    """True se o usuário informou credenciais de dev do ScreenScraper."""
    return bool(cfg.get("ss_devid") and cfg.get("ss_devpassword"))


def _pick_media(medias: list) -> str | None:
    """Escolhe a melhor URL de capa numa lista de mídias, com fallback de
    preferência de mídia e de região."""
    for want in _MEDIA_PREF:
        for region in _REGION_PREF:
            for m in medias:
                if m.get("type") == want and m.get("region") == region:
                    url = m.get("url")
                    if url:
                        return url
        # qualquer região pra esse tipo
        for m in medias:
            if m.get("type") == want and m.get("url"):
                return m["url"]
    return None


def boxart_url(cfg, system: str, rom_path: str, timeout: int = 25) -> str | None:
    """URL da capa no ScreenScraper (None se falhar/sem credencial/sistema).

    Busca pelo nome do arquivo da ROM (sem extensão) + systemeid.
    """
    if not configured(cfg):
        return None
    sysid = SYSTEM_ID.get(system)
    if not sysid:
        return None
    stem = rom_path.rsplit("/", 1)[-1]
    stem = stem.rsplit(".", 1)[0]
    if not stem:
        return None

    params = {
        "devid": cfg.get("ss_devid", ""),
        "devpassword": cfg.get("ss_devpassword", ""),
        "softname": SOFTNAME,
        "output": "json",
        "systemeid": str(sysid),
        "romnom": stem,
    }
    # credenciais de usuário (opcional, sobe o limite de requisições)
    if cfg.get("ss_user") and cfg.get("ss_password"):
        params["user"] = cfg.get("ss_user")
        params["password"] = cfg.get("ss_password")

    url = API + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            raw = r.read()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError,
            TimeoutError):
        return None
    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except (ValueError, UnicodeDecodeError):
        return None

    jeu = (data.get("response") or {}).get("jeu") or {}
    if not jeu:
        return None
    medias = (jeu.get("medias") or {}).get("media") or []
    if isinstance(medias, dict):        # API devolve 1 item como objeto solo
        medias = [medias]
    return _pick_media(medias)
