import logging
import string
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from ..models.command import Command
from ..models.analysis import AnalysisResult
from ..config import HotkeyConfig, DEFAULT_CONFIG
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)

RUSSIAN_TO_LATIN = {
    "а": "A", "б": "B", "в": "V", "г": "G", "д": "D",
    "е": "E", "ё": "YO", "ж": "ZH", "з": "Z", "и": "I",
    "й": "Y", "к": "K", "л": "L", "м": "M", "н": "N",
    "о": "O", "п": "P", "р": "R", "с": "S", "т": "T",
    "у": "U", "ф": "F", "х": "KH", "ц": "TS", "ч": "CH",
    "ш": "SH", "щ": "SHCH", "ъ": "", "ы": "Y", "ь": "",
    "э": "E", "ю": "YU", "я": "YA",
}

COMMAND_KEYWORDS = {
    "разрушить": "D",
    "уничтожить": "D",
    "удалить": "X",
    "стереть": "X",
    "копировать": "C",
    "вставить": "V",
    "вставка": "V",
    "вырезать": "X",
    "отменить": "Z",
    "повторить": "Y",
    "сохранить": "S",
    "открыть": "O",
    "новый": "N",
    "печать": "P",
    "выделить": "A",
    "найти": "F",
    "заменить": "H",
    "переместить": "M",
    "двигать": "M",
    "повернуть": "R",
    "вращать": "R",
    "масштаб": "Z",
    "приблизить": "Z",
    "отдалить": "Z",
    "линейка": "L",
    "размер": "D",
    "замер": "L",
    "блок": "B",
    "группа": "G",
    "группировка": "G",
    "разгруппировать": "U",
    "зеркало": "M",
    "отразить": "M",
    "массив": "A",
    "копия": "C",
    "смещение": "O",
    "сдвинуть": "O",
    "обрезать": "T",
    "удлинить": "E",
    "скруглить": "F",
    "скос": "C",
    "текст": "T",
    "надпись": "T",
    "линия": "L",
    "отрезок": "L",
    "прямоугольник": "R",
    "квадрат": "R",
    "окружность": "C",
    "круг": "C",
    "дуга": "A",
    "штриховка": "H",
    "заливка": "H",
    "слой": "L",
    "уровень": "L",
    "цвет": "C",
    "материал": "M",
    "текстура": "T",
    "конструкция": "K",
    "деталь": "D",
    "сборка": "S",
    "экспорт": "E",
    "импорт": "I",
    "параметры": "P",
    "настройка": "S",
    "справка": "H",
    "проверка": "C",
    "анализ": "A",
    "спецификация": "S",
    "отчет": "R",
}


@dataclass
class AIResult:
    command: Command
    suggested_key: str
    confidence: float
    reason: str


class AIEngine:
    def __init__(self, config: HotkeyConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.checker = WindowsConflictChecker()
        self._used: Set[str] = set()

    def generate(
        self,
        result: AnalysisResult,
    ) -> AnalysisResult:
        logger.info(f"AI генерация для {len(result.free)} команд")

        ai_results = []
        for cmd in result.free:
            ai_result = self._analyze_command(cmd)
            if ai_result:
                ai_results.append(ai_result)

        ai_results.sort(key=lambda x: x.confidence, reverse=True)

        for ai_result in ai_results:
            cmd = ai_result.command
            combo = f"Ctrl+Alt+{ai_result.suggested_key}"

            if combo not in self._used:
                check = self.checker.check(combo)
                if check.is_available:
                    cmd.suggested_hotkey = combo
                    cmd.semantic_hint = ai_result.reason
                    self._used.add(combo)
                    self.checker.mark_used(combo)
                    logger.debug(
                        f"{cmd.name} → {combo} "
                        f"(уверенность: {ai_result.confidence:.0%}, "
                        f"причина: {ai_result.reason})"
                    )
                    continue

            fallback = self._find_fallback(ai_result.suggested_key)
            if fallback:
                cmd.suggested_hotkey = fallback
                cmd.semantic_hint = ai_result.reason
                self._used.add(fallback)
                self.checker.mark_used(fallback)
                logger.debug(f"{cmd.name} → {fallback} (fallback)")

        logger.info("AI генерация завершена")
        return result

    def _analyze_command(self, cmd: Command) -> Optional[AIResult]:
        key, confidence, reason = self._extract_key(cmd.name)

        if not key:
            return None

        return AIResult(
            command=cmd,
            suggested_key=key,
            confidence=confidence,
            reason=reason,
        )

    def _extract_key(self, name: str) -> Tuple[Optional[str], float, str]:
        lower = name.lower()

        for keyword, key in COMMAND_KEYWORDS.items():
            if keyword in lower:
                return key, 0.9, f"Ключевое слово: {keyword}"

        words = lower.split()
        if words:
            first_word = words[0]
            if first_word in COMMAND_KEYWORDS:
                key = COMMAND_KEYWORDS[first_word]
                return key, 0.85, f"Первое слово: {first_word}"

        if name and name[0].isalpha():
            if name[0] in RUSSIAN_TO_LATIN:
                key = RUSSIAN_TO_LATIN[name[0]]
                if len(key) == 1:
                    return key, 0.7, f"Первая буква: {name[0]}"
            elif name[0].upper() in string.ascii_uppercase:
                return name[0].upper(), 0.7, f"Первая буква: {name[0]}"

        if name:
            first_char = name[0].lower()
            if first_char in RUSSIAN_TO_LATIN:
                key = RUSSIAN_TO_LATIN[first_char]
                if len(key) == 1:
                    return key, 0.6, f"Транслитерация: {name[0]}"

        return None, 0.0, ""

    def _find_fallback(self, preferred_key: str) -> Optional[str]:
        import string

        key_order = [preferred_key]
        for letter in string.ascii_uppercase:
            if letter != preferred_key:
                key_order.append(letter)

        for key in key_order:
            combo = f"Ctrl+Alt+{key}"
            if combo not in self._used:
                check = self.checker.check(combo)
                if check.is_available:
                    return combo

        for key in key_order:
            combo = f"Ctrl+Shift+Alt+{key}"
            if combo not in self._used:
                check = self.checker.check(combo)
                if check.is_available:
                    return combo

        return None
