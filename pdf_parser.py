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
            max_age_hours=config.cache.max_age,
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

    for page_num, text in enumerate(pages_text, 1):
        lines = text.split("\n")
        current_category = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if _is_category(line):
                current_category = _clean_category(line)
                continue

            parsed = _parse_command_line(line, current_category, page_num)
            if parsed:
                commands.append(parsed)

    return commands


def _is_category(line: str) -> bool:
    category_keywords = [
        "блок",
        "правка",
        "вид",
        "рисование",
        "размер",
        "файл",
        "сервис",
        "окно",
        "справка",
        "настройк",
        "модель",
        "конструкц",
        "материал",
        "анализ",
        "сборк",
        "спецификац",
        "отчет",
        "печать",
    ]
    lower = line.lower()
    return any(kw in lower for kw in category_keywords) and len(line) < 60


def _clean_category(line: str) -> str:
    line = line.strip().rstrip(":").rstrip("·")
    return line.strip()


def _parse_command_line(line: str, category: str, page: int) -> RawCommand | None:
    hotkey_pattern = r"(Ctrl\+[\w]+|Alt\+[\w]+|Shift\+[\w]+|F\d+)"
    match = re.search(hotkey_pattern, line)

    hotkey = None
    name = line

    if match:
        hotkey = match.group(0)
        name = line[: match.start()].strip()
    else:
        name = line.strip()

    if not name or len(name) < 2:
        return None

    logger.debug(f"Команда: {name} | Категория: {category} | Клавиша: {hotkey}")

    return RawCommand(
        category=category or "Без категории",
        name=name,
        hotkey=hotkey,
        page=page,
    )
