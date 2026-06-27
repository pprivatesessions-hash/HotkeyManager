from dataclasses import dataclass
from typing import Optional


@dataclass
class RawCommand:
    category: str
    name: str
    hotkey: Optional[str]
    page: int


@dataclass
class Command:
    category: str
    name: str
    current_hotkey: Optional[str]
    suggested_hotkey: Optional[str] = None
    status: str = "free"
    conflict_with: Optional[str] = None
    priority: float = 0.0
    semantic_hint: Optional[str] = None
