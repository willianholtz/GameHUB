"""Configuração do GameHub.

Tudo fica dentro do projeto (``config/front.json``) — nada é escrito em
``~/.config`` ou ``~/.local`` fora do que os próprios emuladores fazem.
"""
from __future__ import annotations

import json
import os
import re
import shutil

from .catalog import CORES, EMULATORS, RA_CONFIG, SYSTEMS, cores_for_system

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
FRONT_CONFIG = os.path.join(CONFIG_DIR, "front.json")
CORES_DIR = os.path.join(PROJECT_DIR, "cores")

DEFAULTS = {
    "language": "pt",
    "gamemode": True,
    "icon_size": 210,
    "sidebar_collapsed": False,  # sidebar só em ícones (dica ao passar o mouse)
    "ra_cores_dir": "~/.config/retroarch/cores",   # pasta SÓ com os cores
    "core_auto_update": False,  # atualizar cores automaticamente
    "core_last_update": 0,      # timestamp da última atualização automática
    "ra_shader": "",            # shader/filtro do RetroArch (caminho .slangp)
    "ra_resolution": "auto",    # resolução fullscreen do RetroArch
    "ra_aspect": "auto",        # proporção de tela do RetroArch
    "rom_dirs": {},      # system_id -> [caminhos, ...]   (múltiplos OK)
    "emulators": {},     # system_id -> nova entrada (ver _migrate_emulators)
    "ss_devid": "",      # ScreenScraper: credencial de dev (grátis no site)
    "ss_devpassword": "",
    "ss_user": "",       # ScreenScraper: conta de usuário (opcional)
    "ss_password": "",
    "pc_games": [],      # [{"name": ..., "path": ...}]
    "favorites": [],
    "last_played": {},   # game_id -> timestamp
}


