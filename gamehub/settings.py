"""Diálogo de Configurações (Geral / Emuladores / Pastas de ROM / Jogos PC).

Aba Geral: idioma, gamemode, ícones + opções do RetroArch (filtro, resolução,
proporção, controles, atualização de cores).

Aba Emuladores: por sistema, escolha entre **emulador standalone** (preferencial)
ou **core do RetroArch** (checkbox). Ao marcar o core, aparece a lista de cores
compatíveis (só nomes); ao desmarcar, as opções de core ficam desabilitadas.
"""
from __future__ import annotations

import os
import shutil
import stat

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSlider, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from .catalog import CORES, EMULATORS, SYSTEMS, sys_short
from .strings import tr


def _ensure_exec(path: str) -> bool:
    """ chmod +x em AppImage escolhido. True se mudou."""
    if path.lower().endswith(".appimage") and not os.access(path, os.X_OK):
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    return False


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(tr(cfg, "cfg_title") + " — " + tr(cfg, "app_title"))
        self.resize(900, 640)

        tabs = QTabWidget()
        tabs.addTab(self._tab_general(), tr(cfg, "cfg_general"))
        tabs.addTab(self._tab_emulators(), tr(cfg, "cfg_emulators"))
        tabs.addTab(self._tab_romdirs(), tr(cfg, "cfg_romdirs"))
        tabs.addTab(self._tab_pc(), tr(cfg, "cfg_pc"))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addWidget(buttons)

    # ---------- Geral ----------
    def _tab_general(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        form = QHBoxLayout()
        form.addWidget(QLabel(tr(self.cfg, "cfg_language")))
        self.lang = QComboBox()
        self.lang.addItem("Português", "pt")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(0 if self.cfg["language"] != "en" else 1)
        form.addWidget(self.lang)
        form.addStretch()
        lay.addLayout(form)

        self.gamemode = QCheckBox(tr(self.cfg, "cfg_gamemode"))
        self.gamemode.setChecked(bool(self.cfg["gamemode"]))
        lay.addWidget(self.gamemode)

        row = QHBoxLayout()
        row.addWidget(QLabel(tr(self.cfg, "cfg_icon_size")))
        self.icon_size = QSlider(Qt.Horizontal)
        self.icon_size.setRange(96, 320)
        self.icon_size.setValue(int(self.cfg["icon_size"]))
        self.icon_size.setTickPosition(QSlider.TicksBelow)
        self.icon_size.setTickInterval(48)
        row.addWidget(self.icon_size)
        lay.addLayout(row)

        lay.addWidget(self._group_ra_general())
        lay.addStretch()
        return w

    def _group_ra_general(self) -> QGroupBox:
        """Regra 7: opções do RetroArch (filtro, resolução, tela, controles)."""
        box = QGroupBox("RetroArch")
        lay = QVBoxLayout(box)
        from . import ra_vendor

        # filtro/shader
        r1 = QHBoxLayout()
        r1.addWidget(QLabel(tr(self.cfg, "cfg_shader")))
        self.shader = QComboBox()
        shaders = ra_vendor.find_shaders()
        self._shader_map = {}
        for rel, name in shaders.items():
            self._shader_map[name] = rel
            self.shader.addItem(name, rel)
        cur = self.cfg.get("ra_shader", "")
        idx = 0
        for i in range(self.shader.count()):
            if self.shader.itemData(i) == cur:
                idx = i
                break
        self.shader.setCurrentIndex(idx)
        r1.addWidget(self.shader, 1)
        lay.addLayout(r1)

        # resolução
        r2 = QHBoxLayout()
        r2.addWidget(QLabel(tr(self.cfg, "cfg_resolution")))
        self.resolution = QComboBox()
        for key, label in [("auto", "Auto (monitor)"), ("720p", "720p"),
                           ("1080p", "1080p"), ("1440p", "1440p (recomendado)"),
                           ("4k", "4K")]:
            self.resolution.addItem(label, key)
        self._set_combo_data(self.resolution, self.cfg.get("ra_resolution", "auto"))
        r2.addWidget(self.resolution, 1)
        lay.addLayout(r2)

        # proporção de tela
        r3 = QHBoxLayout()
        r3.addWidget(QLabel(tr(self.cfg, "cfg_aspect")))
        self.aspect = QComboBox()
        for key, label in [("auto", "Auto (jogo/core)"), ("4:3", "4:3"),
                           ("16:9", "16:9"), ("1:1", "1:1 (pixel perfeito)")]:
            self.aspect.addItem(label, key)
        self._set_combo_data(self.aspect, self.cfg.get("ra_aspect", "auto"))
        r3.addWidget(self.aspect, 1)
        lay.addLayout(r3)

        # controles detectados (regra 8)
        r4 = QHBoxLayout()
        self.controls_lbl = QLabel()
        btn_ctrl = QPushButton(tr(self.cfg, "cfg_detect_controls"))
        btn_ctrl.clicked.connect(self._refresh_controls)
        r4.addWidget(self.controls_lbl, 1)
        r4.addWidget(btn_ctrl)
        lay.addLayout(r4)
        self._refresh_controls()

        # atualização de cores (regra 9)
        self.core_auto = QCheckBox(tr(self.cfg, "cfg_core_auto"))
        self.core_auto.setChecked(bool(self.cfg.get("core_auto_update")))
        lay.addWidget(self.core_auto)
        lay.addWidget(self._group_covers())
        return box

    def _group_covers(self) -> QGroupBox:
        """Capas: Libretro (livre) + ScreenScraper (fallback, com credencial)."""
        box = QGroupBox(tr(self.cfg, "cfg_covers"))
        lay = QVBoxLayout(box)
        from . import screenscraper

        tip = QLabel(tr(self.cfg, "cfg_ss_hint"))
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #5b6b85;")
        lay.addWidget(tip)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("devid"))
        self.ss_devid = QLineEdit(self.cfg.get("ss_devid", ""))
        self.ss_devid.setPlaceholderText("credencial de dev (screenscraper.fr)")
        r1.addWidget(self.ss_devid, 1)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("devpassword"))
        self.ss_devpass = QLineEdit(self.cfg.get("ss_devpassword", ""))
        self.ss_devpass.setEchoMode(QLineEdit.Password)
        r2.addWidget(self.ss_devpass, 1)
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel(tr(self.cfg, "cfg_ss_user")))
        self.ss_user = QLineEdit(self.cfg.get("ss_user", ""))
        r3.addWidget(self.ss_user, 1)
        r3.addWidget(QLabel(tr(self.cfg, "cfg_ss_pass")))
        self.ss_pass = QLineEdit(self.cfg.get("ss_password", ""))
        self.ss_pass.setEchoMode(QLineEdit.Password)
        r3.addWidget(self.ss_pass, 1)
        lay.addLayout(r3)

        self.ss_status = QLabel()
        if screenscraper.configured(self.cfg):
            self.ss_status.setText(tr(self.cfg, "cfg_ss_on"))
            self.ss_status.setStyleSheet("color: #3fb950;")
        else:
            self.ss_status.setText(tr(self.cfg, "cfg_ss_off"))
            self.ss_status.setStyleSheet("color: #5b6b85;")
        lay.addWidget(self.ss_status)
        return box

    def _refresh_controls(self) -> None:
        from .controls import detect_gamepads
        pads = detect_gamepads()
        if pads:
            self.controls_lbl.setText("🎮 " + ", ".join(pads))
            self.controls_lbl.setStyleSheet("color: #3fb950;")
        else:
            self.controls_lbl.setText(tr(self.cfg, "cfg_no_controls"))
            self.controls_lbl.setStyleSheet("color: #5b6b85;")

    # ---------- Emuladores ----------
    def _tab_emulators(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        split = QSplitter()
        self.emu_list = QListWidget()
        self.emu_list.setIconSize(QSize(22, 22))
        self.emu_list.setFixedWidth(210)
        self.emu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for sysid, sysdef in SYSTEMS.items():
            if not sysdef.get("emu"):
                continue
            cur = self.cfg["emulators"].get(sysid) or {}
            label = f"{sysdef['name']}  →  {self._sys_label(sysid, cur)}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, sysid)
            item.setIcon(self._emu_list_icon(sysid))
            self.emu_list.addItem(item)
        split.addWidget(self.emu_list)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(4, 0, 0, 0)
        rlay.setSpacing(8)

        # ---- RetroArch: pasta dos cores + embutido (em um grupo) ----
        from . import ra_vendor
        ra_group = QGroupBox("RetroArch")
        rg = QVBoxLayout(ra_group)
        rg.setSpacing(6)
        ra_row = QHBoxLayout()
        self.ra_cores = QLineEdit(self.cfg.ra_cores_dir())
        self.ra_cores.setPlaceholderText("~/.config/retroarch/cores")
        btn_ra = QPushButton(tr(self.cfg, "cfg_browse"))
        btn_ra.clicked.connect(self._browse_ra_cores)
        ra_row.addWidget(self.ra_cores, 1)
        ra_row.addWidget(btn_ra)
        rg.addLayout(ra_row)
        ra_box = QHBoxLayout()
        self.ra_status = QLabel()
        self._refresh_ra_status()
        btn_ra_dl = QPushButton(tr(self.cfg, "cfg_ra_embed"))
        btn_ra_dl.clicked.connect(lambda: self._download_ra(ra_vendor, btn_ra_dl))
        self.ra_progress = QLabel("")
        self.ra_progress.setStyleSheet("color: #5b6b85;")
        ra_box.addWidget(self.ra_status, 1)
        ra_box.addWidget(self.ra_progress)
        ra_box.addWidget(btn_ra_dl)
        rg.addLayout(ra_box)
        rlay.addWidget(ra_group)

        # ---- modo: standalone (preferido) ↔ core (checkbox) ----
        self.use_core = QCheckBox(tr(self.cfg, "cfg_use_core"))
        self.use_core.toggled.connect(self._toggle_mode)
        rlay.addWidget(self.use_core)

        # faixa de observação: quando existe standalone E core, o standalone
        # é sempre melhor — mas a escolha é do usuário.
        self.sa_note = QLabel(tr(self.cfg, "cfg_sa_note"))
        self.sa_note.setWordWrap(True)
        self.sa_note.setStyleSheet(
            "background: #1b2a44; color: #9fc1ff; border: 1px solid #2c4570;"
            " border-radius: 6px; padding: 6px 8px; font-size: 12px;")
        rlay.addWidget(self.sa_note)

        # núcleo: lista de cores compatíveis
        self.core_box = QGroupBox(tr(self.cfg, "cfg_core_pick"))
        cb = QVBoxLayout(self.core_box)
        cb.setSpacing(6)
        crow = QHBoxLayout()
        self.core_combo = QComboBox()
        self.core_combo.currentIndexChanged.connect(self._on_core_changed)
        crow.addWidget(self.core_combo, 1)
        self.btn_core_update = QPushButton(tr(self.cfg, "cfg_update_core"))
        self.btn_core_update.clicked.connect(self._update_current_core)
        crow.addWidget(self.btn_core_update)
        cb.addLayout(crow)
        self.core_hint = QLabel()
        self.core_hint.setStyleSheet("color: #5b6b85;")
        self.core_hint.setWordWrap(True)
        cb.addWidget(self.core_hint)
        rlay.addWidget(self.core_box)

        # fullscreen (regra 6) — vale pros dois modos
        self.fullscreen = QCheckBox(tr(self.cfg, "cfg_fullscreen"))
        rlay.addWidget(self.fullscreen)

        # ---- standalone: binário + argumentos ----
        self.sa_box = QGroupBox(tr(self.cfg, "cfg_standalone"))
        sb = QVBoxLayout(self.sa_box)
        sb.setSpacing(6)
        path_row = QHBoxLayout()
        self.emu_path = QLineEdit()
        self.emu_path.setReadOnly(True)
        btn_browse = QPushButton(tr(self.cfg, "cfg_browse"))
        btn_browse.clicked.connect(self._browse_emu)
        btn_detect = QPushButton(tr(self.cfg, "cfg_detect"))
        btn_detect.clicked.connect(self._detect_emu)
        path_row.addWidget(QLabel(tr(self.cfg, "cfg_binary")))
        path_row.addWidget(self.emu_path, 1)
        path_row.addWidget(btn_browse)
        path_row.addWidget(btn_detect)
        sb.addLayout(path_row)
        args_row = QHBoxLayout()
        self.emu_args = QLineEdit()
        self.emu_args.setPlaceholderText("-fastboot {game}")
        args_row.addWidget(QLabel(tr(self.cfg, "cfg_args")))
        args_row.addWidget(self.emu_args, 1)
        sb.addLayout(args_row)
        # ---- AppImage oficial: baixa pra cores/ do projeto, nada no sistema ----
        dl_row = QHBoxLayout()
        self.btn_appi = QPushButton(tr(self.cfg, "cfg_dl_appimage"))
        self.btn_appi.clicked.connect(self._download_appimage)
        self.appi_status = QLabel()
        self.appi_status.setStyleSheet("color: #5b6b85;")
        self.appi_status.setWordWrap(True)
        dl_row.addWidget(self.btn_appi)
        dl_row.addWidget(self.appi_status, 1)
        sb.addLayout(dl_row)
        rlay.addWidget(self.sa_box)

        rlay.addStretch()
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        lay.addWidget(split, 1)

        self.emu_list.currentItemChanged.connect(self._load_emu)
        if self.emu_list.count():
            self.emu_list.setCurrentRow(0)
        return w

    def _emu_list_icon(self, sysid: str):
        """Ícone do console (Assets reais) pra lista de configurações."""
        from .icons import system_icon
        return system_icon(sysid, 22, self.emu_list)

    # ---------- helpers emuladores ----------
    def _sys_label(self, sysid: str, cur: dict) -> str:
        if not cur:
            return "—"
        if cur.get("mode") == "retroarch":
            cname = CORES.get(cur.get("core", ""), {}).get("name", "?")
            return f"{cname} (core)"
        return cur.get("name") or "—"

    def _current_sysid(self) -> str | None:
        item = self.emu_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _load_emu(self, *_a) -> None:
        sysid = self._current_sysid()
        if not sysid:
            return
        cur = self.cfg["emulators"].get(sysid) or {}
        mode = cur.get("mode", "standalone")

        # núcleos compatíveis com o sistema
        compat = self.cfg.compat_cores(sysid)
        self.core_combo.clear()
        for cid, name, installed in compat:
            mark = "" if installed else "  (baixar)"
            self.core_combo.addItem(f"{name}{mark}", cid)
        has_compat = bool(compat)
        # core só é opção quando EXISTE core compatível — sem core, o checkbox
        # fica desabilitado e o sistema permanece em modo standalone.
        self.use_core.setEnabled(has_compat)
        self.use_core.setToolTip(
            "" if has_compat else tr(self.cfg, "cfg_no_compat_core"))
        if not has_compat:
            self.core_hint.setText(tr(self.cfg, "cfg_no_compat_core"))
        self.btn_core_update.setEnabled(has_compat)

        # aplica modo salvo (sem core compatível, força standalone)
        if mode == "retroarch" and not has_compat:
            mode = "standalone"
        self.core_combo.blockSignals(True)
        if mode == "retroarch":
            self.use_core.setChecked(True)
            self._select_core(cur.get("core", ""))
        else:
            self.use_core.setChecked(False)
        self.core_combo.blockSignals(False)
        self._toggle_mode(self.use_core.isChecked())

        # standalone
        self.emu_path.setText(cur.get("app", ""))
        self.emu_args.setText(" ".join(
            cur.get("args") or
            EMULATORS.get(SYSTEMS[sysid]["emu"], {}).get("args", ["{game}"])))

        # fullscreen
        if mode == "retroarch":
            self.fullscreen.setChecked(bool(cur.get("fullscreen", True)))
        else:
            self.fullscreen.setChecked(bool(cur.get("fullscreen_sa")))
        self._update_fs_enabled()

        # status do botão de AppImage
        from . import appstore
        emu_name = SYSTEMS[sysid]["emu"]
        self.btn_appi.setEnabled(appstore.has_appimage(emu_name))
        if appstore.has_appimage(emu_name):
            self.appi_status.setText(tr(self.cfg, "cfg_appi_hint"))
        else:
            self.appi_status.setText(tr(
                self.cfg, "cfg_appi_none", name=emu_name,
                info=appstore.no_appimage_note(emu_name)))

        # faixa de observação: só quando o sistema tem as DUAS opções
        standalone_ok = SYSTEMS[sysid].get("emu") not in ("", "RetroArch")
        self.sa_note.setVisible(standalone_ok and has_compat)

    def _select_core(self, core_id: str) -> None:
        for i in range(self.core_combo.count()):
            if self.core_combo.itemData(i) == core_id:
                self.core_combo.setCurrentIndex(i)
                return

    def _toggle_mode(self, checked: bool) -> None:
        """Regra 4: core ligado → mostra core, desabilita standalone."""
        self.core_box.setVisible(checked)
        self.sa_box.setVisible(not checked)
        self._update_fs_enabled()

    def _on_core_changed(self) -> None:
        self._refresh_core_hint()

    def _refresh_core_hint(self) -> None:
        sysid = self._current_sysid()
        core_id = self.core_combo.currentData()
        if not sysid or not core_id:
            return
        installed = core_id in self.cfg.installed_cores()
        name = CORES.get(core_id, {}).get("name", core_id)
        if installed:
            self.core_hint.setText(f"✔ {name} instalado.")
        else:
            self.core_hint.setText(
                f"⬇ {name} ainda não instalado — clique em "
                f"“{tr(self.cfg, 'cfg_update_core')}”.")

    def _update_fs_enabled(self) -> None:
        """Fullscreen só faz sentido com core (regra 6) ou standalone que suporta."""
        if self.use_core.isChecked():
            self.fullscreen.setEnabled(True)
            self.fullscreen.setToolTip(tr(self.cfg, "cfg_fullscreen_tip"))
        else:
            sysid = self._current_sysid()
            name = SYSTEMS.get(sysid or "", {}).get("emu", "")
            supported = bool(EMULATORS.get(name, {}).get("fullscreen"))
            self.fullscreen.setEnabled(supported)
            self.fullscreen.setToolTip(
                "" if supported else tr(self.cfg, "cfg_fs_unsupported"))

    def _save_current_emu(self) -> None:
        sysid = self._current_sysid()
        if not sysid:
            return
        if self.use_core.isChecked():
            core = self.core_combo.currentData()
            if not core:
                self.cfg["emulators"].pop(sysid, None)
                return
            self.cfg["emulators"][sysid] = {
                "mode": "retroarch", "core": core,
                "fullscreen": self.fullscreen.isChecked(),
            }
        else:
            app = self.emu_path.text().strip()
            if not app:
                self.cfg["emulators"].pop(sysid, None)
                return
            name = SYSTEMS[sysid]["emu"]
            args = self.emu_args.text().split() or ["{game}"]
            self.cfg["emulators"][sysid] = {
                "mode": "standalone", "name": name, "app": app, "args": args,
                "fullscreen_sa": self.fullscreen.isChecked(),
            }
        # atualiza label + ícone na lista
        item = self.emu_list.currentItem()
        if item:
            sysdef = SYSTEMS[sysid]
            item.setText(f"{sysdef['name']}  →  "
                         f"{self._sys_label(sysid, self.cfg['emulators'][sysid])}")
            item.setIcon(self._emu_list_icon(sysid))

    def _browse_ra_cores(self) -> None:
        d = QFileDialog.getExistingDirectory(self, tr(self.cfg, "cfg_ra_cores"),
                                             self.ra_cores.text() or os.path.expanduser("~"))
        if d:
            self.ra_cores.setText(d)

    # ---------- atualização de cores ----------
    def _update_current_core(self) -> None:
        core_id = self.core_combo.currentData()
        if not core_id:
            return
        dest = self.cfg.ra_cores_dir()
        self._run_core_update([core_id], dest)

    def _run_core_update(self, cores: list[str], dest: str) -> None:
        from . import ra_vendor
        self.btn_core_update.setEnabled(False)
        self.core_hint.setText(tr(self.cfg, "cfg_updating"))

        class Worker(QThread):
            progress = Signal(str)
            done = Signal(int)

            def run(self):
                n = ra_vendor.update_cores(cores, dest, self.progress.emit)
                self.done.emit(n)

        self._core_worker = Worker()
        self._core_worker.progress.connect(
            lambda m: self.core_hint.setText(m))
        self._core_worker.done.connect(self._core_update_done)
        self._core_worker.start()

    def _core_update_done(self, n: int) -> None:
        self.btn_core_update.setEnabled(True)
        self._load_emu()  # refresh (marca ✔ instalado)
        self._refresh_core_hint()

    # ---------- RetroArch embutido ----------
    def _refresh_ra_status(self) -> None:
        from . import ra_vendor
        if ra_vendor.is_installed():
            ver = ra_vendor.version() or "?"
            self.ra_status.setText(f"🎲 RetroArch embutido: {ver}")
            self.ra_status.setStyleSheet("color: #3fb950;")
        else:
            sys_ra = shutil.which("retroarch")
            tip = sys_ra or "—"
            self.ra_status.setText(f"🎲 RetroArch: só do sistema ({tip})")
            self.ra_status.setStyleSheet("color: #8b97ab;")

    def _download_ra(self, ra_vendor, button) -> None:
        button.setEnabled(False)

        class Worker(QThread):
            progress = Signal(str)
            done = Signal(bool)

            def run(self):
                ok = ra_vendor.install(progress=self.progress.emit)
                self.done.emit(ok)

        self._ra_worker = Worker()
        self._ra_worker.progress.connect(self.ra_progress.setText)
        self._ra_worker.done.connect(lambda ok: self._ra_done(ra_vendor, button, ok))
        self._ra_worker.start()

    def _ra_done(self, ra_vendor, button, ok: bool) -> None:
        button.setEnabled(True)
        if ok:
            self.cfg.save()
            self._load_emu()
        self._refresh_ra_status()

    def _browse_emu(self) -> None:
        sysid = self._current_sysid()
        if not sysid:
            return
        start = self.cfg.cores_dir()
        path, _ = QFileDialog.getOpenFileName(self, tr(self.cfg, "cfg_binary"), start)
        if path:
            _ensure_exec(path)
            self.emu_path.setText(path)
            if not self.emu_args.text().strip():
                self._load_emu()
            self._save_current_emu()

    def _detect_emu(self) -> None:
        sysid = self._current_sysid()
        if not sysid:
            return
        det = self.cfg.detect_standalone(sysid)
        if det:
            self.emu_path.setText(det["app"])
            self.emu_args.setText(" ".join(det["args"]))
            self._save_current_emu()

    # ---------- AppImage oficial ----------
    def _download_appimage(self) -> None:
        """Baixa o AppImage oficial do emulador do sistema pra cores/."""
        sysid = self._current_sysid()
        if not sysid or self.use_core.isChecked():
            return
        from . import appstore
        emu_name = SYSTEMS[sysid]["emu"]
        dest = self.cfg.cores_dir()
        self.btn_appi.setEnabled(False)
        self.appi_status.setText(tr(self.cfg, "cfg_dl_start", name=emu_name))

        class Worker(QThread):
            progress = Signal(str)
            done = Signal(object, str)  # caminho | "none" | erro

            def run(self):
                try:
                    p = appstore.download(emu_name, dest,
                                          progress=self.progress.emit)
                    self.done.emit(p, "" if p else "none")
                except Exception as e:  # rede, JSON, disco…
                    self.done.emit(None, str(e) or type(e).__name__)

        self._appi_worker = Worker()
        self._appi_worker.progress.connect(self.appi_status.setText)
        self._appi_worker.done.connect(
            lambda p, e: self._appi_done(sysid, p, e))
        self._appi_worker.start()

    def _appi_done(self, sysid: str, path, err: str) -> None:
        import shiboken6
        if not shiboken6.isValid(self):
            return  # diálogo fechado no meio do download
        self.btn_appi.setEnabled(True)
        if err == "none":
            self.appi_status.setText(tr(self.cfg, "cfg_dl_noresource"))
            return
        if err:
            self.appi_status.setText(tr(self.cfg, "cfg_dl_fail", err=err))
            return
        # detecta em cores/ e configura o sistema pra usar o AppImage baixado
        det = self.cfg.detect_standalone(sysid)
        if det:
            self.emu_path.setText(det["app"])
            if not self.emu_args.text().strip():
                self.emu_args.setText(" ".join(det["args"]))
            self._save_current_emu()
            self._load_emu()  # refresh (ícone/label na lista)
            # por último: _load_emu reseta o status — regrava a mensagem
            self.appi_status.setText(tr(
                self.cfg, "cfg_dl_done", file=os.path.basename(path or "")))
        else:
            self.appi_status.setText(tr(
                self.cfg, "cfg_dl_fail", err=os.path.basename(path or "?")))

    # ---------- Pastas de ROM ----------
    def _tab_romdirs(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        top = QHBoxLayout()
        top.addWidget(QLabel(tr(self.cfg, "cfg_system")))
        self.dir_sys = QComboBox()
        for sysid, sysdef in SYSTEMS.items():
            if sysdef["kind"] == "manual":
                continue
            self.dir_sys.addItem(sys_short(sysid), sysid)
        top.addWidget(self.dir_sys, 1)
        lay.addLayout(top)

        self.dir_list = QListWidget()
        lay.addWidget(self.dir_list, 1)

        btns = QHBoxLayout()
        btn_add = QPushButton("+ " + tr(self.cfg, "cfg_add"))
        btn_add.clicked.connect(self._add_dir)
        btn_del = QPushButton("− " + tr(self.cfg, "cfg_remove"))
        btn_del.clicked.connect(self._del_dir)
        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        btns.addStretch()
        lay.addLayout(btns)

        self.dir_sys.currentIndexChanged.connect(self._load_dirs)
        self._load_dirs()
        return w

    def _load_dirs(self) -> None:
        self.dir_list.clear()
        sysid = self.dir_sys.currentData()
        for d in self.cfg["rom_dirs"].get(sysid, []):
            self.dir_list.addItem(d)

    def _save_dirs(self) -> None:
        sysid = self.dir_sys.currentData()
        dirs = [self.dir_list.item(i).text() for i in range(self.dir_list.count())]
        if dirs:
            self.cfg["rom_dirs"][sysid] = dirs
        else:
            self.cfg["rom_dirs"].pop(sysid, None)

    def _add_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, tr(self.cfg, "cfg_add_folder"),
                                             os.path.expanduser("~"))
        if d and self.dir_list.findItems(d, Qt.MatchFixedString) == []:
            self.dir_list.addItem(d)
        self._save_dirs()

    def _del_dir(self) -> None:
        for item in self.dir_list.selectedItems():
            self.dir_list.takeItem(self.dir_list.row(item))
        self._save_dirs()

    # ---------- Jogos PC ----------
    def _tab_pc(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.pc_list = QListWidget()
        for g in self.cfg["pc_games"]:
            self.pc_list.addItem(f"{g.get('name', '')}  —  {g.get('path', '')}")
        lay.addWidget(self.pc_list, 1)

        row = QHBoxLayout()
        self.pc_name = QLineEdit()
        self.pc_name.setPlaceholderText(tr(self.cfg, "cfg_pc_name"))
        btn_add = QPushButton("+ " + tr(self.cfg, "cfg_add_exe"))
        btn_add.clicked.connect(self._add_pc)
        btn_del = QPushButton("− " + tr(self.cfg, "cfg_remove"))
        btn_del.clicked.connect(self._del_pc)
        row.addWidget(self.pc_name, 1)
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        lay.addLayout(row)
        return w

    def _add_pc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr(self.cfg, "cfg_add_exe"),
                                              os.path.expanduser("~"))
        if not path:
            return
        name = self.pc_name.text().strip() or os.path.splitext(os.path.basename(path))[0]
        self.cfg["pc_games"].append({"name": name, "path": path})
        self.pc_list.addItem(f"{name}  —  {path}")
        self.pc_name.clear()

    def _del_pc(self) -> None:
        for item in self.pc_list.selectedItems():
            row = self.pc_list.row(item)
            self.pc_list.takeItem(row)
            if 0 <= row < len(self.cfg["pc_games"]):
                self.cfg["pc_games"].pop(row)

    # ---------- gravar ----------
    def _apply(self) -> None:
        self.cfg["language"] = self.lang.currentData()
        self.cfg["gamemode"] = self.gamemode.isChecked()
        self.cfg["icon_size"] = self.icon_size.value()
        self.cfg["ra_cores_dir"] = self.ra_cores.text().strip() or "~/.config/retroarch/cores"
        # ScreenScraper (fallback de capas)
        self.cfg["ss_devid"] = self.ss_devid.text().strip()
        self.cfg["ss_devpassword"] = self.ss_devpass.text().strip()
        self.cfg["ss_user"] = self.ss_user.text().strip()
        self.cfg["ss_password"] = self.ss_pass.text().strip()
        self.cfg["ra_shader"] = self.shader.currentData() or ""
        self.cfg["ra_resolution"] = self.resolution.currentData()
        self.cfg["ra_aspect"] = self.aspect.currentData()
        self.cfg["core_auto_update"] = self.core_auto.isChecked()
        self._save_current_emu()
        self._save_dirs()

        # aplica opções gerais do RetroArch embutido
        from . import ra_vendor
        if ra_vendor.is_installed():
            ra_vendor.apply_ra_general(self.cfg["ra_shader"],
                                       self.cfg["ra_resolution"],
                                       self.cfg["ra_aspect"])
        self.cfg.save()
        self.accept()

    # ---------- helpers ----------
    @staticmethod
    def _set_combo_data(combo: QComboBox, value) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
