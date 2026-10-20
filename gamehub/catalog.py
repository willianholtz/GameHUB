"""Catálogo de sistemas e emuladores do GameHub.

- SYSTEMS: sistemas suportados (extensões, tipo de scanner, emulador padrão).
- EMULATORS: emuladores standalone esperados em ``cores/`` (AppImage ou binário).

O campo ``detect`` é regex aplicada ao nome do arquivo (case-insensitive) pra
auto-detectar qual AppImage é qual quando você joga na pasta ``cores/``.
``args`` usa ``{game}`` como placeholder do caminho do jogo.
"""
from __future__ import annotations

# kind: "files"     → acha arquivos por extensão (recursivo)
#       "folder_sfo"→ pastas com sce_sys/param.sfo (PS4)
#       "folder_ps3"→ pastas com USRDIR/eboot.bin (RPCS3)
# ra_core: core do RetroArch usado como fallback quando não há standalone.
SYSTEMS: dict[str, dict] = {
    "ps4": {
        "name": "PlayStation 4", "kind": "folder_sfo", "ext": [],
        "emu": "shadPS4", "ra_folder": "Sony - Playstation 4",
    },
    "ps3": {
        "name": "PlayStation 3", "kind": "folder_ps3", "ext": [],
        "emu": "RPCS3", "ra_folder": "",
    },
    "ps2": {
        "name": "PlayStation 2", "kind": "files",
        "ext": [".iso", ".chd", ".bin", ".cso", ".img", ".gz"],
        "emu": "PCSX2", "ra_folder": "Sony - Playstation 2",
    },
    "ps1": {
        "name": "PlayStation", "kind": "files",
        "ext": [".bin", ".cue", ".chd", ".pbp", ".img", ".iso"],
        "emu": "DuckStation", "ra_folder": "Sony - Playstation",
    },
    "psp": {
        "name": "PlayStation Portable", "kind": "files",
        "ext": [".iso", ".cso", ".chd"],
        "emu": "PPSSPP", "ra_folder": "Sony - Playstation Portable",
    },
    "switch": {
        "name": "Nintendo Switch", "kind": "files",
        "ext": [".nsp", ".xci", ".nro"],
        "emu": "Eden", "ra_folder": "Nintendo - Nintendo Switch",
    },
    "3ds": {
        "name": "Nintendo 3DS", "kind": "files",
        "ext": [".3ds", ".cci", ".3dex", ".cxi"],
        "emu": "Azahar", "ra_folder": "Nintendo - Nintendo 3DS",
    },
    "wii": {
        "name": "Nintendo Wii", "kind": "files",
        "ext": [".wbfs", ".iso", ".rvz", ".gcz", ".ciso"],
        "emu": "Dolphin", "ra_folder": "Nintendo - Nintendo Wii",
    },
    "gc": {
        "name": "Nintendo GameCube", "kind": "files",
        "ext": [".gcm", ".iso", ".rvz", ".gcz", ".ciso"],
        "emu": "Dolphin", "ra_folder": "Nintendo - Gamecube",
    },
    "n64": {
        "name": "Nintendo 64", "kind": "files",
        "ext": [".z64", ".n64", ".v64", ".zip"],
        "emu": "RetroArch", "ra_core": "parallel_n64",
        "ra_folder": "Nintendo - Nintendo 64",
    },
    "nds": {
        "name": "Nintendo DS", "kind": "files",
        "ext": [".nds"],
        "emu": "RetroArch", "ra_core": "melonds",
        "ra_folder": "Nintendo - Nintendo DS",
    },
    "famicom": {
        "name": "Famicom", "kind": "files",
        "ext": [".nes", ".fds", ".zip"],
        "emu": "RetroArch", "ra_core": "mesen",
        "ra_folder": "Nintendo - Famicom",
    },
    "fds": {
        "name": "Famicom Disk System", "kind": "files",
        "ext": [".fds"],
        "emu": "RetroArch", "ra_core": "mesen",
        "ra_folder": "Nintendo - Family Computer Disk System",
    },
    "gba": {
        "name": "Game Boy Advance", "kind": "files",
        "ext": [".gba", ".zip"],
        "emu": "RetroArch", "ra_core": "mgba",
        "ra_folder": "Nintendo - Game Boy Advance",
    },
    "gbc": {
        "name": "Game Boy Color", "kind": "files",
        "ext": [".gbc", ".zip"],
        "emu": "RetroArch", "ra_core": "gambatte",
        "ra_folder": "Nintendo - Game Boy Color",
    },
    "gb": {
        "name": "Game Boy", "kind": "files",
        "ext": [".gb", ".zip"],
        "emu": "RetroArch", "ra_core": "gambatte",
        "ra_folder": "Nintendo - Game Boy",
    },
    "vb": {
        "name": "Virtual Boy", "kind": "files",
        "ext": [".vb", ".zip"],
        "emu": "RetroArch", "ra_core": "mednafen_vb",
        "ra_folder": "Nintendo - Virtual Boy",
    },
    "snes": {
        "name": "Super Nintendo", "kind": "files",
        "ext": [".sfc", ".smc", ".zip"],
        "emu": "RetroArch", "ra_core": "bsnes",
        "ra_folder": ["Nintendo - Super Nintendo Entertainment System",
                      "Nintendo - Sufami Turbo"],
    },
    "nes": {
        "name": "Nintendo Entertainment System", "kind": "files",
        "ext": [".nes", ".zip"],
        "emu": "RetroArch", "ra_core": "mesen",
        "ra_folder": "Nintendo - Nintendo Entertainment System",
    },
    "wiiu": {
        "name": "Nintendo Wii U", "kind": "files",
        "ext": [".wua", ".wud", ".wux", ".rpx", ".wiiu"],
        "emu": "Cemu", "ra_folder": "Nintendo - Nintendo Wii U",
    },
    "genesis": {
        "name": "Sega Mega Drive", "kind": "files",
        "ext": [".md", ".gen", ".bin", ".smd", ".zip"],
        "emu": "RetroArch", "ra_core": "genesis_plus_gx",
        "ra_folder": ["Sega - Mega Drive - Genesis", "Sega - Naomi",
                      "Sega - Atomiswave"],
    },
    "ms": {
        "name": "Sega Master System", "kind": "files",
        "ext": [".sms", ".zip"],
        "emu": "RetroArch", "ra_core": "genesis_plus_gx",
        "ra_folder": "Sega - Master System - Mark III",
    },
    "gg": {
        "name": "Sega Game Gear", "kind": "files",
        "ext": [".gg", ".zip"],
        "emu": "RetroArch", "ra_core": "genesis_plus_gx",
        "ra_folder": "Sega - Game Gear",
    },
    "mdcd": {
        "name": "Sega Mega CD", "kind": "files",
        "ext": [".chd", ".cue", ".bin", ".iso"],
        "emu": "RetroArch", "ra_core": "genesis_plus_gx",
        "ra_folder": "Sega - CD",
    },
    "dc": {
        "name": "Sega Dreamcast", "kind": "files",
        "ext": [".gdi", ".chd", ".cdi", ".mcd"],
        "emu": "redream", "ra_folder": "Sega - Dreamcast",
    },
    "saturn": {
        "name": "Sega Saturn", "kind": "files",
        "ext": [".chd", ".cue", ".bin", ".iso"],
        "emu": "RetroArch", "ra_core": "mednafen_saturn",
        "ra_folder": "Sega - Saturn",
    },
    "pce": {
        "name": "PC Engine", "kind": "files",
        "ext": [".pce", ".cue", ".bin", ".chd", ".iso"],
        "emu": "RetroArch", "ra_core": "mednafen_supergrafx",
        "ra_folder": ["NEC - PC Engine", "NEC - TurboGrafx 16"],
    },
    "tgcd": {
        "name": "PC Engine CD", "kind": "files",
        "ext": [".cue", ".bin", ".chd", ".iso"],
        "emu": "RetroArch", "ra_core": "mednafen_supergrafx",
        "ra_folder": ["NEC - PC Engine CD", "NEC - TurboGrafx CD"],
    },
    "sgx": {
        "name": "SuperGrafx", "kind": "files",
        "ext": [".pce", ".cue", ".bin"],
        "emu": "RetroArch", "ra_core": "mednafen_supergrafx",
        "ra_folder": "NEC - PC Engine SuperGrafx",
    },
    "lynx": {
        "name": "Atari Lynx", "kind": "files",
        "ext": [".lnx", ".zip"],
        "emu": "RetroArch", "ra_core": "mednafen_lynx",
        "ra_folder": "Atari - Lynx",
    },
    "a26": {
        "name": "Atari 2600", "kind": "files",
        "ext": [".a26", ".bin", ".zip"],
        "emu": "RetroArch", "ra_core": "stella2014",
        "ra_folder": "Atari - 2600",
    },
    "a52": {
        "name": "Atari 5200", "kind": "files",
        "ext": [".a52", ".atr", ".bin"],
        "emu": "RetroArch", "ra_core": "atari800",
        "ra_folder": "Atari - 5200",
    },
    "vectrex": {
        "name": "Vectrex", "kind": "files",
        "ext": [".vec", ".bin", ".dat", ".zip"],
        "emu": "RetroArch", "ra_core": "vecx",
        "ra_folder": "GCE - Vectrex",
    },
    "msx": {
        "name": "MSX2", "kind": "files",
        "ext": [".rom", ".mx1", ".mx2", ".dsk", ".zip"],
        "emu": "RetroArch", "ra_core": "bluemsx",
        "ra_folder": "Microsoft - MSX2",
    },
    "wswan": {
        "name": "WonderSwan", "kind": "files",
        "ext": [".ws", ".wsc", ".zip"],
        "emu": "RetroArch", "ra_core": "mednafen_wswan",
        "ra_folder": ["Bandai - WonderSwan", "Bandai - WonderSwan Color"],
    },
    "ngp": {
        "name": "Neo Geo Pocket", "kind": "files",
        "ext": [".ngp", ".ngc", ".zip"],
        "emu": "RetroArch", "ra_core": "mednafen_ngp",
        "ra_folder": ["SNK - Neo Geo Pocket", "SNK - Neo Geo Pocket Color"],
    },
    "neogeo": {
        "name": "Neo Geo (arcade)", "kind": "files",
        "ext": [".zip"],
        "emu": "RetroArch", "ra_core": "fbneo",
        "ra_folder": "SNK - Neo Geo",
    },
    "3do": {
        "name": "3DO", "kind": "files",
        "ext": [".bin", ".cue", ".chd", ".iso"],
        "emu": "RetroArch", "ra_core": "opera",
        "ra_folder": "",
    },
    "arcade": {
        "name": "Arcade (FBNeo)", "kind": "files",
        "ext": [".zip"],
        "emu": "RetroArch", "ra_core": "fbneo",
        "ra_folder": "FBNeo - Arcade Games",
    },
    "xbox": {
        "name": "Xbox", "kind": "files",
        "ext": [".iso", ".xiso"],
        "emu": "xemu", "ra_folder": "Microsoft - Xbox",
    },
    "pc": {
        "name": "PC (nativo)", "kind": "manual", "ext": [],
        "emu": "", "ra_folder": "",
    },
}

