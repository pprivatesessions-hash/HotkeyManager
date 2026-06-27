import pytest
from HotkeyManager.models.command import RawCommand
from HotkeyManager.analyzer import analyze_commands
from HotkeyManager.ai.engine import AIEngine
from HotkeyManager.config import HotkeyConfig


class TestAIEngine:
    def setup_method(self):
        self.config = HotkeyConfig(
            prefix_combos=["Ctrl+Alt"],
            exclude_keys=["Ctrl+C", "Ctrl+V"],
            semantic_hints={},
        )
        self.engine = AIEngine(self.config)

    def test_ai_generate_basic(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey=None, page=1),
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        cmd = result.commands[0]
        assert cmd.suggested_hotkey is not None
        assert cmd.semantic_hint is not None

    def test_ai_semantic_destroy(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey=None, page=1),
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        cmd = result.commands[0]
        assert cmd.suggested_hotkey == "Ctrl+Alt+D"

    def test_ai_semantic_copy(self):
        raw_commands = [
            RawCommand(category="Правка", name="Копировать", hotkey=None, page=1),
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        cmd = result.commands[0]
        assert cmd.suggested_hotkey == "Ctrl+Alt+C"

    def test_ai_preserves_existing(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить", hotkey="Ctrl+Alt+D", page=1),
            RawCommand(category="Правка", name="Копировать", hotkey=None, page=1),
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        assert result.commands[0].current_hotkey == "Ctrl+Alt+D"
        assert result.commands[0].suggested_hotkey is None
        assert result.commands[1].suggested_hotkey is not None

    def test_ai_no_duplicates(self):
        raw_commands = [
            RawCommand(category="Блоки", name=f"Команда{i}", hotkey=None, page=1)
            for i in range(5)
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        hotkeys = [cmd.suggested_hotkey for cmd in result.commands if cmd.suggested_hotkey]
        assert len(hotkeys) == len(set(hotkeys))

    def test_ai_first_letter_fallback(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Абракадабра", hotkey=None, page=1),
        ]
        result = analyze_commands(raw_commands)
        result = self.engine.generate(result)

        cmd = result.commands[0]
        assert cmd.suggested_hotkey is not None
