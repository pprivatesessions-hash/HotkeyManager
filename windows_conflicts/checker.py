import logging
from typing import List, Set, Dict
from dataclasses import dataclass

from .database import WindowsConflictDB, ConflictLevel, HotkeyInfo

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    combo: str
    info: HotkeyInfo
    is_available: bool
    reason: str


class WindowsConflictChecker:
    def __init__(self):
        self.db = WindowsConflictDB()
        self._used_in_app: Set[str] = set()

    def mark_used(self, combo: str) -> None:
        self._used_in_app.add(combo)

    def clear_used(self) -> None:
        self._used_in_app.clear()

    def check(self, combo: str) -> CheckResult:
        info = self.db.check(combo)

        if combo in self._used_in_app:
            return CheckResult(
                combo=combo,
                info=info,
                is_available=False,
                reason="Уже используется в приложении",
            )

        if info.level == ConflictLevel.SYSTEM:
            return CheckResult(
                combo=combo,
                info=info,
                is_available=False,
                reason=f"Системная: {info.description}",
            )

        if info.level == ConflictLevel.FORBIDDEN:
            return CheckResult(
                combo=combo,
                info=info,
                is_available=False,
                reason=f"Запрещена: {info.description}",
            )

        if info.level == ConflictLevel.RISKY:
            return CheckResult(
                combo=combo,
                info=info,
                is_available=True,
                reason=f"Риск: {info.description}",
            )

        return CheckResult(
            combo=combo,
            info=info,
            is_available=True,
            reason="Свободна",
        )

    def find_safe_combo(self, prefix: str, key: str) -> str:
        combo = f"{prefix}+{key}"
        result = self.check(combo)

        if result.is_available:
            return combo

        import string
        for letter in string.ascii_uppercase:
            if letter == key:
                continue
            combo = f"{prefix}+{letter}"
            result = self.check(combo)
            if result.is_available:
                return combo

        return ""

    def get_all_conflicts(self) -> Dict[str, List[str]]:
        conflicts = {}
        import string
        for letter in string.ascii_uppercase:
            for prefix in ["Ctrl+Alt", "Ctrl+Shift+Alt"]:
                combo = f"{prefix}+{letter}"
                result = self.check(combo)
                if not result.is_available:
                    if combo not in conflicts:
                        conflicts[combo] = []
                    conflicts[combo].append(result.reason)
        return conflicts

    def summary(self) -> Dict[str, int]:
        import string
        total = 0
        safe = 0
        risky = 0
        forbidden = 0

        for letter in string.ascii_uppercase:
            for prefix in ["Ctrl+Alt", "Ctrl+Shift+Alt"]:
                combo = f"{prefix}+{letter}"
                result = self.check(combo)
                total += 1
                if result.is_available:
                    if result.info.level == ConflictLevel.RISKY:
                        risky += 1
                    else:
                        safe += 1
                else:
                    forbidden += 1

        return {
            "total": total,
            "safe": safe,
            "risky": risky,
            "forbidden": forbidden,
        }
