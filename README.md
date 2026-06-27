# 🔥 HotkeyManager

Менеджер горячих клавиш для [БАЗИС-Мебельщик](https://bazis-center.ru/).

Автоматически распознаёт горячие клавиши из PDF, анализирует конфликты и генерирует оптимальную раскладку.

## 🎯 Возможности

| Функция | Описание |
|---------|----------|
| 📄 **PDF парсер** | Извлечение команд из PDF с OCR |
| 🖼️ **GUI** | Удобный графический интерфейс |
| 🤖 **AI режим** | Умное назначение по семантике |
| 🔄 **Сравнение** | Анализ изменений между версиями |
| ⚠️ **Конфликты** | Проверка запрещённых комбинаций Windows |
| 📊 **Экспорт** | Excel, Markdown, JSON |

## 📦 Установка

### 1. Клонируй репозиторий

```bash
git clone https://github.com/pprivatesessions-hash/HotkeyManager.git
cd HotkeyManager
```

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Установи Tesseract OCR

Скачай и установи [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).

При установке выбери:
- ✅ Русский язык
- ✅ Английский язык

## 🚀 Запуск

### Графический интерфейс

```bash
python -m HotkeyManager --gui
```

![GUI Preview](https://via.placeholder.com/800x400?text=HotkeyManager+GUI)

### Командная строка

```bash
# Базовый запуск
python -m HotkeyManager hotkeys.pdf

# AI генерация
python -m HotkeyManager hotkeys.pdf --ai

# С указанием папки вывода
python -m HotkeyManager hotkeys.pdf -o results

# Подробный вывод
python -m HotkeyManager hotkeys.pdf -v
```

### Все опции

| Опция | Описание |
|-------|----------|
| `-o, --output` | Папка для выходных файлов (по умолчанию: `output`) |
| `-c, --config` | Путь к файлу конфигурации |
| `--gui` | Запустить графический интерфейс |
| `--ai` | Использовать AI генерацию |
| `--no-generate` | Не генерировать новые клавиши |
| `--no-cache` | Отключить кэширование OCR |
| `-v, --verbose` | Подробный вывод |
| `--clear-cache` | Очистить кэш OCR |

## 🤖 AI Режим

Генерирует клавиши на основе семантического анализа:

| Команда | Анализ | Ключ | Результат |
|---------|--------|------|-----------|
| Разрушить блок | Ключевое слово: разрушить | D | `Ctrl+Alt+D` |
| Копировать | Ключевое слово: копировать | C | `Ctrl+Alt+C` |
| Вставить | Ключевое слово: вставить | V | `Ctrl+Alt+V` |
| Повернуть | Ключевое слово: повернуть | R | `Ctrl+Alt+R` |
| Линия | Ключевое слово: линия | L | `Ctrl+Alt+L` |
| Материал | Ключевое слово: материал | M | `Ctrl+Alt+M` |

### Приоритеты AI

1. **Семантика** — ключевые слова команды
2. **Категория** — вес категории (Блоки > Правка > Вид)
3. **Близость** — соседние клавиши на клавиатуре
4. **Конфликты** — проверка Windows ограничений

## ⚠️ Проверка конфликтов

База данных включает:

| Уровень | Описание |
|---------|----------|
| 🔴 **SYSTEM** | Системные комбинации Windows |
| 🔴 **FORBIDDEN** | Стандартные сочетания (Ctrl+C, Ctrl+V) |
| 🟡 **RISKY** | Возможные конфликты с приложениями |
| 🟢 **SAFE** | Свободные комбинации |

### Запрещённые комбинации

```
Ctrl+Alt+Delete    — Системная
Ctrl+C             — Копировать
Ctrl+V             — Вставить
Ctrl+Z             — Отменить
F1                 — Справка
...
```

## 🔄 Сравнение версий

Сравнивает горячие клавиши между разными версиями БАЗИС:

```bash
# Через GUI
# Меню → Инструменты → Сравнить версии

# Результат
## Добавлены новые команды
- **Новая команда** (Категория) → Ctrl+Alt+N

## Изменены комбинации
| Команда | Было | Стало |
|---------|------|-------|
| Масштаб | Ctrl+Z | Ctrl+Alt+Z |
```

## 📁 Структура проекта

```
HotkeyManager/
├── main.py                    # Точка входа
├── config.py                  # Загрузка конфигурации
├── config.yaml               # Конфигурация по умолчанию
├── pdf_parser.py             # Парсинг PDF
├── analyzer.py               # Анализ команд
├── generator.py              # Генерация клавиш
│
├── models/                   # Модели данных
│   ├── command.py            # Command, RawCommand
│   ├── category.py           # Category
│   ├── hotkey.py             # Hotkey
│   └── analysis.py           # AnalysisResult
│
├── ocr/                      # OCR модуль
│   ├── base.py               # Интерфейс OCRProvider
│   ├── tesseract_provider.py # Tesseract реализация
│   ├── preprocessor.py       # Предобработка изображений
│   └── cache.py              # Кэширование результатов
│
├── gui/                      # Графический интерфейс
│   └── app.py                # Tkinter приложение
│
├── ai/                       # AI генерация
│   └── engine.py             # Семантический анализ
│
├── compare/                  # Сравнение версий
│   └── comparator.py         # Сравнительный анализ
│
├── windows_conflicts/        # Конфликты Windows
│   ├── database.py           # База запрещённых комбинаций
│   └── checker.py            # Проверка конфликтов
│
├── exporter_excel.py         # Экспорт в Excel
├── exporter_md.py            # Экспорт в Markdown
├── exporter_json.py          # Экспорт в JSON
│
├── tests/                    # Тесты (42 теста)
│   ├── test_analyzer.py
│   ├── test_generator.py
│   ├── test_parser.py
│   ├── test_ai.py
│   ├── test_compare.py
│   └── test_windows_conflicts.py
│
├── requirements.txt          # Зависимости
└── README.md                 # Этот файл
```

## ⚙️ Конфигурация

Файл `config.yaml`:

```yaml
hotkey_manager:
  prefix_combos:
    - "Ctrl+Alt"
    - "Ctrl+Shift+Alt"

  strategy:
    use_semantic: true        # Семантический анализ
    use_category_weight: true # Вес категорий
    prefer_key_proximity: true # Близость клавиш

  category_weights:
    Блоки: 1.0
    Модель: 0.95
    Правка: 0.9
    Рисование: 0.85
    Вид: 0.8

  semantic_hints:
    Destroy: "D"
    Copy: "C"
    Paste: "V"
    # ... больше подсказок
```

## 🧪 Тесты

```bash
# Запуск всех тестов
pytest HotkeyManager/tests/ -v

# Результат
42 passed in 1.04s
```

### Покрытие

| Модуль | Тесты |
|--------|-------|
| analyzer | 5 |
| generator | 6 |
| parser | 8 |
| ai | 6 |
| compare | 6 |
| windows_conflicts | 9 |
| **Итого** | **42** |

## 📊 Экспорт

### Excel (`Hotkeys.xlsx`)

- Цветовая кодировка статусов
- Фильтры по категориям
- Статусы: ✅ Назначена, 🔄 Требует назначения, ⚠️ Дубликат

### Markdown (`Hotkeys.md`)

```markdown
# HotkeyManager — Горячие клавиши БАЗИС-Мебельщик

Всего команд: 150
Назначено: 80
Требует назначения: 65
Дубликатов: 5
```

### JSON (`hotkeys.json`)

```json
{
  "summary": {
    "total": 150,
    "assigned": 80,
    "free": 65,
    "duplicates": 5
  },
  "commands": [...]
}
```

## 🛠️ Технологии

- **Python 3.11+**
- **PyMuPDF** — чтение PDF
- **Tesseract OCR** — распознавание текста
- **Pillow** — обработка изображений
- **openpyxl** — экспорт в Excel
- **PyYAML** — конфигурация
- **tkinter** — GUI
- **pytest** — тестирование

## 📝 Лицензия

MIT License

## 👨‍💻 Автор

[@pprivatesessions-hash](https://github.com/pprivatesessions-hash)

---

⭐ Если проект полезен, поставь звезду!
