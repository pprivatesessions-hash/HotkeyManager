import pytest
from HotkeyManager.windows_conflicts.database import WindowsConflictDB, ConflictLevel
from HotkeyManager.windows_conflicts.checker import WindowsConflictChecker


class TestWindowsConflicts:
    def setup_method(self):
        self.db = WindowsConflictDB()
        self.checker = WindowsConflictChecker()

    def test_system_key(self):
        info = self.db.check("Ctrl+Alt+Delete")
        assert info.level == ConflictLevel.SYSTEM

    def test_reserved_key(self):
        info = self.db.check("Ctrl+C")
        assert info.level == ConflictLevel.FORBIDDEN

    def test_risky_key(self):
        info = self.db.check("Ctrl+Alt+S")
        assert info.level == ConflictLevel.RISKY

    def test_safe_key(self):
        info = self.db.check("Ctrl+Alt+Q")
        assert info.level == ConflictLevel.SAFE

    def test_checker_available(self):
        result = self.checker.check("Ctrl+Alt+Q")
        assert result.is_available is True

    def test_checker_used_in_app(self):
        self.checker.mark_used("Ctrl+Alt+Q")
        result = self.checker.check("Ctrl+Alt+Q")
        assert result.is_available is False

    def test_checker_forbidden(self):
        result = self.checker.check("Ctrl+C")
        assert result.is_available is False

    def test_find_safe_combo(self):
        combo = self.checker.find_safe_combo("Ctrl+Alt", "Q")
        assert combo == "Ctrl+Alt+Q"

    def test_summary(self):
        summary = self.checker.summary()
        assert "total" in summary
        assert "safe" in summary
        assert "risky" in summary
        assert "forbidden" in summary
