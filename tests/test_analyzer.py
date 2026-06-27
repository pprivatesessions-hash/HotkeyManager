import pytest
from HotkeyManager.models.command import RawCommand, Command
from HotkeyManager.analyzer import analyze_commands, find_conflicts


class TestAnalyzer:
    def test_analyze_commands_basic(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey="Ctrl+D", page=1),
            RawCommand(category="Правка", name="Копировать", hotkey="Ctrl+C", page=1),
            RawCommand(category="Вид", name="Масштаб", hotkey=None, page=1),
        ]

        result = analyze_commands(raw_commands)

        assert result.total == 3
        assert result.assigned_count == 2
        assert result.free_count == 1
        assert result.duplicate_count == 0

    def test_analyze_commands_with_duplicates(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Команда1", hotkey="Ctrl+D", page=1),
            RawCommand(category="Правка", name="Команда2", hotkey="Ctrl+D", page=1),
        ]

        result = analyze_commands(raw_commands)

        assert result.duplicate_count == 1
        assert "Ctrl+D" in result.duplicates
        assert len(result.duplicates["Ctrl+D"]) == 2

    def test_analyze_commands_status(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey="Ctrl+D", page=1),
            RawCommand(category="Вид", name="Масштаб", hotkey=None, page=1),
        ]

        result = analyze_commands(raw_commands)

        assigned = [cmd for cmd in result.commands if cmd.status == "assigned"]
        free = [cmd for cmd in result.commands if cmd.status == "needs_assignment"]

        assert len(assigned) == 1
        assert len(free) == 1

    def test_find_conflicts(self):
        used = {"Ctrl+D", "Ctrl+C"}

        assert find_conflicts("Ctrl+D", used) is True
        assert find_conflicts("Ctrl+A", used) is False

    def test_empty_commands(self):
        result = analyze_commands([])

        assert result.total == 0
        assert result.assigned_count == 0
        assert result.free_count == 0
