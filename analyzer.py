import logging
from typing import List, Dict, Set
from collections import defaultdict

from .models.command import RawCommand, Command
from .models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


def analyze_commands(raw_commands: List[RawCommand]) -> AnalysisResult:
    logger.info(f"Анализ {len(raw_commands)} команд")

    result = AnalysisResult()
    hotkey_to_commands: Dict[str, List[Command]] = defaultdict(list)

    for raw in raw_commands:
        cmd = Command(
            category=raw.category,
            name=raw.name,
            current_hotkey=raw.hotkey,
        )
        result.commands.append(cmd)

        if cmd.current_hotkey:
            hotkey_to_commands[cmd.current_hotkey].append(cmd)
            result.used_hotkeys.add(cmd.current_hotkey)

    for hotkey, cmds in hotkey_to_commands.items():
        if len(cmds) > 1:
            result.duplicates[hotkey] = cmds
            for cmd in cmds:
                cmd.status = "duplicate"
                cmd.conflict_with = ", ".join(
                    c.name for c in cmds if c != cmd
                )
            logger.warning(f"Дубликат: {hotkey} -> {[c.name for c in cmds]}")

    for cmd in result.commands:
        if cmd.status != "duplicate":
            if not cmd.current_hotkey:
                cmd.status = "needs_assignment"
                result.free.append(cmd)
            else:
                cmd.status = "assigned"
                result.assigned.append(cmd)

    logger.info(
        f"Результат: {result.assigned_count} назначено, "
        f"{result.free_count} требует назначения, "
        f"{result.duplicate_count} дубликатов"
    )

    return result


def find_conflicts(hotkey: str, used_hotkeys: Set[str]) -> bool:
    return hotkey in used_hotkeys
