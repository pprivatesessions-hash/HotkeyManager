import json
import logging
from pathlib import Path

from .models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


def export_json(result: AnalysisResult, output_path: str) -> str:
    logger.info(f"Экспорт JSON: {output_path}")

    data = {
        "summary": result.summary(),
        "hotkeys": {},
        "commands": [],
    }

    for cmd in result.commands:
        entry = {
            "category": cmd.category,
            "name": cmd.name,
            "current_hotkey": cmd.current_hotkey,
            "suggested_hotkey": cmd.suggested_hotkey,
            "status": cmd.status,
        }
        if cmd.conflict_with:
            entry["conflict_with"] = cmd.conflict_with
        data["commands"].append(entry)

        hotkey = cmd.suggested_hotkey or cmd.current_hotkey
        if hotkey:
            if hotkey not in data["hotkeys"]:
                data["hotkeys"][hotkey] = []
            data["hotkeys"][hotkey].append(
                {
                    "category": cmd.category,
                    "name": cmd.name,
                }
            )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON сохранён: {output_path}")
    return output_path
