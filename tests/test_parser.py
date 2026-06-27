from HotkeyManager.pdf_parser import _clean_category, _is_category, _parse_command_line


class TestParser:
    def test_is_category_block(self):
        assert _is_category("Блоки") is True

    def test_is_category_edit(self):
        assert _is_category("Правка") is True

    def test_is_category_not_category(self):
        assert _is_category("Выделить все объекты на текущем слое") is False

    def test_clean_category_with_colon(self):
        assert _clean_category("Блоки:") == "Блоки"

    def test_clean_category_with_dot(self):
        assert _clean_category("Блоки·") == "Блоки"

    def test_clean_category_simple(self):
        assert _clean_category("  Блоки  ") == "Блоки"

    def test_parse_command_line_with_hotkey(self):
        result = _parse_command_line("Разрушить блок Ctrl+D", "Блоки", 1)
        assert result is not None
        assert result.name == "Разрушить блок"
        assert result.hotkey == "Ctrl+D"
        assert result.category == "Блоки"

    def test_parse_command_line_without_hotkey(self):
        result = _parse_command_line("Вставить блок", "Блоки", 1)
        assert result is not None
        assert result.name == "Вставить блок"
        assert result.hotkey is None

    def test_parse_command_line_empty(self):
        result = _parse_command_line("", "Блоки", 1)
        assert result is None

    def test_parse_command_line_short(self):
        result = _parse_command_line("А", "Блоки", 1)
        assert result is None
