import logging
import string

from .config import DEFAULT_CONFIG, HotkeyConfig
from .models.analysis import AnalysisResult
from .models.command import Command
from .windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)

KEY_PROXIMITY = {
    "Q": ["W", "A"],
    "W": ["Q", "E", "S"],
    "E": ["W", "R", "D"],
    "R": ["E", "T", "F"],
    "T": ["R", "Y", "G"],
    "Y": ["T", "U", "H"],
    "U": ["Y", "I", "J"],
    "I": ["U", "O", "K"],
    "O": ["I", "P", "L"],
    "P": ["O", "L"],
    "A": ["Q", "S", "Z"],
    "S": ["A", "D", "W", "X"],
    "D": ["S", "F", "E", "C"],
    "F": ["D", "G", "R", "V"],
    "G": ["F", "H", "T", "B"],
    "H": ["G", "J", "Y", "N"],
    "J": ["H", "K", "U", "M"],
    "K": ["J", "L", "I"],
    "L": ["K", "O", "P"],
    "Z": ["A", "X"],
    "X": ["Z", "C", "S"],
    "C": ["X", "V", "D"],
    "V": ["C", "B", "F"],
    "B": ["V", "N", "G"],
    "N": ["B", "M", "H"],
    "M": ["N", "J"],
}


def generate_hotkeys(
    result: AnalysisResult,
    config: HotkeyConfig = None,
) -> AnalysisResult:
    config = config or DEFAULT_CONFIG
    used = result.used_hotkeys.copy()
    checker = WindowsConflictChecker()

    for hotkey in used:
        checker.mark_used(hotkey)

    logger.info(f"Генерация клавиш для {len(result.free)} команд")

    for cmd in result.free:
        new_hotkey = _find_best_hotkey(cmd, used, config, checker)
        if new_hotkey:
            cmd.suggested_hotkey = new_hotkey
            used.add(new_hotkey)
            result.used_hotkeys.add(new_hotkey)
            checker.mark_used(new_hotkey)
            logger.debug(f"{cmd.name} -> {new_hotkey}")
        else:
            logger.warning(f"Не удалось подобрать клавишу для: {cmd.name}")

    logger.info("Генерация завершена")
    return result


def _find_best_hotkey(
    cmd: Command,
    used: set[str],
    config: HotkeyConfig,
    checker: WindowsConflictChecker,
) -> str | None:
    if config.strategy.use_semantic:
        semantic_hotkey = _try_semantic(cmd, used, config, checker)
        if semantic_hotkey:
            return semantic_hotkey

    if config.strategy.use_category_weight:
        category_hotkey = _try_category_based(cmd, used, config, checker)
        if category_hotkey:
            return category_hotkey

    return _next_free(used, config, checker)


def _try_semantic(
    cmd: Command,
    used: set[str],
    config: HotkeyConfig,
    checker: WindowsConflictChecker,
) -> str | None:
    hint = config.semantic_hints.get(cmd.name)
    if not hint:
        hint = _extract_semantic_hint(cmd.name)

    if hint:
        key = hint.upper()
        if key not in string.ascii_uppercase:
            return None

        for prefix in config.prefix_combos:
            combo = f"{prefix}+{key}"
            if combo not in used and combo not in config.exclude_keys:
                check = checker.check(combo)
                if check.is_available:
                    logger.debug(f"Семантическое совпадение: {cmd.name} -> {combo}")
                    return combo

    return None


def _extract_semantic_hint(name: str) -> str | None:
    russian_to_latin = {
        "Разрушить": "D",
        "Вставить": "V",
        "Копировать": "C",
        "Удалить": "X",
        "Отменить": "Z",
        "Повторить": "Y",
        "Сохранить": "S",
        "Открыть": "O",
        "Новый": "N",
        "Печать": "P",
        "Выделить": "A",
        "Найти": "F",
        "Переместить": "M",
        "Повернуть": "R",
        "Масштаб": "Z",
        "Линейка": "L",
        "Размер": "D",
        "Блок": "B",
        "Группа": "G",
        "Зеркало": "M",
        "Массив": "A",
        "Смещение": "O",
        "Обрезать": "T",
        "Удлинить": "E",
        "Скруглить": "F",
        "Текст": "T",
        "Линия": "L",
        "Прямоугольник": "R",
        "Окружность": "C",
        "Дуга": "A",
        "Штриховка": "H",
        "Слой": "L",
        "Цвет": "C",
        "Материал": "M",
    }

    for russian, latin in russian_to_latin.items():
        if russian.lower() in name.lower():
            return latin

    return None


def _try_category_based(
    cmd: Command,
    used: set[str],
    config: HotkeyConfig,
    checker: WindowsConflictChecker,
) -> str | None:
    category_keys = {
        "Блоки": ["B", "G", "U"],
        "Правка": ["C", "V", "X", "Z", "Y"],
        "Вид": ["Z", "F", "H"],
        "Рисование": ["L", "R", "C", "A", "P"],
        "Размеры": ["D", "M", "L"],
        "Модель": ["B", "S", "E"],
        "Материал": ["M", "T", "C"],
    }

    keys = category_keys.get(cmd.category, [])
    for key in keys:
        for prefix in config.prefix_combos:
            combo = f"{prefix}+{key}"
            if combo not in used and combo not in config.exclude_keys:
                check = checker.check(combo)
                if check.is_available:
                    return combo

    return None


def _next_free(used: set[str], config: HotkeyConfig, checker: WindowsConflictChecker) -> str | None:
    letters = list(string.ascii_uppercase)

    for prefix in config.prefix_combos:
        for letter in letters:
            combo = f"{prefix}+{letter}"
            if combo not in used and combo not in config.exclude_keys:
                check = checker.check(combo)
                if check.is_available:
                    return combo

    extra_prefixes = ["Ctrl+Shift", "Alt+Shift"]
    for prefix in extra_prefixes:
        if prefix not in config.prefix_combos:
            for letter in letters:
                combo = f"{prefix}+{letter}"
                if combo not in used and combo not in config.exclude_keys:
                    check = checker.check(combo)
                    if check.is_available:
                        return combo

    return None
