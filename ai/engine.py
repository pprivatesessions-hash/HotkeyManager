import logging
import string
from dataclasses import dataclass

from ..config import DEFAULT_CONFIG, HotkeyConfig
from ..models.analysis import AnalysisResult
from ..models.command import Command
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)


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
        self._used: set[str] = set()

        self.command_keywords = self.config.command_keywords
        self.keyboard_layout = self.config.keyboard_layout

        logger.info(
            f"AI Engine: {len(self.command_keywords)} ключевых слов, "
            f"{len(self.keyboard_layout)} символов в раскладке"
        )

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

    def _analyze_command(self, cmd: Command) -> AIResult | None:
        key, confidence, reason = self._extract_key(cmd.name)

        if not key:
            return None

        return AIResult(
            command=cmd,
            suggested_key=key,
            confidence=confidence,
            reason=reason,
        )

    def _extract_key(self, name: str) -> tuple[str | None, float, str]:
        lower = name.lower()

        for keyword, key in self.command_keywords.items():
            if keyword in lower:
                return key, 0.9, f"Ключевое слово: {keyword}"

        words = lower.split()
        if words:
            first_word = words[0]
            if first_word in self.command_keywords:
                key = self.command_keywords[first_word]
                return key, 0.85, f"Первое слово: {first_word}"

        if name and name[0].isalpha():
            if name[0] in self.keyboard_layout:
                key = self.keyboard_layout[name[0]]
                if len(key) == 1:
                    return key, 0.7, f"Первая буква: {name[0]}"
            elif name[0].upper() in string.ascii_uppercase:
                return name[0].upper(), 0.7, f"Первая буква: {name[0]}"

        if name:
            first_char = name[0].lower()
            if first_char in self.keyboard_layout:
                key = self.keyboard_layout[first_char]
                if len(key) == 1:
                    return key, 0.6, f"Транслитерация: {name[0]}"

        return None, 0.0, ""

    def _find_fallback(self, preferred_key: str) -> str | None:
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
