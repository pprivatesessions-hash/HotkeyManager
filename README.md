# HotkeyManager

Менеджер горячих клавиш для БАЗИС-Мебельщик.

## Возможности

- **GUI** — графический интерфейс без командной строки
- **AI режим** — умное назначение клавиш по семантике
- **Сравнение версий** — анализ изменений между PDF
- **Проверка конфликтов** — база запрещённых комбинаций Windows
- **Экспорт** — Excel, Markdown, JSON

## Установка

```bash
pip install -r HotkeyManager/requirements.txt
```

Также требуется Tesseract OCR:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Установите русский и английский языки

## Запуск

### Графический интерфейс

```bash
python -m HotkeyManager --gui
```

### Командная строка

```bash
python -m HotkeyManager hotkeys.pdf
python -m HotkeyManager hotkeys.pdf --ai
python -m HotkeyManager hotkeys.pdf -o results -v
```

### Опции

- `-o, --output` — папка для выходных файлов
- `-c, --config` — путь к конфигу
- `--gui` — графический интерфейс
- `--ai` — AI генерация
- `--no-generate` — не генерировать новые клавиши
- `--no-cache` — не использовать кэш OCR
- `-v, --verbose` — подробный вывод
- `--clear-cache` — очистить кэш

## Структура

```
HotkeyManager/
├── main.py
├── config.py
├── config.yaml
├── pdf_parser.py
├── analyzer.py
├── generator.py
├── exporter_excel.py
├── exporter_md.py
├── exporter_json.py
├── models/
│   ├── command.py
│   ├── category.py
│   ├── hotkey.py
│   └── analysis.py
├── ocr/
│   ├── base.py
│   ├── tesseract_provider.py
│   ├── preprocessor.py
│   └── cache.py
├── gui/
│   └── app.py
├── ai/
│   └── engine.py
├── compare/
│   └── comparator.py
├── windows_conflicts/
│   ├── database.py
│   └── checker.py
├── tests/
│   ├── test_analyzer.py
│   ├── test_generator.py
│   ├── test_parser.py
│   ├── test_ai.py
│   ├── test_compare.py
│   └── test_windows_conflicts.py
└── cache/
```

## AI режим

Генерирует клавиши на основе семантики:

| Команда | Ключ | Результат |
|---------|------|-----------|
| Разрушить блок | D | Ctrl+Alt+D |
| Копировать | C | Ctrl+Alt+C |
| Вставить | V | Ctrl+Alt+V |
| Повернуть | R | Ctrl+Alt+R |

## Тесты

```bash
pytest HotkeyManager/tests/
```
