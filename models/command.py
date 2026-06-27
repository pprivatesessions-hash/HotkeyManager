from dataclasses import dataclass


@dataclass
class RawCommand:
    category: str
    name: str
    hotkey: str | None
    page: int


@dataclass
class Command:
    category: str
    name: str
    current_hotkey: str | None
    suggested_hotkey: str | None = None
    status: str = "free"
    conflict_with: str | None = None
    priority: float = 0.0
    semantic_hint: str | None = None