# Nome curto de exibição (sidebar, badge). Sem o prefixo "Nintendo -",
# "Sega -", "Sony -" etc. Fallback: o "name" completo do SYSTEMS.
SHORT_NAMES: dict[str, str] = {
    "ps4": "PS4", "ps3": "PS3", "ps2": "PS2", "ps1": "PS1", "psp": "PSP",
    "switch": "Switch", "3ds": "3DS", "wii": "Wii", "gc": "GameCube",
    "n64": "N64", "nds": "DS", "famicom": "Famicom", "fds": "FDS",
    "gba": "GBA", "gbc": "GBC", "gb": "GB", "vb": "Virtual Boy",
    "snes": "SNES", "nes": "NES", "wiiu": "Wii U",
    "genesis": "Mega Drive", "ms": "Master System", "gg": "Game Gear",
    "mdcd": "Mega CD", "dc": "Dreamcast", "saturn": "Saturn",
    "pce": "PC Engine", "tgcd": "PC Engine CD", "sgx": "SuperGrafx",
    "lynx": "Lynx", "a26": "2600", "a52": "5200", "vectrex": "Vectrex",
    "msx": "MSX2", "wswan": "WonderSwan", "ngp": "Neo Geo Pocket",
    "neogeo": "Neo Geo", "3do": "3DO", "arcade": "Arcade", "xbox": "Xbox",
    "pc": "PC",
}


