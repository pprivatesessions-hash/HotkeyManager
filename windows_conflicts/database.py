import logging
from enum import Enum
from typing import Set, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConflictLevel(Enum):
    NONE = "none"
    SAFE = "safe"
    RISKY = "risky"
    FORBIDDEN = "forbidden"
    SYSTEM = "system"


@dataclass
class HotkeyInfo:
    combo: str
    level: ConflictLevel
    description: str
    reserved_by: str


class WindowsConflictDB:
    def __init__(self):
        self._system_keys = self._init_system_keys()
        self._reserved_combos = self._init_reserved_combos()
        self._risky_combos = self._init_risky_combos()
        self._app_specific = self._init_app_specific()

    def _init_system_keys(self) -> Set[str]:
        return {
            "Ctrl+Alt+Delete",
            "Ctrl+Shift+Esc",
            "Alt+Tab",
            "Alt+F4",
            "Win+L",
            "Win+R",
            "Win+E",
            "Win+D",
            "Win+M",
            "Win+Shift+S",
            "PrintScreen",
            "Ctrl+PrintScreen",
            "Alt+PrintScreen",
        }

    def _init_reserved_combos(self) -> Dict[str, str]:
        return {
            "Ctrl+C": "Копировать",
            "Ctrl+V": "Вставить",
            "Ctrl+X": "Вырезать",
            "Ctrl+Z": "Отменить",
            "Ctrl+Y": "Повторить",
            "Ctrl+A": "Выделить все",
            "Ctrl+S": "Сохранить",
            "Ctrl+O": "Открыть",
            "Ctrl+N": "Новый",
            "Ctrl+P": "Печать",
            "Ctrl+F": "Найти",
            "Ctrl+H": "Заменить",
            "Ctrl+G": "Перейти к строке",
            "Ctrl+L": "Адресная строка",
            "Ctrl+W": "Закрыть вкладку",
            "Ctrl+T": "Новая вкладка",
            "Ctrl+R": "Обновить",
            "Ctrl+Shift+T": "Восстановить вкладку",
            "Ctrl+Tab": "Следующая вкладка",
            "Ctrl+PageDown": "Следующая вкладка",
            "Ctrl+PageUp": "Предыдущая вкладка",
            "Ctrl+Home": "Начало документа",
            "Ctrl+End": "Конец документа",
            "Ctrl+Left": "Слово влево",
            "Ctrl+Right": "Слово вправо",
            "Ctrl+Up": "Абзац вверх",
            "Ctrl+Down": "Абзац вниз",
            "Shift+Delete": "Удалить без корзины",
            "Shift+F10": "Контекстное меню",
            "Alt+Space": "Меню окна",
            "Alt+F4": "Закрыть окно",
            "Alt+Enter": "Свойства",
            "F1": "Справка",
            "F2": "Переименовать",
            "F3": "Найти далее",
            "F4": "Адресная строка",
            "F5": "Обновить",
            "F6": "Панели навигации",
            "F7": "Проверка орфографии",
            "F10": "Меню",
            "F11": "Полноэкранный режим",
            "F12": "Сохранить как",
            "Delete": "Удалить",
            "Insert": "Вставка",
            "Home": "Начало строки",
            "End": "Конец строки",
            "PageUp": "Страницу вверх",
            "PageDown": "Страницу вниз",
        }

    def _init_risky_combos(self) -> Dict[str, str]:
        return {
            "Ctrl+Alt+A": "Может конфликтовать с диспетчером задач",
            "Ctrl+Alt+B": "Может конфликтовать с Some software",
            "Ctrl+Alt+F": "Может конфликтовать с Teams",
            "Ctrl+Alt+H": "Может конфликтовать с Outlook",
            "Ctrl+Alt+I": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+K": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+L": "Может конфликтовать с LockAPP",
            "Ctrl+Alt+M": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+O": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+P": "Может конфликтовать с Photoshop",
            "Ctrl+Alt+R": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+S": "Может конфликтовать с Spotify",
            "Ctrl+Alt+T": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+W": "Может конфликтовать с некоторыми приложениями",
            "Ctrl+Alt+X": "Может конфликтовать с Malwarebytes",
            "Ctrl+Alt+Z": "Может конфликтовать с NVIDIA",
        }

    def _init_app_specific(self) -> Dict[str, Dict[str, str]]:
        return {
            "AutoCAD": {
                "Ctrl+Z": "Отменить",
                "Ctrl+Y": "Повторить",
                "Ctrl+C": "Копировать",
                "Ctrl+V": "Вставить",
                "Ctrl+X": "Вырезать",
                "Ctrl+A": "Выделить все",
                "F1": "Справка",
                "F2": "Переименовать",
                "F3": "Найти",
                "F5": "Обновить",
                "F7": "Орфография",
                "F8": "Ortho mode",
                "F10": "Polar tracking",
                "F11": "Object snap tracking",
                "F12": "Dynamic UCS",
            },
            "3dsMax": {
                "Ctrl+Z": "Отменить",
                "Ctrl+Y": "Повторить",
                "Ctrl+C": "Копировать",
                "Ctrl+V": "Вставить",
                "F1": "Справка",
                "F2": "Wireframe",
                "F3": "Edged faces",
                "F4": "Edged faces toggle",
                "F5": "Следующий уровень",
                "F9": "Snap toggle",
            },
        }

    def check(self, combo: str) -> HotkeyInfo:
        if combo in self._system_keys:
            return HotkeyInfo(
                combo=combo,
                level=ConflictLevel.SYSTEM,
                description="Системная комбинация Windows",
                reserved_by="Windows",
            )

        if combo in self._reserved_combos:
            return HotkeyInfo(
                combo=combo,
                level=ConflictLevel.FORBIDDEN,
                description=self._reserved_combos[combo],
                reserved_by="Стандартные сочетания",
            )

        if combo in self._risky_combos:
            return HotkeyInfo(
                combo=combo,
                level=ConflictLevel.RISKY,
                description=self._risky_combos[combo],
                reserved_by="Возможные конфликты",
            )

        return HotkeyInfo(
            combo=combo,
            level=ConflictLevel.SAFE,
            description="Свободна",
            reserved_by="",
        )

    def get_safe_prefixes(self) -> List[str]:
        return ["Ctrl+Alt", "Ctrl+Shift+Alt"]

    def get_forbidden_combos(self) -> Set[str]:
        return set(self._reserved_combos.keys()) | self._system_keys
