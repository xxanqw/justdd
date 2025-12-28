from enum import Enum
from typing import Any


class StepState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"

    def is_waiting(self) -> bool:
        return self is StepState.WAITING

    def is_active(self) -> bool:
        return self is StepState.ACTIVE

    def is_completed(self) -> bool:
        return self is StepState.COMPLETED

    def is_error(self) -> bool:
        return self is StepState.ERROR

    def is_final(self) -> bool:
        return self in (StepState.COMPLETED, StepState.ERROR)

    @classmethod
    def from_value(cls, value: Any) -> "StepState":
        if isinstance(value, cls):
            return value
        val = str(value).strip().lower()
        for member in cls:
            if member.name.lower() == val or member.value.lower() == val:
                return member
        raise ValueError(f"Unknown StepState: {value!r}")


__all__ = ["StepState"]
