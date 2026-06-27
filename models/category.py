from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Category:
    name: str
    weight: float = 1.0
    description: str = ""
    keywords: list = field(default_factory=list)

    def matches_keyword(self, text: str) -> bool:
        lower = text.lower()
        return any(kw.lower() in lower for kw in self.keywords)


DEFAULT_CATEGORIES: Dict[str, Category] = {
    "Блоки": Category(
        name="Блоки",
        weight=1.0,
        keywords=["блок", "разрушить блок", "вставить блок", "группировка"],
    ),
    "Правка": Category(
        name="Правка",
        weight=0.9,
        keywords=["копировать", "вставить", "удалить", "отменить", "повторить", "вырезать"],
    ),
    "Вид": Category(
        name="Вид",
        weight=0.8,
        keywords=["масштаб", "приблизить", "отдалить", "рамка", "сетка"],
    ),
    "Рисование": Category(
        name="Рисование",
        weight=0.85,
        keywords=["линия", "прямоугольник", "окружность", "перо", "кисть"],
    ),
    "Размеры": Category(
        name="Размеры",
        weight=0.7,
        keywords=["размер", "линейка", "угломер", "координат"],
    ),
    "Файл": Category(
        name="Файл",
        weight=0.5,
        keywords=["открыть", "сохранить", "новый", "печать", "экспорт"],
    ),
    "Модель": Category(
        name="Модель",
        weight=0.95,
        keywords=["модель", "конструкция", "деталь", "сборка"],
    ),
    "Материал": Category(
        name="Материал",
        weight=0.6,
        keywords=["материал", "текстура", "цвет", "поверхность"],
    ),
    "Анализ": Category(
        name="Анализ",
        weight=0.65,
        keywords=["анализ", "проверка", "спецификация", "отчет"],
    ),
    "Сервис": Category(
        name="Сервис",
        weight=0.55,
        keywords=["настройка", "параметры", "сервис", "утилита"],
    ),
}