def sys_short(sysid: str) -> str:
    """Nome curto do sistema (badge/sidebar); cai no nome completo."""
    return SHORT_NAMES.get(sysid) or SYSTEMS.get(sysid, {}).get("name", sysid)

# Emuladores standalone. "detect": regex no nome do arquivo em cores/.
# "path": binário no PATH usado como fallback (quando instalado no sistema).
EMULATORS: dict[str, dict] = {
    "shadPS4": {"detect": r"shadps4", "args": ["{game}"], "path": "shadps4"},
    "RPCS3": {"detect": r"rpcs3", "args": ["--no-gui", "{game}"], "path": "rpcs3"},
    "PCSX2": {"detect": r"pcsx2", "args": ["-fastboot", "{game}"], "path": "pcsx2",
              "fullscreen": ["-fullscreen"]},
    "DuckStation": {"detect": r"duckstation", "args": ["-batch", "-fastboot", "{game}"],
                    "path": "duckstation", "fullscreen": ["-fullscreen"]},
    "PPSSPP": {"detect": r"ppsspp", "args": ["{game}"], "path": "PPSSPPSDL"},
    "Eden": {"detect": r"eden", "args": ["{game}"], "path": "eden"},
    "Azahar": {"detect": r"azahar", "args": ["{game}"], "path": "azahar"},
    "Dolphin": {"detect": r"dolphin", "args": ["-b", "-e", "{game}"], "path": "dolphin-emu",
                "fullscreen": ["-f"]},
    "Cemu": {"detect": r"cemu", "args": ["-g", "{game}"], "path": "cemu"},
    "xemu": {"detect": r"^xemu", "args": ["-dvd", "{game}"], "path": "xemu"},
    "redream": {"detect": r"redream", "args": ["-i", "{game}"], "path": "redream"},
    "RetroArch": {"detect": r"retroarch", "args": ["-L", "{core}", "{game}"],
                  "path": "retroarch"},
}

