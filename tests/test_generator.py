from HotkeyManager.config import HotkeyConfig
from HotkeyManager.generator import _extract_semantic_hint, generate_hotkeys
from HotkeyManager.models.command import RawCommand


class TestGenerator:
    def setup_method(self):
        self.config = HotkeyConfig(
            prefix_combos=["Ctrl+Alt", "Ctrl+Shift+Alt"],
            exclude_keys=["Ctrl+C", "Ctrl+V"],
            semantic_hints={
                "Destroy": "D",
                "Copy": "C",
            },
            category_weights={"Блоки": 1.0, "Правка": 0.9},
        )

    def test_generate_hotkeys_basic(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey=None, page=1),
            RawCommand(category="Правка", name="Копировать", hotkey=None, page=1),
        ]

        from HotkeyManager.analyzer import analyze_commands

        result = analyze_commands(raw_commands)
        result = generate_hotkeys(result, self.config)

        for cmd in result.free:
            assert cmd.suggested_hotkey is not None

    def test_generate_hotkeys_preserves_existing(self):
        raw_commands = [
            RawCommand(category="Блоки", name="Разрушить блок", hotkey="Ctrl+Alt+D", page=1),
            RawCommand(category="Вид", name="Масштаб", hotkey=None, page=1),
        ]

        from HotkeyManager.analyzer import analyze_commands

        result = analyze_commands(raw_commands)
        result = generate_hotkeys(result, self.config)

        assert result.commands[0].current_hotkey == "Ctrl+Alt+D"
        assert result.commands[0].suggested_hotkey is None

    def test_generate_hotkeys_no_duplicates(self):
        raw_commands = [
            RawCommand(category="Блоки", name=f"Команда{i}", hotkey=None, page=1) for i in range(10)
        ]

        from HotkeyManager.analyzer import analyze_commands

        result = analyze_commands(raw_commands)
        result = generate_hotkeys(result, self.config)

        hotkeys = [cmd.suggested_hotkey for cmd in result.commands if cmd.suggested_hotkey]
        assert len(hotkeys) == len(set(hotkeys))

    def test_semantic_hint_destroy(self):
        hint = _extract_semantic_hint("Разрушить блок")
        assert hint == "D"

    def test_semantic_hint_copy(self):
        hint = _extract_semantic_hint("Копировать")
        assert hint == "C"

    def test_semantic_hint_not_found(self):
        hint = _extract_semantic_hint("Несуществующая команда")
        assert hint is None
