import pytest
from HotkeyManager.models.command import Command
from HotkeyManager.compare.comparator import HotkeyComparator, ChangeType


class TestComparator:
    def setup_method(self):
        self.comparator = HotkeyComparator()

    def test_compare_identical(self):
        old = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]
        new = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]

        result = self.comparator.compare(old, new)

        assert result.has_changes is False
        assert len(result.unchanged) == 1

    def test_compare_new_command(self):
        old = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]
        new = [
            Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D"),
            Command(category="Правка", name="Копировать", current_hotkey="Ctrl+C"),
        ]

        result = self.comparator.compare(old, new)

        assert result.has_changes is True
        assert len(result.added) == 1
        assert result.added[0].command == "Копировать"

    def test_compare_removed_command(self):
        old = [
            Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D"),
            Command(category="Правка", name="Копировать", current_hotkey="Ctrl+C"),
        ]
        new = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]

        result = self.comparator.compare(old, new)

        assert result.has_changes is True
        assert len(result.removed) == 1
        assert result.removed[0].command == "Копировать"

    def test_compare_hotkey_changed(self):
        old = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]
        new = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+X")]

        result = self.comparator.compare(old, new)

        assert result.has_changes is True
        assert len(result.changed) == 1
        assert result.changed[0].change_type == ChangeType.HOTKEY_CHANGED

    def test_compare_category_changed(self):
        old = [Command(category="Блоки", name="Разрушить", current_hotkey="Ctrl+D")]
        new = [Command(category="Правка", name="Разрушить", current_hotkey="Ctrl+D")]

        result = self.comparator.compare(old, new)

        assert result.has_changes is True
        assert len(result.changed) == 1
        assert result.changed[0].change_type == ChangeType.CATEGORY_CHANGED

    def test_summary(self):
        old = [Command(category="Блоки", name="A", current_hotkey="Ctrl+A")]
        new = [Command(category="Блоки", name="B", current_hotkey="Ctrl+B")]

        result = self.comparator.compare(old, new)
        summary = result.summary

        assert summary["old_total"] == 1
        assert summary["new_total"] == 1
        assert summary["removed"] == 1
        assert summary["added"] == 1