# Catálogo de cores do RetroArch: core → nome amigável + sistemas compatíveis.
# Serve pra (a) listar só cores válidos por emulador, (b) permitir instalar/
# atualizar via buildbot oficial do Libretro.
CORES: dict[str, dict] = {
    "mesen": {"name": "Mesen", "systems": ["nes", "famicom", "fds"]},
    "nestopia": {"name": "Nestopia", "systems": ["nes", "famicom", "fds"]},
    "fceumm": {"name": "FCEUmm", "systems": ["nes", "famicom", "fds"]},
    "bsnes": {"name": "bsnes", "systems": ["snes"]},
    "snes9x": {"name": "Snes9x", "systems": ["snes"]},
    "snes9x2010": {"name": "Snes9x 2010", "systems": ["snes"]},
    "gambatte": {"name": "Gambatte", "systems": ["gb", "gbc"]},
    "sameboy": {"name": "SameBoy", "systems": ["gb", "gbc"]},
    "mgba": {"name": "mGBA", "systems": ["gba", "gb", "gbc"]},
    "vbam": {"name": "VBA-M", "systems": ["gba"]},
    "gpsp": {"name": "gpSP", "systems": ["gba"]},
    "parallel_n64": {"name": "ParaLLEl N64", "systems": ["n64"]},
    "mupen64plus_next": {"name": "Mupen64Plus-Next", "systems": ["n64"]},
    "melonds": {"name": "melonDS", "systems": ["nds"]},
    "desmume": {"name": "DeSmuME", "systems": ["nds"]},
    "dolphin": {"name": "Dolphin", "systems": ["gc", "wii"]},
    "genesis_plus_gx": {"name": "Genesis Plus GX",
                        "systems": ["genesis", "ms", "gg", "mdcd"]},
    "picodrive": {"name": "Picodrive", "systems": ["genesis", "ms", "gg", "mdcd"]},
    "flycast": {"name": "Flycast", "systems": ["dc"]},
    "mednafen_saturn": {"name": "Beetle Saturn", "systems": ["saturn"]},
    "yabause": {"name": "Yabause", "systems": ["saturn"]},
    "mednafen_psx": {"name": "Beetle PSX", "systems": ["ps1"]},
    "swanstation": {"name": "SwanStation", "systems": ["ps1"]},
    "pcsx_rearmed": {"name": "PCSX ReARMed", "systems": ["ps1"]},
    "ppsspp": {"name": "PPSSPP", "systems": ["psp"]},
    "pcsx2": {"name": "PCSX2", "systems": ["ps2"]},
    "mednafen_pce_fast": {"name": "Beetle PCE Fast", "systems": ["pce", "tgcd"]},
    "mednafen_supergrafx": {"name": "Beetle SuperGrafx",
                            "systems": ["pce", "tgcd", "sgx"]},
    "mednafen_lynx": {"name": "Beetle Lynx", "systems": ["lynx"]},
    "mednafen_wswan": {"name": "Beetle WonderSwan", "systems": ["wswan"]},
    "mednafen_ngp": {"name": "Beetle Neo Geo Pocket", "systems": ["ngp"]},
    "mednafen_vb": {"name": "Beetle Virtual Boy", "systems": ["vb"]},
    "stella": {"name": "Stella", "systems": ["a26"]},
    "stella2014": {"name": "Stella 2014", "systems": ["a26"]},
    "atari800": {"name": "Atari800", "systems": ["a52"]},
    "vecx": {"name": "Vecx", "systems": ["vectrex"]},
    "bluemsx": {"name": "blueMSX", "systems": ["msx"]},
    "fbneo": {"name": "FinalBurn Neo", "systems": ["arcade", "neogeo"]},
    "mame2003_plus": {"name": "MAME 2003-Plus", "systems": ["arcade"]},
    "opera": {"name": "Opera (3DO)", "systems": ["3do"]},
}


