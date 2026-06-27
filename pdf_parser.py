import logging
import re
from pathlib import Path

import fitz

from .config import DEFAULT_CONFIG, HotkeyConfig
from .models.command import RawCommand
from .ocr.base import OCRProvider
from .ocr.cache import OCRCache
from .ocr.tesseract_provider import TesseractProvider

logger = logging.getLogger(__name__)


def parse_pdf(
    pdf_path: str,
    config: HotkeyConfig = None,
    ocr_provider: OCRProvider = None,
    use_cache: bool = True,
) -> list[RawCommand]:
    config = config or DEFAULT_CONFIG
    ocr_provider = ocr_provider or TesseractProvider(
        languages=config.ocr.languages,
        dpi=config.ocr.dpi,
        preprocess=config.ocr.preprocess,
    )
    cache = (
        OCRCache(
            cache_dir=config.cache.directory,
            max_age_hours=config.cache.max_age_hours,
        )
        if use_cache and config.cache.enabled
        else None
    )

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF не найден: {pdf_path}")

    logger.info(f"Чтение PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        if cache:
            cached = cache.get(pdf_path, page_num)
            if cached:
                pages_text.append(cached)
                continue

        pix = page.get_pixmap(dpi=config.ocr.dpi)
        from PIL import Image

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        text = ocr_provider.recognize(img)
        pages_text.append(text)

        if cache:
            cache.set(pdf_path, page_num, text)

        logger.debug(f"Страница {page_num + 1}: {len(text)} символов")

    doc.close()

    commands = _extract_commands(pages_text)
    logger.info(f"Извлечено команд: {len(commands)}")

    return commands


def _extract_commands(pages_text: list[str]) -> list[RawCommand]:
    commands = []
    categories_found: list[str] = []

    all_lines = []
    for page_num, text in enumerate(pages_text, 1):
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                all_lines.append((line, page_num))

    has_hotkeys = any(re.search(r"(Ctrl\+|Alt\+|Shift\+|F\d+|\[.*\])", line) for line, _ in all_lines)
    all_short = all(len(line) < 40 for line, _ in all_lines)

    if all_short and not has_hotkeys:
        for line, page_num in all_lines:
            cat_name = _clean_category(line)
            if cat_name and cat_name not in categories_found:
                categories_found.append(cat_name)
        for cat in categories_found:
            commands.append(RawCommand(
                category=cat,
                name=cat,
                hotkey=None,
                page=1,
            ))
        return commands

    current_category = ""
    for line, page_num in all_lines:
        if _is_category(line):
            current_category = _clean_category(line)
            if current_category not in categories_found:
                categories_found.append(current_category)
            continue

        parsed = _parse_command_line(line, current_category, page_num)
        if parsed:
            commands.append(parsed)

    return commands


def _is_category(line: str) -> bool:
    if len(line) > 40:
        return False

    if re.search(r"(Ctrl\+|Alt\+|Shift\+|F\d+|\[.*\])", line):
        return False

    if re.search(r"[-–—=]", line):
        return False

    exact_categories = {
        "блок", "блоки",
        "правка",
        "вид", "вид 3d",
        "рисование",
        "размер", "размеры",
        "файл",
        "сервис",
        "окно", "окна",
        "справка",
        "настройк", "настройки",
        "модель", "моделирование",
        "конструкц", "конструкция",
        "материал", "материалы",
        "анализ",
        "сборк", "сборка",
        "спецификац", "спецификация",
        "отчет", "отчеты",
        "печать",
        "выделение",
        "группировка",
        "директивы",
        "изделие", "изделия",
        "измерить", "измерения",
        "мебель",
        "операции",
        "оформить", "оформление",
        "править",
        "разрушить",
        "скрипты",
        "строить",
        "удаление",
        "управление курсором",
        "пользовательские скрипты",
        "экструзия",
        "торцевание",
        "раскрой",
        "создание",
        "редактирование",
        "преобразование",
        "вставка",
        "копирование",
        "перенос",
        "поворот",
        "масштаб",
        "отображение",
        "скрытие",
        "слои",
        "типы",
        "свойства",
        "параметры",
        "проверка",
        "экспорт",
        "импорт",
    }

    lower = line.lower().strip()

    for cat in exact_categories:
        if lower == cat:
            return True

    return False


def _clean_category(line: str) -> str:
    line = line.strip().rstrip(":").rstrip("·")
    return line.strip()


def _parse_command_line(line: str, category: str, page: int) -> RawCommand | None:
    bracket_pattern = r"\[([^\]]+)\]"
    bracket_match = re.search(bracket_pattern, line)

    if bracket_match:
        hotkey = bracket_match.group(1).strip()
        name = line[: bracket_match.start()].strip()
        name = re.sub(r"[-–—=]\s*$", "", name).strip()
    else:
        hotkey_pattern = r"(?:-\s*)?(Ctrl\+[\w]+|Alt\+[\w]+|Shift\+[\w]+|F\d+)"
        match = re.search(hotkey_pattern, line, re.IGNORECASE)
        if match:
            hotkey = match.group(1)
            name = line[: match.start()].strip()
            name = re.sub(r"[-–—]\s*$", "", name).strip()
        else:
            hotkey = None
            name = line.strip()

    name = re.sub(r"[-–—=]\s*$", "", name).strip()

    if not name or len(name) < 2:
        return None

    logger.debug(f"Команда: {name} | Категория: {category} | Клавиша: {hotkey}")

    return RawCommand(
        category=category or "Без категории",
        name=name,
        hotkey=hotkey,
        page=page,
    )
