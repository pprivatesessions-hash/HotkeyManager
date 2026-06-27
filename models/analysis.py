from dataclasses import dataclass, field

from .command import Command


@dataclass
class AnalysisResult:
    commands: list[Command] = field(default_factory=list)
    assigned: list[Command] = field(default_factory=list)
    free: list[Command] = field(default_factory=list)
    duplicates: dict[str, list[Command]] = field(default_factory=dict)
    conflicts: list[dict] = field(default_factory=list)
    used_hotkeys: set[str] = field(default_factory=set)

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

    def get_by_category(self, category: str) -> list[Command]:
        return [cmd for cmd in self.commands if cmd.category == category]

    def get_by_status(self, status: str) -> list[Command]:
        return [cmd for cmd in self.commands if cmd.status == status]

    def summary(self) -> dict[str, int]:
        return {
            "total": self.total,
            "assigned": self.assigned_count,
            "free": self.free_count,
            "duplicates": self.duplicate_count,
        }