class Config:
    def __init__(self) -> None:
        self.data: dict = json.loads(json.dumps(DEFAULTS))
        self.load()

    # ---------- persistência ----------
    def load(self) -> None:
        if os.path.isfile(FRONT_CONFIG):
            try:
                with open(FRONT_CONFIG, encoding="utf-8") as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    self.data[k] = v
            except (OSError, json.JSONDecodeError):
                pass  # corrompida: mantém defaults
        # descarta chaves de sistemas que saíram do catálogo
        for key in ("rom_dirs", "emulators"):
            for sid in list(self.data.get(key, {})):
                if sid not in SYSTEMS:
                    del self.data[key][sid]

    def save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = FRONT_CONFIG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, FRONT_CONFIG)

    # ---------- export/import ----------
    def export_to(self, path: str) -> None:
        """Cópia fiel da configuração atual pra ``path`` (JSON)."""
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def import_from(self, path: str) -> str | None:
        """Importa configuração exportada de ``path`` e persiste.

        ``None`` = ok; ``str`` = motivo da recusa (o arquivo não mexe em nada).
        """
        from .strings import tr
        try:
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return str(e)
        if (not isinstance(saved, dict)
                or "emulators" not in saved or "rom_dirs" not in saved):
            return tr(self, "cfg_import_bad")
        # mesma semântica do load(): defaults, com o export por cima
        data = json.loads(json.dumps(DEFAULTS))
        for k, v in saved.items():
            data[k] = v
        for key in ("rom_dirs", "emulators"):
            for sid in list(data.get(key, {})):
                if sid not in SYSTEMS:
                    del data[key][sid]
        self.data = data
        self.save()
        return None

    # ---------- acesso ----------
    def __getitem__(self, key: str):
        return self.data[key]

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = value

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    # ---------- emuladores ----------
    def cores_dir(self) -> str:
        return CORES_DIR

    def ra_cores_dir(self) -> str:
        """Pasta configurada com os cores do RetroArch (*.so)."""
        return os.path.expanduser(self.data.get("ra_cores_dir") or
                                  "~/.config/retroarch/cores")

    def ra_binary(self) -> str | None:
        """Binário do RetroArch: embutido no projeto → sistema."""
        from . import ra_vendor
        app = ra_vendor.ra_appimage()
        if app and os.access(app, os.X_OK):
            return app
        return shutil.which("retroarch")

    def ra_core_file(self, core: str) -> str | None:
        """Caminho completo de um core, se existir na pasta configurada."""
        p = os.path.join(self.ra_cores_dir(), f"{core}_libretro.so")
        return p if os.path.isfile(p) else None

    def installed_cores(self) -> dict[str, str]:
        """Cores instalados: {core_id: caminho} (apenas os do catálogo)."""
        d = self.ra_cores_dir()
        out: dict[str, str] = {}
        if os.path.isdir(d):
            for cid in CORES:
                p = os.path.join(d, f"{cid}_libretro.so")
                if os.path.isfile(p):
                    out[cid] = p
        return out

    def compat_cores(self, sysid: str) -> list[tuple[str, str, bool]]:
        """Cores compatíveis com o sistema: [(id, nome, instalado?), ...]."""
        inst = self.installed_cores()
        return [(cid, name, cid in inst)
                for cid, name in cores_for_system(sysid)]

    def default_core(self, sysid: str) -> str | None:
        """Melhor core pro sistema: o instalado preferido do catálogo."""
        pref = SYSTEMS.get(sysid, {}).get("ra_core", "")
        inst = self.installed_cores()
        if pref and pref in inst:
            return pref
        compat = [cid for cid, _n in cores_for_system(sysid) if cid in inst]
        return compat[0] if compat else (pref or None)

    def list_cores(self) -> list[str]:
        """Executáveis encontrados em cores/ (AppImage ou binário solto)."""
        if not os.path.isdir(CORES_DIR):
            return []
        out = []
        for fn in sorted(os.listdir(CORES_DIR)):
            p = os.path.join(CORES_DIR, fn)
            if os.path.isfile(p) and (os.access(p, os.X_OK) or fn.endswith(".AppImage")):
                out.append(p)
        return out

    def detect_standalone(self, sysid: str) -> dict | None:
        """Acha o emulador standalone de um sistema: cores/ → PATH."""
        sysdef = SYSTEMS.get(sysid)
        if not sysdef or not sysdef.get("emu") or sysdef["emu"] == "RetroArch":
            return None
        emu_name = sysdef["emu"]
        emu_def = EMULATORS.get(emu_name, {})
        pat = emu_def.get("detect", re.escape(emu_name.lower()))
        rx = re.compile(pat, re.I)
        for path in self.list_cores():
            if rx.search(os.path.basename(path)):
                return {"name": emu_name, "app": path,
                        "args": list(emu_def.get("args", ["{game}"]))}
        sysbin = shutil.which(emu_def.get("path", emu_name.lower()))
        if sysbin:
            return {"name": emu_name, "app": sysbin,
                    "args": list(emu_def.get("args", ["{game}"]))}
        return None

    def detect_emulator(self, sysid: str) -> dict | None:
        """Entrada padrão de emulação do sistema (modo retroarch/standalone)."""
        sysdef = SYSTEMS.get(sysid)
        if not sysdef or not sysdef.get("emu"):
            return None
        # sistemas que preferem core do RetroArch
        if sysdef["emu"] == "RetroArch":
            if not self.ra_binary():
                return None
            core = self.default_core(sysid)
            if not core:
                return None
            return {"mode": "retroarch", "core": core, "fullscreen": True}
        # sistemas com standalone: preferir standalone, mas expor core na UI
        det = self.detect_standalone(sysid)
        entry: dict = {"mode": "standalone" if det else
                       ("retroarch" if self.ra_binary() else "standalone")}
        if det:
            entry.update(det)
        else:
            core = self.default_core(sysid)
            entry["core"] = core
            entry["fullscreen"] = True
        return entry

    def emu_mode(self, sysid: str) -> str:
        """Modo efetivo de um sistema: 'retroarch' ou 'standalone'."""
        return (self.data["emulators"].get(sysid) or {}).get("mode", "standalone")

    def emu_name_for(self, sysid: str) -> str:
        """Nome do emulador que roda o sistema (p/ badge e ícone)."""
        emu = self.data["emulators"].get(sysid) or {}
        if emu.get("mode") == "retroarch":
            return "RetroArch"
        return emu.get("name") or SYSTEMS.get(sysid, {}).get("emu", "?")

    def _migrate_emulators(self) -> bool:
        """Schema antigo {name, app, args} → novo {mode, core, fullscreen,...}."""
        changed = False
        for sysid, emu in list(self.data["emulators"].items()):
            if not isinstance(emu, dict) or "mode" in emu:
                continue
            name = emu.get("name", "")
            if name == "RetroArch":
                new = {"mode": "retroarch", "core": self.default_core(sysid),
                       "fullscreen": True}
            else:
                new = {"mode": "standalone", "name": name,
                       "app": emu.get("app", ""), "args": emu.get("args") or []}
            self.data["emulators"][sysid] = new
            changed = True
        return changed

    def ensure_emulators(self) -> bool:
        """Preenche emuladores faltantes via auto-detect. Retorna True se mudou."""
        changed = self._migrate_emulators()
        for sysid, sysdef in SYSTEMS.items():
            if not sysdef.get("emu"):
                continue
            if sysid not in self.data["emulators"] or not self.data["emulators"][sysid]:
                det = self.detect_emulator(sysid)
                if det:
                    self.data["emulators"][sysid] = det
                    changed = True
        return changed

    def ensure_rom_dirs(self) -> bool:
        """Cria as pastas de ROM padrão (estrutura do RetroArch) se existirem."""
        ra_root = os.path.expanduser(os.path.join(RA_CONFIG, "roms"))
        changed = False
        for sysid, sysdef in SYSTEMS.items():
            folder = sysdef.get("ra_folder", "")
            if not folder or sysid in self.data["rom_dirs"]:
                continue
            folders = folder if isinstance(folder, list) else [folder]
            found = [os.path.join(ra_root, f) for f in folders
                     if os.path.isdir(os.path.join(ra_root, f))]
            if found:
                self.data["rom_dirs"][sysid] = found
                changed = True
        return changed

    def all_rom_dirs(self) -> dict[str, list[str]]:
        return dict(self.data["rom_dirs"])
