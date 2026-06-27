import logging
from pathlib import Path

from .models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


def export_markdown(result: AnalysisResult, output_path: str) -> str:
    logger.info(f"Экспорт Markdown: {output_path}")

    lines = []
    lines.append("# HotkeyManager — Горячие клавиши БАЗИС-Мебельщик")
    lines.append("")
    lines.append(f"Всего команд: {result.total}")
    lines.append(f"Назначено: {result.assigned_count}")
    lines.append(f"Требует назначения: {result.free_count}")
    lines.append(f"Дубликатов: {result.duplicate_count}")
    lines.append("")

    lines.append("## Статистика по категориям")
    lines.append("")
    categories = {}
    for cmd in result.commands:
        if cmd.category not in categories:
            categories[cmd.category] = {"total": 0, "assigned": 0, "free": 0}
        categories[cmd.category]["total"] += 1
        if cmd.current_hotkey:
            categories[cmd.category]["assigned"] += 1
        else:
            categories[cmd.category]["free"] += 1

    lines.append("| Категория | Всего | Назначено | Свободно |")
    lines.append("|-----------|-------|-----------|----------|")
    for cat, stats in sorted(categories.items()):
        lines.append(f"| {cat} | {stats['total']} | {stats['assigned']} | {stats['free']} |")
    lines.append("")

    lines.append("## Дубликаты")
    lines.append("")
    if result.duplicates:
        for hotkey, cmds in result.duplicates.items():
            lines.append(f"### {hotkey}")
            for cmd in cmds:
                lines.append(f"- {cmd.category} → {cmd.name}")
        lines.append("")
    else:
        lines.append("Дубликатов нет.")
        lines.append("")

    lines.append("## Полная таблица")
    lines.append("")
    lines.append("| Категория | Команда | Текущая | Новая | Статус |")
    lines.append("|-----------|---------|---------|-------|--------|")

    for cmd in result.commands:
        current = cmd.current_hotkey or "—"
        new = cmd.suggested_hotkey or "—"
        status_map = {
            "assigned": "✅",
            "needs_assignment": "🔄",
            "duplicate": "⚠️",
        }
        status = status_map.get(cmd.status, "")
        lines.append(f"| {cmd.category} | {cmd.name} | {current} | {new} | {status} |")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Markdown сохранён: {output_path}")
    return output_path