def cores_for_system(sysid: str) -> list[tuple[str, str]]:
    """Cores compatíveis com um sistema: [(core_id, nome_amigável), ...]."""
    out = [(cid, cdef["name"]) for cid, cdef in CORES.items()
           if sysid in cdef["systems"]]
    return sorted(out, key=lambda t: t[1].lower())


# Nome da pasta no repositório Libretro Thumbnails (oficial, grátis, sem API).
# Difere do ra_folder em alguns sistemas (casing/nomenclatura) — por isso um
# mapa dedicado. Sistemas sem entrada (switch, pc) não têm capa automática.
THUMB_SYSTEMS: dict[str, str] = {
    "ps1": "Sony - PlayStation",
    "ps2": "Sony - PlayStation 2",
    "ps3": "Sony - PlayStation 3",
    "ps4": "Sony - PlayStation 4",
    "psp": "Sony - PlayStation Portable",
    "3ds": "Nintendo - Nintendo 3DS",
    "wii": "Nintendo - Wii",
    "wiiu": "Nintendo - Wii U",
    "gc": "Nintendo - GameCube",
    "n64": "Nintendo - Nintendo 64",
    "nds": "Nintendo - Nintendo DS",
    "nes": "Nintendo - Nintendo Entertainment System",
    "famicom": "Nintendo - Nintendo Entertainment System",  # melhor esforço
    "fds": "Nintendo - Family Computer Disk System",
    "snes": "Nintendo - Super Nintendo Entertainment System",
    "gb": "Nintendo - Game Boy",
    "gbc": "Nintendo - Game Boy Color",
    "gba": "Nintendo - Game Boy Advance",
    "vb": "Nintendo - Virtual Boy",
    "genesis": "Sega - Mega Drive - Genesis",
    "ms": "Sega - Master System - Mark III",
    "gg": "Sega - Game Gear",
    "mdcd": "Sega - Mega-CD - Sega CD",
    "dc": "Sega - Dreamcast",
    "saturn": "Sega - Saturn",
    "pce": "NEC - PC Engine - TurboGrafx 16",
    "tgcd": "NEC - PC Engine CD - TurboGrafx-CD",
    "sgx": "NEC - PC Engine SuperGrafx",
    "lynx": "Atari - Lynx",
    "a26": "Atari - 2600",
    "a52": "Atari - 5200",
    "vectrex": "GCE - Vectrex",
    "msx": "Microsoft - MSX2",
    "wswan": "Bandai - WonderSwan",
    "ngp": "SNK - Neo Geo Pocket",
    "neogeo": "SNK - Neo Geo",
    "3do": "The 3DO Company - 3DO",
    "arcade": "FBNeo - Arcade Games",
    "xbox": "Microsoft - Xbox",
}

# Pastas alternativas no servidor oficial pro MESMO sistema (o repo GitHub
# e o thumbnails.libretro.com não usam sempre o mesmo nome). Cada pasta é
# tentada em ordem até achar capa. **Só nome que existe no servidor.**
THUMB_SYSTEM_ALIAS: dict[str, tuple[str, ...]] = {
    "arcade": ("MAME",),
    "msx": ("Microsoft - MSX2",),
    "ngp": ("SNK - Neo Geo Pocket Color",),
    "wswan": ("Bandai - WonderSwan Color",),
}

# Endereço do RetroArch (cores).
RA_CONFIG = "~/.config/retroarch"
RA_CORES = RA_CONFIG + "/cores"
