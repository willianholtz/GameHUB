"""Tela de detalhes do jogo: ícone grande + metadados (gamelist.xml)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                               QVBoxLayout)

from .catalog import SYSTEMS
from .icons import system_icon
from .strings import tr


def _fmt_rating(v: float) -> str:
    """0..1 (padrão ES-DE) → '8.5/10'."""
    return f"{max(0.0, min(1.0, v)) * 10:.1f}/10"


class DetailsDialog(QDialog):
    """Detalhes de um jogo: ícone, título, sistema, gênero, nota, descrição e caminho.

    ``play_cb`` (opcional) liga o botão Jogar — quem chama decide o disparo
    (o MainWindow joga o mesmo jogo que está na tela).
    """

    def __init__(self, cfg, game, play_cb=None, parent=None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.game = game
        self.setWindowTitle(game.title)
        self.setMinimumWidth(560)

        root = QHBoxLayout(self)

        # ---------- ícone grande ----------
        self.icon_label = QLabel()
        if game.icon:
            pm = QPixmap(game.icon)
        else:
            pm = system_icon(game.system, 256)
        if not pm.isNull():
            self.icon_label.setPixmap(
                pm.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        root.addWidget(self.icon_label, alignment=Qt.AlignTop)

        # ---------- textos ----------
        col = QVBoxLayout()
        self.title_label = QLabel(game.title)
        f = self.title_label.font()
        f.setBold(True)
        f.setPointSize(max(10, f.pointSize()) + 4)
        self.title_label.setFont(f)
        self.title_label.setWordWrap(True)
        col.addWidget(self.title_label)

        sysdef = SYSTEMS.get(game.system, {})
        self.sys_label = QLabel(sysdef.get("name", game.system))
        self.sys_label.setStyleSheet("color: #8fa3c8;")
        col.addWidget(self.sys_label)

        meta = game.meta or {}
        self.genre_value = self._row(col, tr(cfg, "det_genre"), meta.get("genre", ""))
        self.rating_value = self._row(
            col, tr(cfg, "det_rating"),
            _fmt_rating(meta["rating"]) if "rating" in meta else "")

        self.desc_label = None
        if meta.get("desc"):
            self.desc_label = QLabel(meta["desc"])
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: #b9c4da;")
            col.addWidget(self.desc_label)

        self.path_value = self._row(col, tr(cfg, "det_path"), game.path)
        self.path_value.setWordWrap(True)
        col.addStretch(1)
        root.addLayout(col, 1)

        # ---------- botões ----------
        buttons = QDialogButtonBox(self)
        if play_cb:
            btn = buttons.addButton(tr(cfg, "play"), QDialogButtonBox.AcceptRole)
            btn.clicked.connect(lambda: (self.close(), play_cb()))
        # Fechar com i18n (o padrão do Qt sai em inglês)
        buttons.addButton(tr(cfg, "det_close"), QDialogButtonBox.RejectRole)
        buttons.rejected.connect(self.close)
        buttons.accepted.connect(self.close)
        root2 = QVBoxLayout()
        root2.addLayout(root)
        root2.addWidget(buttons)
        self.setLayout(root2)

    def _row(self, parent_layout, name: str, value: str) -> QLabel:
        """Linha 'Nome: valor' — devolve o label do valor (vazio = linha some)."""
        row = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("color: #5b6b85;")
        lbl_val = QLabel(value)
        lbl_val.setWordWrap(True)
        row.addWidget(lbl_name)
        row.addWidget(lbl_val, 1)
        hidden = not value
        lbl_name.setVisible(not hidden)
        lbl_val.setVisible(not hidden)
        parent_layout.addLayout(row)
        return lbl_val
