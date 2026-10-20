"""Janela principal do GameHub."""
from __future__ import annotations

import datetime
import os
import time

from PySide6.QtCore import (QAbstractListModel, QEvent, QModelIndex, QSize, Qt,
                            QThread, QTimer, QUrl, Signal)
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QIcon,
                           QLinearGradient, QPainter, QPen, QPixmap, QPolygon)
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QListView,
                               QListWidget, QListWidgetItem, QMenu, QMessageBox,
                               QPushButton, QScrollArea, QStyle, QToolButton,
                               QVBoxLayout, QWidget, QDialog,
                               QDialogButtonBox, QStyledItemDelegate,
                               QStyleOptionViewItem, QAbstractItemView)

from . import appstore, cheats, runners
from .catalog import SYSTEMS, sys_short
from .config import Config, PROJECT_DIR
from .icons import all_icon, emulator_icon, system_icon
from .scanner import Game, scan
from .settings import SettingsDialog
from .strings import tr

ALL = "__all__"


# ============================ modelo ============================
class GameModel(QAbstractListModel):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._all: list[Game] = []
        self._visible: list[Game] = []
        self._system = ALL
        self._query = ""

    def set_games(self, games: list[Game]) -> None:
        self.beginResetModel()
        self._all = games
        self._refilter()
        self.endResetModel()

    def set_system(self, sysid: str) -> None:
        self.beginResetModel()
        self._system = sysid
        self._refilter()
        self.endResetModel()

    def set_query(self, q: str) -> None:
        self.beginResetModel()
        self._query = q.strip().lower()
        self._refilter()
        self.endResetModel()

    def _refilter(self) -> None:
        self._visible = [
            g for g in self._all
            if (self._system == ALL or g.system == self._system)
            and (not self._query or self._query in g.title.lower())
        ]

    def game_at(self, row: int) -> Game | None:
        return self._visible[row] if 0 <= row < len(self._visible) else None

    def rowCount(self, _parent=QModelIndex()) -> int:
        return len(self._visible)

    def data(self, index, role=Qt.DisplayRole):
        g = self.game_at(index.row())
        if not g:
            return None
        if role == Qt.DisplayRole:
            return g.title
        if role == Qt.UserRole:
            return g
        return None

    def is_favorite(self, g: Game) -> bool:
        return g.id in self.cfg["favorites"]


