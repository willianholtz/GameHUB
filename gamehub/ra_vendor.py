"""RetroArch portátil embutido no projeto (vendor/retroarch).

O build Linux oficial do Libretro é um AppImage que, ao rodar, aponta o
próprio $HOME pra uma pasta ``.home`` vizinha — logo, config, saves,
states e cache do RetroArch ficam **dentro do projeto**, sem tocar em
``~/.config`` do sistema.

Instalação: baixa o .7z oficial, extrai (py7zr num venv privado em
``vendor/venv``, criado sob demanda — não polui o Python do sistema),
gera a config mínima e verifica o binário.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import urllib.request

from .config import PROJECT_DIR

VENDOR_DIR = os.path.join(PROJECT_DIR, "vendor")
RA_DIR = os.path.join(VENDOR_DIR, "retroarch")
VENV_DIR = os.path.join(VENDOR_DIR, "venv")
VENV_PY = os.path.join(VENV_DIR, "bin", "python")

RA_URL = "https://buildbot.libretro.com/nightly/linux/x86_64/RetroArch.7z"

# Config mínima: o básico pra rodar conteúdo via -L. Salva onde o AppImage
# usa como $HOME (vendor/retroarch/…AppImage.home/.config/retroarch/).
MINIMAL_CFG = """\
# GameHub — config mínima do RetroArch portátil (gerada automaticamente).
# O AppImage usa a pasta .home vizinha como $HOME: tudo fica no projeto.
config_save_on_exit = "false"
video_driver = "vulkan"
video_vsync = "true"
audio_driver = "pulse"
input_autodetect_enable = "true"
"""

# Perfil "kiosk": só o jogo. Bloqueia Quick Menu (core options, save states,
# shaders…), deixa F11 (fullscreen), P (pausa) e ESC 2x (sair). Aplicado ao
# RetroArch embutido pra nunca aparecer menu de núcleo.
KIOSK_OPTIONS: dict[str, str] = {
    "kiosk_mode_enable": "true",             # bloqueia o menu/Quick Menu
    "kiosk_mode_password": "",               # sem senha → menu totalmente morto
    "input_menu_toggle": "",                 # desliga a tecla de menu (F1/ESC)
    "input_menu_toggle_gamepad_combo": "0",  # desliga combo de gamepad p/ menu
    "input_toggle_fullscreen": "f11",        # F11 → fullscreen/janela
    "input_pause_toggle": "p",               # P → pausa
    "input_quit_key": "escape",              # ESC → sair
    "quit_press_twice": "true",              # ...precisa apertar 2x
}


def apply_kiosk_mode() -> bool:
    """Aplica o perfil kiosk ao RetroArch embutido. True se tinha embutido."""
    if not ra_cfg():
        return False
    set_cfg_options(KIOSK_OPTIONS)
    return True


def apply_cheats_support() -> bool:
    """Liga o auto-load de cheats no RetroArch embutido.

    Com isso, ao abrir um conteúdo o RetroArch lê sozinho
    ``<cheat_database_path>/<nome do core>/<rom>.cht`` e aplica os itens com
    ``enable = true`` — sem passar pelo menu (princípio do hub).
    """
    home, cfg = ra_home(), ra_cfg()
    if not home or not cfg:
        return False
    set_cfg_options({
        "cheat_database_path":
            os.path.join(home, ".config", "retroarch", "cheats"),
        "apply_cheats_after_load": "true",
    })
    return True


def ra_appimage() -> str | None:
    """Caminho do AppImage embutido (procura no layout extraído)."""
    hits = glob.glob(os.path.join(RA_DIR, "**", "*.AppImage"), recursive=True)
    return hits[0] if hits else None


def ra_home() -> str | None:
    """Pasta que o AppImage usa como $HOME (…AppImage.home)."""
    app = ra_appimage()
    return app + ".home" if app else None


def ra_cfg() -> str | None:
    home = ra_home()
    return os.path.join(home, ".config", "retroarch", "retroarch.cfg") if home else None


def is_installed() -> bool:
    app = ra_appimage()
    return bool(app) and os.access(app, os.X_OK)


def version() -> str | None:
    app = ra_appimage()
    if not app:
        return None
    try:
        out = subprocess.run([app, "--version"], capture_output=True,
                             text=True, timeout=30)
        for line in (out.stdout + out.stderr).splitlines():
            if "Version:" in line:
                return "RetroArch " + line.split("Version:", 1)[1].strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "?"


def _ensure_layout(progress) -> bool:
    """Permissões + config mínima no lugar certo. True se binário existe."""
    app = ra_appimage()
    if not app:
        return False
    os.chmod(app, os.stat(app).st_mode | 0o755)
    cfg = ra_cfg()
    if cfg and not os.path.isfile(cfg):
        os.makedirs(os.path.dirname(cfg), exist_ok=True)
        with open(cfg, "w", encoding="utf-8") as f:
            f.write(MINIMAL_CFG)
        progress("config mínima gerada ✔")
    # garante o perfil kiosk (bloqueia menu de núcleo) em qualquer instalação
    apply_kiosk_mode()
    return True


def _ensure_venv(progress) -> bool:
    """Cria vendor/venv com py7zr (sob demanda)."""
    if os.path.isfile(VENV_PY):
        return True
    progress("criando ambiente virtual do projeto…")
    try:
        subprocess.run([sys.executable, "-m", "venv", "--system-site-packages",
                        VENV_DIR], check=True, capture_output=True, timeout=120)
        progress("instalando py7zr (só dentro do projeto)…")
        subprocess.run([VENV_PY, "-m", "pip", "install", "--quiet", "py7zr"],
                       check=True, capture_output=True, timeout=300)
        return os.path.isfile(VENV_PY)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        progress(f"falha no venv: {e}")
        return False


def _download(progress) -> str | None:
    """Baixa o .7z oficial. Retorna o caminho ou None."""
    dest = os.path.join(VENDOR_DIR, "RetroArch.7z")
    if os.path.isfile(dest) and os.path.getsize(dest) > 10_000_000:
        progress("download já existente, reusando…")
        return dest
    progress("baixando RetroArch oficial (~40 MB)…")
    try:
        req = urllib.request.Request(RA_URL, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            with open(dest, "wb") as f:
                while chunk := resp.read(1 << 16):
                    f.write(chunk)
                    done += len(chunk)
                    if total and (done % (4 << 20) < (1 << 16)):
                        progress(f"baixando… {done * 100 // total}%")
        return dest
    except OSError as e:
        progress(f"falha no download: {e}")
        return None


def install(progress=print) -> bool:
    """Instala o RetroArch portátil no projeto. True se ficou pronto."""
    if is_installed() and _ensure_layout(progress):
        ver = version()
        progress(f"RetroArch já embutido ({ver or '?'}) ✔")
        return True
    os.makedirs(VENDOR_DIR, exist_ok=True)
    if not _ensure_venv(progress):
        return False
    archive = _download(progress)
    if not archive:
        return False
    progress("extraindo…")
    try:
        subprocess.run([VENV_PY, "-m", "py7zr", "x", archive, RA_DIR],
                       check=True, capture_output=True, timeout=600)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        progress(f"falha na extração: {e}")
        return False
    try:
        os.remove(archive)
    except OSError:
        pass
    if not _ensure_layout(progress):
        progress("AppImage retroarch não encontrado no pacote")
        return False
    ver = version()
    progress(f"pronto! {ver or 'RetroArch'} embutido no projeto ✔")
    return True


def uninstall() -> None:
    """Remove o RetroArch embutido (não toca em nada do sistema)."""
    shutil.rmtree(RA_DIR, ignore_errors=True)


# ---------- cores (buildbot oficial) ----------

CORES_ZIP_URL = ("https://buildbot.libretro.com/nightly/linux/x86_64/latest/"
                 "{core}_libretro.so.zip")


def update_core(core: str, dest_dir: str, progress=print) -> bool:
    """Baixa/atualiza UM core pra ``dest_dir`` (pasta de *.so). True se ok."""
    import zipfile
    url = CORES_ZIP_URL.format(core=core)
    tmp = os.path.join(dest_dir, f".{core}.zip")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameHub"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(tmp, "wb") as f:
                while chunk := resp.read(1 << 16):
                    f.write(chunk)
        with zipfile.ZipFile(tmp) as z:
            names = [n for n in z.namelist() if n.endswith(".so")]
            if not names:
                progress(f"{core}: .so não encontrado no pacote")
                return False
            data = z.read(names[0])
        os.makedirs(dest_dir, exist_ok=True)
        with open(os.path.join(dest_dir, f"{core}_libretro.so"), "wb") as f:
            f.write(data)
        return True
    except (OSError, zipfile.BadZipFile) as e:
        progress(f"{core}: falha ({e})")
        return False
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def update_cores(cores: list[str], dest_dir: str, progress=print) -> int:
    """Atualiza VÁRIOS cores. Retorna quantos deram certo."""
    ok = 0
    for core in cores:
        progress(f"atualizando {core}…")
        if update_core(core, dest_dir, progress):
            ok += 1
            progress(f"{core} ✔")
    return ok


# ---------- opções gerais (filtros/resolução/proporção) ----------

def set_cfg_options(options: dict[str, str]) -> None:
    """Grava chaves no retroarch.cfg do RetroArch embutido (só o básico)."""
    cfg = ra_cfg()
    if not cfg:
        return
    os.makedirs(os.path.dirname(cfg), exist_ok=True)
    cur: dict[str, str] = {}
    lines: list[str] = []
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for ln in lines:
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                cur[k.strip()] = v.strip().strip('"')  # remove aspas antigas
    cur.update({k: str(v) for k, v in options.items()})
    with open(cfg, "w", encoding="utf-8") as f:
        f.write("# GameHub — config do RetroArch portátil (gerada automaticamente)\n")
        for k, v in cur.items():
            f.write(f'{k} = "{v}"\n')


# Filtros visuais prontos (caminhos relativos ao retroarch embutido).
# Confirmados no pacote nightly.
SHADERS = {
    "": "Nenhum",
    "shaders/shaders_slang/crt/crt-easymode.slangp": "CRT",
    "shaders/shaders_slang/handheld/ags001.slangp": "LCD portátil",
    "shaders/shaders_slang/bilinear.slangp": "Suave (bilinear)",
    "shaders/shaders_slang/nearest.slangp": "Nítido (nearest)",
}

# Resoluções fullscreen oferecidas → valores de video_fullscreen_x/y
RESOLUTIONS = {
    "auto": ("", ""),
    "720p": ("1280", "720"),
    "1080p": ("1920", "1080"),
    "1440p": ("2560", "1440"),
    "4k": ("3840", "2160"),
}

# Proporção de tela → valores de video_aspect_ratio (float) + índice custom.
# "" = padrão do core/jogo (índice 0).
ASPECTS = {
    "auto": ("", "0"),
    "4:3": ("1.333333", "19"),
    "16:9": ("1.777778", "19"),
    "1:1": ("1.0", "19"),
    "pixel_perfect": ("", "0"),
}


def apply_ra_general(shader: str, resolution: str, aspect: str) -> None:
    """Aplica as opções gerais do RetroArch embutido (aba Geral)."""
    home = ra_home()
    base = os.path.join(home, ".config", "retroarch") if home else ""
    opts: dict[str, str] = {}
    sh_abs = os.path.join(base, shader) if (shader and base) else ""
    if shader and sh_abs and os.path.isfile(sh_abs):
        opts["video_shader"] = sh_abs
    else:
        opts["video_shader"] = "false"
    x, y = RESOLUTIONS.get(resolution, ("", ""))
    opts["video_fullscreen_x"] = x or "0"
    opts["video_fullscreen_y"] = y or "0"
    ratio, idx = ASPECTS.get(aspect, ("", "0"))
    opts["video_aspect_ratio"] = ratio          # vazio = padrão do core
    opts["video_aspect_ratio_index"] = idx      # 19 = custom, 0 = auto
    set_cfg_options(opts)


def find_shaders() -> dict[str, str]:
    """Shaders realmente presentes no pacote embutido: {rel: nome}."""
    home = ra_home()
    if not home:
        return {}
    base = os.path.join(home, ".config", "retroarch")
    out = {}
    for rel, name in SHADERS.items():
        if not rel or os.path.isfile(os.path.join(base, rel)):
            out[rel] = name
    return out
