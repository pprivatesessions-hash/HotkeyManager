from dataclasses import dataclass, field
from typing import List, Dict, Set
from collections import defaultdict

from .command import Command


@dataclass
class AnalysisResult:
    commands: List[Command] = field(default_factory=list)
    assigned: List[Command] = field(default_factory=list)
    free: List[Command] = field(default_factory=list)
    duplicates: Dict[str, List[Command]] = field(default_factory=dict)
    conflicts: List[Dict] = field(default_factory=list)
    used_hotkeys: Set[str] = field(default_factory=set)

    @property
    def total(self) -> int:
        return len(self.commands)

    @property
    def assigned_count(self) -> int:
        return len(self.assigned)

    @property
    def free_count(self) -> int:
        return len(self.free)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    def get_by_category(self, category: str) -> List[Command]:
        return [cmd for cmd in self.commands if cmd.category == category]

    def get_by_status(self, status: str) -> List[Command]:
        return [cmd for cmd in self.commands if cmd.status == status]

    def summary(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "assigned": self.assigned_count,
            "free": self.free_count,
            "duplicates": self.duplicate_count,
        }