# ============================ delegate ============================
class GameDelegate(QStyledItemDelegate):
    def __init__(self, cfg, model: GameModel):
        super().__init__()
        self.cfg = cfg
        self.model = model
        self._pix: dict[str, QPixmap] = {}

    def sizeHint(self, option, index) -> QSize:
        w = int(self.cfg["icon_size"])
        return QSize(w, w + 58)

    def _cover(self, path: str | None, w: int, h: int) -> QPixmap | None:
        if not path or not os.path.isfile(path):
            return None
        key = f"{path}|{w}x{h}"
        if key not in self._pix:
            img = QPixmap(path)
            if img.isNull():
                return None
            sc = max(w / img.width(), h / img.height())
            img = img.scaled(int(img.width() * sc), int(img.height() * sc),
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._pix[key] = img
        return self._pix[key]

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        g: Game | None = index.data(Qt.UserRole)
        if not g:
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        w = option.rect.width()
        h = option.rect.height()
        x, y = option.rect.x(), option.rect.y()
        hover = bool(option.state & QStyle.State_MouseOver)

        # card
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1d2841" if hover else "#182136"))
        painter.drawRoundedRect(x, y, w, h, 12, 12)

        # arte
        art_h = h - 58
        art = (x + 8, y + 8, w - 16, art_h - 8)
        cover = self._cover(g.icon, art[2], art[3])
        if cover:
            painter.save()
            painter.setClipRect(art[0], art[1], art[2], art[3])
            painter.drawPixmap(art[0] - (cover.width() - art[2]) // 2,
                               art[1] - (cover.height() - art[3]) // 2, cover)
            painter.restore()
        else:  # placeholder com gradiente por sistema
            hue = hash(g.system) % 360
            g1 = QColor.fromHsv(hue, 140, 60)
            g2 = QColor.fromHsv((hue + 40) % 360, 180, 110)
            grad = QLinearGradient(art[0], art[1], art[0] + art[2], art[1] + art[3])
            grad.setColorAt(0, g1)
            grad.setColorAt(1, g2)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(art[0], art[1], art[2], art[3], 8, 8)
            painter.setPen(QColor(255, 255, 255, 80))
            f = QFont(painter.font())
            f.setPixelSize(44)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(art[0], art[1], art[2], art[3], Qt.AlignCenter,
                             g.title[:1].upper())

        # badge do sistema
        sysname = sys_short(g.system)
        bf = QFont(painter.font())
        bf.setPixelSize(9)
        bf.setBold(True)
        painter.setFont(bf)
        bw = painter.fontMetrics().horizontalAdvance(sysname) + 14
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(10, 14, 24, 210))
        painter.drawRoundedRect(art[0] + 8, art[1] + 8, bw, 20, 10, 10)
        painter.setPen(QColor("#9fc1ff"))
        painter.drawText(art[0] + 8, art[1] + 8, bw, 20, Qt.AlignCenter, sysname)

        # favorito
        if self.model.is_favorite(g):
            painter.setPen(QColor("#f5c542"))
            f2 = QFont(painter.font())
            f2.setPixelSize(14)
            painter.setFont(f2)
            painter.drawText(art[0] + art[2] - 22, art[1] + 24, "★")

        # badge do emulador (ícone no canto inferior da arte)
        emu_name = self.cfg.emu_name_for(g.system)
        isz = 22
        from .icons import emulator_icon
        icon = emulator_icon(emu_name, isz, option.widget or None)
        ix = art[0] + art[2] - isz - 8
        iy = art[1] + art[3] - isz - 8
        painter.drawPixmap(ix, iy, icon)

        # título
        tf = QFont(painter.font())
        tf.setPixelSize(11)
        tf.setBold(True)
        painter.setFont(tf)
        painter.setPen(QColor("#e8eef8"))
        painter.drawText(x + 12, y + art_h + 4, w - 24, 18, Qt.AlignLeft | Qt.TextSingleLine,
                         painter.fontMetrics().elidedText(g.title, Qt.ElideMiddle, w - 24))

        # último jogado
        ts = self.cfg["last_played"].get(g.id)
        if ts:
            painter.setPen(QColor("#5b6b85"))
            f3 = QFont(painter.font())
            f3.setPixelSize(9)
            painter.setFont(f3)
            when = datetime.datetime.fromtimestamp(ts)
            label = tr(self.cfg, "last_played", when=when.strftime("%d/%m"))
            painter.drawText(x + 12, y + art_h + 24, w - 24, 14,
                             Qt.AlignLeft | Qt.TextSingleLine, label)

        # hover: borda + play
        if hover:
            painter.setPen(QPen(QColor("#4f8cff"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(x, y, w, h, 12, 12)
            cx, cy = x + w // 2, y + art_h // 2 + 4
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(79, 140, 255, 235))
            painter.drawEllipse(QPoint(cx, cy), 26, 26)
            painter.setBrush(QColor("white"))
            painter.drawPolygon(QPolygon([QPoint(cx - 6, cy - 10),
                                          QPoint(cx + 12, cy), QPoint(cx - 6, cy + 10)]))
        painter.restore()


# ============================ janela ============================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = Config()
        changed = self.cfg.ensure_rom_dirs() | self.cfg.ensure_emulators()
        if changed:
            self.cfg.save()
        try:
            from . import ra_vendor
            ra_vendor.apply_cheats_support()  # auto-load de cheats ligado
        except OSError:
            pass

        self.proc = None
        self.running_game: Game | None = None
        self.model = GameModel(self.cfg)
        self.delegate = GameDelegate(self.cfg, self.model)

        self._build_ui()
        icon = os.path.join(PROJECT_DIR, "icon.png")
        if os.path.isfile(icon):
            self.setWindowIcon(QIcon(icon))
        self.setWindowTitle(tr(self.cfg, "app_title"))
        self.resize(1280, 800)

        self._start_gamepad()
        QTimer.singleShot(0, self.rescan)
        QTimer.singleShot(1500, self._maybe_auto_update_cores)

    # ---------- navegação por controle ----------
    def _start_gamepad(self) -> None:
        """Liga a navegação por gamepad (se houver controle conectado)."""
        from .gamepad import GamepadThread, controller_name
        self._pad = GamepadThread(self)
        self._pad.move.connect(self._pad_move)
        self._pad.activate.connect(self.play)
        self._pad.back.connect(self._pad_back)
        self._pad.menu.connect(lambda: SettingsDialog(self.cfg, self).exec())
        self._pad.start()
        name = controller_name()
        if name:
            self.status.setText(tr(self.cfg, "gamepad_on", name=name))

    def _pad_move(self, dx: int, dy: int) -> None:
        """Move a seleção na grade pelo controle (dx/dy em -1/0/+1)."""
        n = self.model.rowCount()
        if n == 0:
            return
        idx = self.list.currentIndex()
        if not idx.isValid():
            self.list.setCurrentIndex(self.model.index(0, 0))
            return
        # calcula itens por linha pela largura da view
        item_w = int(self.cfg["icon_size"]) + self.list.spacing()
        per_row = max(1, self.list.viewport().width() // item_w)
        row, col = divmod(idx.row(), per_row)
        col = max(0, min(per_row - 1, col + dx))
        row = max(0, min((n - 1) // per_row, row + dy))
        newrow = min(n - 1, row * per_row + col)
        newidx = self.model.index(newrow, 0)
        self.list.setCurrentIndex(newidx)
        self.list.scrollTo(newidx)

    def _pad_back(self) -> None:
        # limpa seleção (volta pro topo) ou sai da tela cheia
        if self.isFullScreen():
            self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)
        else:
            self.list.clearSelection()

    def closeEvent(self, event) -> None:
        pad = getattr(self, "_pad", None)
        if pad is not None:
            pad.stop()
            pad.wait(300)
        super().closeEvent(event)

    # ---------- atualização automática de cores (regra 9) ----------
    def _maybe_auto_update_cores(self) -> None:
        """Atualiza cores instalados a cada ~7 dias, em background."""
        if not self.cfg.get("core_auto_update"):
            return
        import time as _t
        last = int(self.cfg.get("core_last_update", 0))
        if _t.time() - last < 7 * 24 * 3600:
            return
        installed = list(self.cfg.installed_cores().keys())
        if not installed:
            return
        from . import ra_vendor

        class Worker(QThread):
            progress = Signal(str)
            done = Signal(int)

            def run(self):
                n = ra_vendor.update_cores(installed, dest, self.progress.emit)
                self.done.emit(n)

        dest = self.cfg.ra_cores_dir()
        self._core_worker = Worker()
        self._core_worker.done.connect(self._cores_updated)
        self._core_worker.start()

    def _cores_updated(self, n: int) -> None:
        import time as _t
        self.cfg["core_last_update"] = int(_t.time())
        self.cfg.save()

    # ---------- capas (Libretro Thumbnails) ----------
    def download_covers(self) -> None:
        """Baixa capas pros jogos visíveis (filtro atual), em background."""
        if getattr(self, "_cover_worker", None) and self._cover_worker.isRunning():
            self._cover_stop = True  # pede pra parar
            return
        games = [self.model.game_at(i) for i in range(self.model.rowCount())]
        games = [g for g in games if g]
        if not games:
            return
        from . import covers
        self._cover_stop = False
        self.status.setText(tr(self.cfg, "dl_covers_start", n=len(games)))

        class Worker(QThread):
            progress = Signal(int, int, str)
            done = Signal(int, int)

            def run(self):
                n = covers.download_many(
                    games, cfg=win.cfg,
                    progress=lambda i, t, title: self.progress.emit(i, t, title),
                    stop_flag=lambda: stop())
                self.done.emit(n, len(games))

        win = self

        def stop():
            return win._cover_stop

        self._cover_worker = Worker()
        self._cover_worker.progress.connect(self._cover_progress)
        self._cover_worker.done.connect(self._covers_done)
        self._cover_worker.start()

    def _cover_progress(self, i: int, total: int, title: str) -> None:
        self.status.setText(tr(self.cfg, "dl_covers_progress",
                               i=i, total=total, title=title[:40]))

    def _covers_done(self, ok: int, total: int) -> None:
        self.status.setText(tr(self.cfg, "dl_covers_done", ok=ok, total=total))
        self.rescan()  # recarrega pra mostrar as capas novas

    # ---------- UI ----------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 6)
        root.setSpacing(8)

        # topbar
        top = QHBoxLayout()
        title = QLabel(f"<b>{tr(self.cfg, 'app_title')}</b>")
        title.setStyleSheet("font-size: 18px; color: #e8eef8;")
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr(self.cfg, "search"))
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(340)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(200)
        self._debounce.timeout.connect(
            lambda: self.model.set_query(self.search.text()))
        self.search.textChanged.connect(lambda _t: self._debounce.start())

        btn_cfg = QToolButton()
        btn_cfg.setText("⚙")
        btn_cfg.setToolTip(tr(self.cfg, "settings"))
        btn_cfg.setStyleSheet("font-size: 16px;")
        btn_cfg.clicked.connect(self.open_settings)

        btn_rescan = QToolButton()
        btn_rescan.setText("⟳")
        btn_rescan.setToolTip(tr(self.cfg, "rescan"))
        btn_rescan.setStyleSheet("font-size: 16px;")
        btn_rescan.clicked.connect(self.rescan)

        btn_covers = QToolButton()
        btn_covers.setText("📥")
        btn_covers.setToolTip(tr(self.cfg, "dl_covers"))
        btn_covers.setStyleSheet("font-size: 16px;")
        btn_covers.clicked.connect(self.download_covers)

        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.search)
        top.addWidget(btn_covers)
        top.addWidget(btn_rescan)
        top.addWidget(btn_cfg)
        root.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(10)

        # sidebar (colapsável: só ícones com dica, ou nomes + contador)
        side_wrap = QVBoxLayout()
        side_wrap.setSpacing(6)
        self.btn_side = QToolButton()
        self.btn_side.setText("⮐")
        self.btn_side.setToolTip(tr(self.cfg, "sidebar_toggle"))
        self.btn_side.setStyleSheet("font-size: 16px;")
        self.btn_side.clicked.connect(self._toggle_sidebar)
        side_wrap.addWidget(self.btn_side, 0, Qt.AlignLeft)
        self.sidebar = QListWidget()
        self.sidebar.setIconSize(QSize(30, 30))
        self.sidebar.setSpacing(2)
        self.sidebar.setMovement(QListView.Static)
        self.sidebar.setFlow(QListView.TopToBottom)
        self.sidebar.setWrapping(False)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setFrameShape(QFrame.NoFrame)
        self.sidebar.currentItemChanged.connect(self._on_sidebar)
        side_wrap.addWidget(self.sidebar, 1)
        body.addLayout(side_wrap)
        self._apply_sidebar_mode()

        # grade
        self.list = QListView()
        self.list.setModel(self.model)
        self.list.setItemDelegate(self.delegate)
        self.list.setViewMode(QListView.IconMode)
        self.list.setResizeMode(QListView.Adjust)
        self.list.setMovement(QListView.Static)
        self.list.setSpacing(12)
        self.list.setUniformItemSizes(False)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setMouseTracking(True)
        self.list.viewport().setAttribute(Qt.WA_Hover, True)
        self.list.doubleClicked.connect(lambda _i: self.play())
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._context_menu)
        self.list.viewport().installEventFilter(self)
        body.addWidget(self.list, 1)
        root.addLayout(body, 1)

        # status
        self.status = QLabel("")
        self.status.setStyleSheet("color: #5b6b85;")
        root.addWidget(self.status)

        self.setStyleSheet("""
            QWidget { background: #0b0f17; color: #e8eef8; }
            QListWidget { background: #101624; border: none; border-radius: 8px;
                          outline: none; }
            QListWidget::item { padding: 8px 10px; border-radius: 8px; }
            QListWidget::item:selected { background: #1b2537; color: #e8eef8; }
            QListView { background: transparent; border: none; outline: none; }
            QLineEdit { background: #151d2c; border: 1px solid #222c42;
                        border-radius: 16px; padding: 7px 14px; }
            QToolButton { background: #151d2c; border: 1px solid #222c42;
                          border-radius: 16px; padding: 6px 12px; }
            QToolButton:hover { border-color: #4f8cff; }
            QMenuBar, QMenu { background: #131a29; border: 1px solid #2a3550; }
            QMenu::item { padding: 6px 22px; }
            QMenu::item:selected { background: #1e2a40; }
            QMenu::separator { height: 1px; background: #232e46; margin: 4px 8px; }
            QDialog { background: #0f1522; }
            QTabWidget::pane { border: 1px solid #222c42; border-radius: 8px; }
            QTabBar::tab { background: #151d2c; padding: 8px 16px;
                           border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background: #1e2a40; }
            QPushButton { background: #1e2a40; border: 1px solid #2a3550;
                          border-radius: 6px; padding: 6px 14px; }
            QPushButton:hover { border-color: #4f8cff; }
            QComboBox, QCheckBox, QLabel { background: transparent; }
            QComboBox { background: #151d2c; border: 1px solid #222c42;
                        border-radius: 6px; padding: 5px 10px; }
        """)

    # ---------- biblioteca ----------
    def rescan(self) -> None:
        self.status.setText(tr(self.cfg, "scanning"))
        QApplication.processEvents()
        self.games = scan(self.cfg)
        self.model.set_games(self.games)
        self._rebuild_sidebar()
        self.status.setText(tr(self.cfg, "games_n", n=len(self.games)))

    def _toggle_sidebar(self) -> None:
        self.cfg["sidebar_collapsed"] = not self.cfg["sidebar_collapsed"]
        self.cfg.save()
        self._apply_sidebar_mode()
        self._rebuild_sidebar()

    def _apply_sidebar_mode(self) -> None:
        """Ajusta largura/botão/estilo conforme colapsado (só ícones) ou não."""
        collapsed = bool(self.cfg["sidebar_collapsed"])
        self.sidebar.setFixedWidth(54 if collapsed else 150)
        self.btn_side.setText("⮑" if collapsed else "⮐")
        self.btn_side.setToolTip(tr(self.cfg, "sidebar_toggle"))
        if collapsed:
            self.sidebar.setStyleSheet("""
                QListWidget { background: transparent; border: none; }
                QListWidget::item { padding: 8px 0px; border-radius: 8px;
                                    qproperty-iconSize: 30px; }
                QListWidget::item:selected { background: #1b2537; }
            """)
        else:
            self.sidebar.setStyleSheet("")

    def _rebuild_sidebar(self) -> None:
        cur = self.sidebar.currentItem().data(Qt.UserRole) if self.sidebar.currentItem() else ALL
        collapsed = bool(self.cfg["sidebar_collapsed"])
        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        counts: dict[str, int] = {}
        for g in self.games:
            counts[g.system] = counts.get(g.system, 0) + 1
        item = QListWidgetItem()
        item.setData(Qt.UserRole, ALL)
        item.setIcon(QIcon(all_icon(30, self.sidebar)))
        all_label = f"{tr(self.cfg, 'all')}  ({len(self.games)})"
        if collapsed:
            item.setToolTip(all_label)
            item.setTextAlignment(Qt.AlignCenter)
        else:
            item.setText(all_label)
        self.sidebar.addItem(item)
        for sysid, sysdef in SYSTEMS.items():
            if counts.get(sysid):
                it = QListWidgetItem()
                it.setData(Qt.UserRole, sysid)
                it.setIcon(QIcon(system_icon(sysid, 30, self.sidebar)))
                label = f"{sys_short(sysid)}  ({counts[sysid]})"
                if collapsed:
                    it.setToolTip(
                        f"{sys_short(sysid)} — {sysdef.get('emu', '')}  "
                        f"({counts[sysid]})")
                    it.setTextAlignment(Qt.AlignCenter)
                else:
                    it.setText(label)
                self.sidebar.addItem(it)
        target_row = 0
        for i in range(self.sidebar.count()):
            if self.sidebar.item(i).data(Qt.UserRole) == cur:
                target_row = i
        self.sidebar.setCurrentRow(target_row)
        self.sidebar.blockSignals(False)

    def _on_sidebar(self, item: QListWidgetItem | None) -> None:
        if item:
            self.model.set_system(item.data(Qt.UserRole))

    def _current_game(self) -> Game | None:
        idx = self.list.currentIndex()
        return self.model.game_at(idx.row()) if idx.isValid() else None

    # ---------- jogar ----------
    def play(self) -> None:
        game = self._current_game()
        if not game or (self.proc and self.proc.state() != self.proc.NotRunning):
            return
        # modo core do RetroArch: avisa se o core escolhido sumiu da pasta
        emu = self.cfg["emulators"].get(game.system) or {}
        sysdef = SYSTEMS.get(game.system, {})
        if emu.get("mode") == "retroarch":
            core = emu.get("core") or sysdef.get("ra_core", "")
            if core and not self.cfg.ra_core_file(core):
                QMessageBox.information(
                    self, tr(self.cfg, "app_title"),
                    tr(self.cfg, "no_core", s=sys_short(game.system),
                       core=core))
                return
        result = runners.launch(self.cfg, game, self)
        if result is None:
            msg = tr(self.cfg, "no_emulator", s=sys_short(game.system))
            emu_name = SYSTEMS.get(game.system, {}).get("emu", "")
            if appstore.has_appimage(emu_name):
                msg += "\n" + tr(self.cfg, "no_emulator_dl", name=emu_name)
            QMessageBox.information(self, tr(self.cfg, "app_title"), msg)
            return
        self.proc, emu_name = result
        self.running_game = game
        self.proc.finished.connect(self._on_finished)
        self.hide()

    def _on_finished(self, *_a) -> None:
        if self.running_game:
            self.cfg["last_played"][self.running_game.id] = int(time.time())
            self.cfg.save()
        self.proc = None
        self.running_game = None
        self.show()
        self.list.viewport().update()

    def stop(self) -> None:
        if self.proc and self.proc.state() != self.proc.NotRunning:
            self.proc.terminate()
            self.proc.waitForFinished(5000)

    # ---------- menu de contexto ----------
    def _context_menu(self, pos) -> None:
        game = self._current_game()
        if not game:
            return
        menu = QMenu(self)
        running = self.proc and self.proc.state() != self.proc.NotRunning
        a_play = menu.addAction(tr(self.cfg, "play"))
        a_play.setEnabled(not running)
        a_play.triggered.connect(self.play)
        a_stop = menu.addAction(tr(self.cfg, "stop"))
        a_stop.setEnabled(bool(running))
        a_stop.triggered.connect(self.stop)
        menu.addSeparator()
        a_fav = menu.addAction(tr(self.cfg, "unfavorite" if self.model.is_favorite(game)
                                  else "favorite"))
        a_fav.triggered.connect(lambda: self._toggle_fav(game))
        a_verify = menu.addAction(tr(self.cfg, "verify"))
        a_verify.triggered.connect(lambda: self.verify_game(game))
        a_open = menu.addAction(tr(self.cfg, "open_folder"))
        a_open.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(game.dir)))
        core = runners.ra_core_id(self.cfg, game.system)
        if core:
            a_cheats = menu.addAction(tr(self.cfg, "cheats_menu"))
            a_cheats.triggered.connect(lambda: self.open_cheats(game, core))
        menu.addSeparator()
        a_del = menu.addAction(tr(self.cfg, "delete_rom"))
        a_del.triggered.connect(lambda: self.delete_game(game))
        menu.popup(self.list.viewport().mapToGlobal(pos))

    def open_cheats(self, game: Game, core: str) -> None:
        """Seleção de cheats do jogo (botão direito → Cheats)."""
        CheatsDialog(self.cfg, game, core, self).exec()

    def _toggle_fav(self, game: Game) -> None:
        favs = self.cfg["favorites"]
        if game.id in favs:
            favs.remove(game.id)
        else:
            favs.append(game.id)
        self.cfg.save()
        self.list.viewport().update()

    # ---------- integridade ----------
    def verify_game(self, game: Game) -> None:
        total = zeros = 0
        for _root, _dirs, files in os.walk(game.dir):
            for fn in files:
                total += 1
                try:
                    if os.path.getsize(os.path.join(_root, fn)) == 0:
                        zeros += 1
                except OSError:
                    zeros += 1
        lines = [f"{tr(self.cfg, 'verify_title')}: {game.title}",
                 f"arquivos: {total}, zerados: {zeros}",
                 tr(self.cfg, "verify_damaged") if zeros else tr(self.cfg, "verify_ok")]
        QMessageBox.information(self, tr(self.cfg, "app_title"), "\n".join(lines))

    # ---------- apagar (lixeira) ----------
    def delete_game(self, game: Game) -> None:
        r1 = QMessageBox.question(
            self, tr(self.cfg, "app_title"),
            f"{tr(self.cfg, 'delete_confirm')}\n{game.title}\n{game.dir}")
        if r1 != QMessageBox.Yes:
            return
        r2 = QMessageBox.question(self, tr(self.cfg, "app_title"),
                                  tr(self.cfg, "delete_confirm2"))
        if r2 != QMessageBox.Yes:
            return

        trash = os.path.expanduser("~/.local/share/Trash/files")
        info = os.path.expanduser("~/.local/share/Trash/info")
        os.makedirs(trash, exist_ok=True)
        os.makedirs(info, exist_ok=True)

        kind = SYSTEMS.get(game.system, {}).get("kind")
        if game.system == "pc":
            # PC: só tira da lista, nunca mexe no executável
            self.cfg["pc_games"] = [g for g in self.cfg["pc_games"]
                                    if g.get("path") != game.path]
        elif kind == "files":
            # arquivos soltos: move só os arquivos do jogo (mesmo stem)
            stem = os.path.splitext(os.path.basename(game.path))[0].lower()
            targets = []
            for fn in os.listdir(game.dir):
                s, ext = os.path.splitext(fn)
                if s.lower() == stem and ext.lower() in (
                        ".bin", ".cue", ".chd", ".iso", ".img", ".pbp", ".gz",
                        ".zip", ".cso", ".gdi", ".cdi", ".mcd", ".z64", ".n64",
                        ".v64", ".nds", ".nsp", ".xci", ".nro", ".3ds", ".cci",
                        ".wbfs", ".rvz", ".gcz", ".ciso", ".gcm", ".xiso",
                        ".png", ".jpg", ".jpeg", ".webp"):
                    targets.append(os.path.join(game.dir, fn))
            self._to_trash(targets, trash, info)
        else:
            # pastas (PS4/PS3): move a pasta inteira
            self._to_trash([game.dir], trash, info)

        self.cfg["favorites"] = [f for f in self.cfg["favorites"] if f != game.id]
        self.cfg["last_played"].pop(game.id, None)
        self.cfg.save()
        self.rescan()

    def _to_trash(self, targets: list[str], trash: str, info: str) -> None:
        stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for src in targets:
            if not os.path.exists(src):
                continue
            base = os.path.basename(src)
            dest = os.path.join(trash, base)
            if os.path.exists(dest):
                dest += f".{int(time.time())}"
            try:
                os.rename(src, dest)
            except OSError:
                continue
            with open(os.path.join(info, os.path.basename(dest) + ".trashinfo"),
                      "w", encoding="utf-8") as f:
                f.write(f"[Trash Info]\nPath={src}\nDeletionDate={stamp}\n")

    # ---------- configurações ----------
    def open_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            self.delegate._pix.clear()
            self.list.viewport().update()
            self.rescan()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_F5:
            self.rescan()
        elif event.key() == Qt.Key_F11:
            # alterna tela cheia da janela
            self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.play()
        elif event.matches(Qt.KeySequence.Find):
            self.search.setFocus()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        # Ctrl+scroll: aumenta/dimui o tamanho dos ícones (global)
        try:
            if obj is self.list.viewport() and event.type() == QEvent.Wheel:
                if event.modifiers() & Qt.ControlModifier:
                    size = int(self.cfg["icon_size"])
                    step = 20 if size < 180 else 32
                    up = event.angleDelta().y() > 0
                    new = max(72, min(400, size + (step if up else -step)))
                    if new != size:
                        self.cfg["icon_size"] = new
                        self.cfg.save()
                        self.delegate._pix.clear()
                        self.list.doItemsLayout()
                        self.list.viewport().update()
                    return True
        except RuntimeError:
            return False  # objeto Qt já destruído no shutdown
        return super().eventFilter(obj, event)


