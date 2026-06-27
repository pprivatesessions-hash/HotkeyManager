from dataclasses import dataclass
from typing import Optional


@dataclass
class Hotkey:
    raw: str
    modifier: str
    key: str

    @classmethod
    def parse(cls, raw: str) -> Optional["Hotkey"]:
        if not raw:
            return None

        parts = raw.split("+")
        if len(parts) < 2:
            return None

        modifier = "+".join(parts[:-1])
        key = parts[-1]

        return cls(raw=raw, modifier=modifier, key=key)

    @property
    def is_ctrl_alt(self) -> bool:
        return self.modifier == "Ctrl+Alt"

    @property
    def is_ctrl_shift_alt(self) -> bool:
        return self.modifier == "Ctrl+Shift+Alt"

    def __hash__(self) -> int:
        return hash(self.raw)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Hotkey):
            return False
        return self.raw == other.raw
