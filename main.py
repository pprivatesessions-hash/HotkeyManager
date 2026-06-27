import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .pdf_parser import parse_pdf
from .analyzer import analyze_commands
from .generator import generate_hotkeys
from .exporter_excel import export_excel
from .exporter_md import export_markdown
from .exporter_json import export_json

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="HotkeyManager — менеджер горячих клавиш для БАЗИС-Мебельщик"
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        help="Путь к PDF файлу с горячими клавишами",
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Папка для выходных файлов (по умолчанию: output)",
    )
    parser.add_argument(
        "-c", "--config",
        help="Путь к файлу конфигурации (config.yaml)",
    )
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Не генерировать новые клавиши",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Не использовать кэш OCR",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Использовать AI генерацию",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Запустить графический интерфейс (Tkinter)",
    )
    parser.add_argument(
        "--gui-qt",
        action="store_true",
        help="Запустить графический интерфейс (PySide6/Qt)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Очистить кэш и выйти",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    config = load_config(args.config)

    if args.clear_cache:
        from .ocr.cache import OCRCache
        cache = OCRCache(cache_dir=config.cache.directory)
        count = cache.clear()
        print(f"Очищено {count} файлов кэша")
        sys.exit(0)

    if args.gui_qt:
        try:
            from .gui.app_qt import run_qt_app
            run_qt_app()
        except ImportError:
            print("PySide6 не установлен. Установите: pip install PySide6")
            print("Или используйте --gui для Tkinter версии")
            sys.exit(1)
        sys.exit(0)

    if args.gui:
        from .gui import HotkeyManagerApp
        app = HotkeyManagerApp()
        app.run()
        sys.exit(0)

    if not args.pdf_path:
        parser.print_help()
        sys.exit(1)

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        logger.error(f"Файл не найден: {pdf_path}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Чтение PDF: {pdf_path}")
    raw_commands = parse_pdf(str(pdf_path), config=config, use_cache=not args.no_cache)
    logger.info(f"Найдено команд: {len(raw_commands)}")

    logger.info("Анализ команд...")
    result = analyze_commands(raw_commands)
    logger.info(
        f"Назначено: {result.assigned_count}, "
        f"Требует назначения: {result.free_count}, "
        f"Дубликатов: {result.duplicate_count}"
    )

    if not args.no_generate and result.free:
        if args.ai:
            logger.info(f"AI генерация для {len(result.free)} команд...")
            from .ai.engine import AIEngine
            ai_engine = AIEngine(config)
            result = ai_engine.generate(result)
        else:
            logger.info(f"Генерация новых клавиш для {len(result.free)} команд...")
            result = generate_hotkeys(result, config)

    excel_path = output_dir / "Hotkeys.xlsx"
    md_path = output_dir / "Hotkeys.md"
    json_path = output_dir / "hotkeys.json"

    export_excel(result, str(excel_path))
    export_markdown(result, str(md_path))
    export_json(result, str(json_path))

    logger.info(f"Готово! Файлы сохранены в: {output_dir}")


if __name__ == "__main__":
    main()