# ============================ cheats ============================
class CheatsDialog(QDialog):
    """Seleção de cheats por jogo (botão direito → Cheats).

    Grava no .cht da pasta que o RetroArch lê sozinho ao abrir o conteúdo —
    os itens marcados entram em ação sem passar pelo menu do emulador.
    """

    def __init__(self, cfg, game: Game, core: str, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.game = game
        self.core = core
        self.path: str | None = None
        self.checks: list[tuple[int, QCheckBox]] = []
        self._worker: QThread | None = None

        self.setWindowTitle(f"{tr(cfg, 'cheats_title')} — {game.title}")
        self.resize(560, 520)

        root = QVBoxLayout(self)
        self.status = QLabel(tr(cfg, "cheats_loading"))
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText(tr(cfg, "cheats_filter"))
        self.filter.textChanged.connect(self._apply_filter)
        root.addWidget(self.filter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.box = QWidget()
        self.box_l = QVBoxLayout(self.box)
        self.box_l.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.box)
        root.addWidget(scroll, 1)

        row = QHBoxLayout()
        self.b_all = QPushButton(tr(cfg, "cheats_all"))
        self.b_all.clicked.connect(lambda: self._set_all(True))
        self.b_clear = QPushButton(tr(cfg, "cheats_none_sel"))
        self.b_clear.clicked.connect(lambda: self._set_all(False))
        self.b_retry = QPushButton(tr(cfg, "cheats_retry"))
        self.b_retry.clicked.connect(self._load)
        self.b_retry.hide()
        for b in (self.b_all, self.b_clear, self.b_retry):
            row.addWidget(b)
        row.addStretch(1)
        root.addLayout(row)

        buttons = QDialogButtonBox()
        self.b_ok = buttons.addButton(tr(cfg, "save"),
                                      QDialogButtonBox.AcceptRole)
        buttons.addButton(tr(cfg, "cancel"), QDialogButtonBox.RejectRole)
        self.b_ok.setEnabled(False)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._load()

    # ---------- carregar ----------
    def _clear(self) -> None:
        while self.box_l.count():
            item = self.box_l.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.checks.clear()

    def _load(self) -> None:
        """Busca o .cht (cópia local ou download) fora da thread de UI."""
        if self._worker and self._worker.isRunning():
            return  # já tem busca em andamento
        self._clear()
        self.status.setText(tr(self.cfg, "cheats_loading"))
        self.b_retry.hide()
        self.b_ok.setEnabled(False)
        cfg, game, core = self.cfg, self.game, self.core

        class Worker(QThread):
            done = Signal(object, str)  # caminho | "none" | "net"

            def run(self):
                try:
                    p = cheats.ensure(game.system, cfg.ra_cores_dir(), core,
                                      game.path)
                    self.done.emit(p, "" if p else "none")
                except OSError:
                    self.done.emit(None, "net")

        self._worker = Worker()
        self._worker.done.connect(self._loaded)
        self._worker.start()

    def _loaded(self, path, err: str) -> None:
        self.path = path
        if err == "net":
            self.status.setText(tr(self.cfg, "cheats_net"))
            self.b_retry.show()
            return
        if not path:
            self.status.setText(tr(self.cfg, "cheats_none"))
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                items = cheats.parse(f.read())
        except OSError:
            self.status.setText(tr(self.cfg, "cheats_none"))
            return
        if not items:
            self.status.setText(tr(self.cfg, "cheats_empty"))
            return
        for it in items:
            cb = QCheckBox(it["desc"])
            cb.setChecked(it["enable"])
            if it["code"]:
                cb.setToolTip(it["code"])
            self.box_l.addWidget(cb)
            self.checks.append((it["i"], cb))
        self.box_l.addStretch(1)
        self.status.setText(tr(self.cfg, "cheats_found", n=len(items)))
        self.b_ok.setEnabled(True)

    # ---------- ações ----------
    def _set_all(self, on: bool) -> None:
        for _i, cb in self.checks:
            if cb.isVisibleTo(self.box):
                cb.setChecked(on)

    def _apply_filter(self, text: str) -> None:
        q = text.strip().lower()
        for _i, cb in self.checks:
            cb.setVisible(not q or q in cb.text().lower())

    def _save(self) -> None:
        if not self.path:
            return
        enabled = {i for i, cb in self.checks if cb.isChecked()}
        try:
            cheats.set_enabled(self.path, enabled)
        except OSError as e:
            QMessageBox.warning(self, tr(self.cfg, "cheats_title"), str(e))
            return
        QMessageBox.information(self, tr(self.cfg, "cheats_title"),
                                tr(self.cfg, "cheats_saved"))
        self.accept()

    def done(self, r) -> None:
        # não destrói a thread de download no meio (rede lenta)
        if self._worker and self._worker.isRunning():
            self._worker.wait()
        super().done(r)
