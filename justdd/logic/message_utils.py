from enum import Enum, IntFlag
from typing import List, Union


class MessageType(Enum):

    INFORMATION = "information"
    WARNING = "warning"
    CRITICAL = "critical"
    QUESTION = "question"


class MessageButton(IntFlag):
    Ok = 0x00000400
    Cancel = 0x00400000
    Yes = 0x00004000
    No = 0x00010000


_ICON_MAP = {
    MessageType.INFORMATION: "fa5s.info-circle",
    MessageType.WARNING: "fa5s.exclamation-triangle",
    MessageType.CRITICAL: "fa5s.times-circle",
    MessageType.QUESTION: "fa5s.question-circle",
}

_COLOR_MAP = {
    MessageType.INFORMATION: "#3498db",
    MessageType.WARNING: "#f39c12",
    MessageType.CRITICAL: "#e74c3c",
    MessageType.QUESTION: "#f9e79f",
}


def get_icon_for_type(mtype: Union[MessageType, str]) -> str:
    if isinstance(mtype, str):
        try:
            mtype = MessageType(mtype.lower())  # type: ignore
        except Exception:
            t = mtype.strip().lower()
            for mt in MessageType:
                if mt.name.lower() == t or mt.value.lower() == t:
                    mtype = mt
                    break
            else:
                return _ICON_MAP[MessageType.INFORMATION]
    return _ICON_MAP.get(mtype, _ICON_MAP[MessageType.INFORMATION])


def get_color_for_type(mtype: Union[MessageType, str]) -> str:
    if isinstance(mtype, str):
        try:
            mtype = MessageType(mtype.lower())  # type: ignore
        except Exception:
            t = mtype.strip().lower()
            for mt in MessageType:
                if mt.name.lower() == t or mt.value.lower() == t:
                    mtype = mt
                    break
            else:
                return _COLOR_MAP[MessageType.INFORMATION]
    return _COLOR_MAP.get(mtype, _COLOR_MAP[MessageType.INFORMATION])


_ORDERED_BUTTONS: List[MessageButton] = [
    MessageButton.No,
    MessageButton.Yes,
    MessageButton.Cancel,
    MessageButton.Ok,
]


def expand_buttons(flags: Union[int, MessageButton]) -> List[MessageButton]:
    if not isinstance(flags, MessageButton):
        flags = MessageButton(flags)
    return [b for b in _ORDERED_BUTTONS if (flags & b) == b]


def labels_for_buttons(flags: Union[int, MessageButton]) -> List[str]:
    btns = expand_buttons(flags)
    labels = []
    for b in btns:
        if b is MessageButton.Ok:
            labels.append("OK")
        elif b is MessageButton.Cancel:
            labels.append("Cancel")
        elif b is MessageButton.Yes:
            labels.append("Yes")
        elif b is MessageButton.No:
            labels.append("No")
        else:
            labels.append(str(int(b)))
    return labels


def default_buttons_for_type(mtype: Union[MessageType, str]) -> MessageButton:
    mt = mtype if isinstance(mtype, MessageType) else MessageType(str(mtype).lower())  # type: ignore
    if mt == MessageType.QUESTION:
        return MessageButton.Yes | MessageButton.No
    return MessageButton.Ok


__all__ = [
    "MessageType",
    "MessageButton",
    "get_icon_for_type",
    "get_color_for_type",
    "expand_buttons",
    "labels_for_buttons",
    "default_buttons_for_type",
]
