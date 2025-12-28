from typing import Optional, Tuple, Union

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

try:
    import qtawesome as qta  # type: ignore

    _HAS_QTA = True
except Exception:
    qta = None  # type: ignore
    _HAS_QTA = False


def qta_icon(name: str, color: Optional[Union[str, Tuple[str, int]]] = None) -> QIcon:
    """
    Return a `QIcon` for the given qtawesome `name`.
    """
    if not _HAS_QTA or qta is None:
        return QIcon()
    try:
        if color is None:
            return qta.icon(name)
        return qta.icon(name, color=color)
    except Exception:
        return QIcon()


def pixmap_for_icon(icon_or_name: Union[QIcon, str], size: int = 16) -> QPixmap:
    if isinstance(icon_or_name, QIcon):
        try:
            return icon_or_name.pixmap(size, size)
        except Exception:
            return QPixmap()
    # Treat as icon name
    icon = qta_icon(icon_or_name)
    try:
        return icon.pixmap(size, size)
    except Exception:
        return QPixmap()


def set_label_icon(
    label: QLabel,
    icon_name_or_icon: Union[str, QIcon],
    size: int = 16,
    color: Optional[Union[str, Tuple[str, int]]] = None,
    fallback_text: str = "",
    keep_aspect: bool = True,
) -> None:
    try:
        from PySide6.QtGui import QGuiApplication

        if QGuiApplication.primaryScreen() is None:
            if fallback_text:
                try:
                    label.setText(fallback_text)
                except Exception:
                    pass
            return
    except Exception:
        pass

    if _HAS_QTA and isinstance(icon_name_or_icon, str):
        try:
            replace_label_with_icon_widget(
                label,
                icon_name_or_icon,
                color=color,
                size=size,
                fallback_text=fallback_text,
            )
            return
        except Exception:
            pass

    pix: QPixmap
    if isinstance(icon_name_or_icon, QIcon):
        pix = pixmap_for_icon(icon_name_or_icon, size)
    else:
        try:
            if _HAS_QTA and color is not None:
                icon = qta_icon(icon_name_or_icon, color=color)
            else:
                icon = qta_icon(icon_name_or_icon)
            pix = pixmap_for_icon(icon, size)
        except Exception:
            pix = QPixmap()

    if pix and not pix.isNull():
        if keep_aspect:
            try:
                scaled = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio)
                label.setPixmap(scaled)
            except Exception:
                if fallback_text:
                    try:
                        label.setText(fallback_text)
                    except Exception:
                        pass
                return
        else:
            try:
                label.setPixmap(pix)
            except Exception:
                if fallback_text:
                    try:
                        label.setText(fallback_text)
                    except Exception:
                        pass
                return
        try:
            label.setText("")
        except Exception:
            pass
    else:
        if fallback_text:
            try:
                label.setText(fallback_text)
            except Exception:
                pass
            return


def set_button_icon(
    button: QPushButton,
    icon_name_or_icon: Union[str, QIcon],
    size: int = 16,
    color: Optional[Union[str, Tuple[str, int]]] = None,
    text: Optional[str] = None,
    icon_only: bool = False,
) -> None:
    icon: QIcon
    if isinstance(icon_name_or_icon, QIcon):
        icon = icon_name_or_icon
    else:
        if _HAS_QTA and color is not None:
            icon = qta_icon(icon_name_or_icon, color=color)
        else:
            icon = qta_icon(icon_name_or_icon)

    try:
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))
    except Exception:
        pass

    if text is not None:
        try:
            button.setText(text)
        except Exception:
            pass

    if icon_only:
        try:
            button.setText("")
        except Exception:
            pass


def make_icon_widget(
    icon_name: str,
    color: Optional[Union[str, Tuple[str, int]]] = None,
    size: int = 16,
) -> QWidget:
    if _HAS_QTA and qta is not None:
        try:
            widget = qta.IconWidget(icon_name, color=color, size=QSize(size, size))
            return widget
        except Exception:
            pass

    label = QLabel()
    set_label_icon(label, icon_name, size=size, color=color)
    return label


def replace_label_with_icon_widget(
    label: QLabel,
    icon_name: str,
    color: Optional[Union[str, Tuple[str, int]]] = None,
    size: int = 16,
    fallback_text: str = "",
) -> None:
    try:
        if not _HAS_QTA:
            if fallback_text:
                try:
                    label.setText(fallback_text)
                except Exception:
                    pass
            return

        if not _HAS_QTA or qta is None:
            raise Exception("qtawesome not available")
        widget = qta.IconWidget(icon_name, color=color, size=QSize(size, size))

        parent = label.parentWidget()
        if parent is None:
            set_label_icon(
                label, icon_name, size=size, color=color, fallback_text=fallback_text
            )
            return

        layout = parent.layout()
        if layout is None:
            set_label_icon(
                label, icon_name, size=size, color=color, fallback_text=fallback_text
            )
            return

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is label:
                try:
                    try:
                        label.clear()
                        label.setText("")
                        label.setPixmap(QPixmap())
                    except Exception:
                        pass

                    try:
                        from PySide6.QtWidgets import QVBoxLayout

                        inner = label.layout()
                        if inner is None:
                            inner = QVBoxLayout()
                            inner.setContentsMargins(0, 0, 0, 0)
                            inner.setSpacing(0)
                            inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            label.setLayout(inner)
                        else:
                            try:
                                while inner.count():
                                    it = inner.takeAt(0)
                                    w2 = it.widget()
                                    if w2 is not None:
                                        try:
                                            w2.setParent(None)
                                            w2.deleteLater()
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                        inner.addWidget(widget)
                        return
                    except Exception:
                        try:
                            layout.removeWidget(label)
                            label.hide()
                            layout.addWidget(widget)
                            return
                        except Exception:
                            set_label_icon(
                                label,
                                icon_name,
                                size=size,
                                color=color,
                                fallback_text=fallback_text,
                            )
                            return
                except Exception:
                    set_label_icon(
                        label,
                        icon_name,
                        size=size,
                        color=color,
                        fallback_text=fallback_text,
                    )
                    return

        set_label_icon(
            label, icon_name, size=size, color=color, fallback_text=fallback_text
        )
    except Exception:
        if fallback_text:
            try:
                label.setText(fallback_text)
            except Exception:
                pass


__all__ = [
    "qta_icon",
    "pixmap_for_icon",
    "set_label_icon",
    "set_button_icon",
    "make_icon_widget",
    "replace_label_with_icon_widget",
]
