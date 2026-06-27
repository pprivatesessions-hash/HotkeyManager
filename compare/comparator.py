import logging
from dataclasses import dataclass, field
from enum import Enum

from ..models.command import Command

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    NEW = "new"
    REMOVED = "removed"
    HOTKEY_CHANGED = "hotkey_changed"
    CATEGORY_CHANGED = "category_changed"
    RENAMED = "renamed"


@dataclass
class ChangedCommand:
    command: str
    category: str
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None


@dataclass
class ComparisonResult:
    old_commands: list[Command] = field(default_factory=list)
    new_commands: list[Command] = field(default_factory=list)
    added: list[ChangedCommand] = field(default_factory=list)
    removed: list[ChangedCommand] = field(default_factory=list)
    changed: list[ChangedCommand] = field(default_factory=list)
    unchanged: list[Command] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "old_total": len(self.old_commands),
            "new_total": len(self.new_commands),
            "added": len(self.added),
            "removed": len(self.removed),
            "changed": len(self.changed),
            "unchanged": len(self.unchanged),
        }


class HotkeyComparator:
    def compare(
        self,
        old_commands: list[Command],
        new_commands: list[Command],
    ) -> ComparisonResult:
        logger.info(f"Сравнение: {len(old_commands)}旧 → {len(new_commands)}新")

        result = ComparisonResult(
            old_commands=old_commands,
            new_commands=new_commands,
        )

        old_map = {cmd.name: cmd for cmd in old_commands}
        new_map = {cmd.name: cmd for cmd in new_commands}

        for name, new_cmd in new_map.items():
            if name not in old_map:
                result.added.append(
                    ChangedCommand(
                        command=name,
                        category=new_cmd.category,
                        change_type=ChangeType.NEW,
                        new_value=new_cmd.current_hotkey,
                    )
                )
            else:
                old_cmd = old_map[name]
                changes = self._compare_commands(old_cmd, new_cmd)
                if changes:
                    result.changed.extend(changes)
                else:
                    result.unchanged.append(new_cmd)

        for name, old_cmd in old_map.items():
            if name not in new_map:
                result.removed.append(
                    ChangedCommand(
                        command=name,
                        category=old_cmd.category,
                        change_type=ChangeType.REMOVED,
                        old_value=old_cmd.current_hotkey,
                    )
                )

        logger.info(
            f"Результат: +{len(result.added)} -{len(result.removed)} "
            f"~{len(result.changed)} ={len(result.unchanged)}"
        )

        return result

    def _compare_commands(
        self,
        old: Command,
        new: Command,
    ) -> list[ChangedCommand]:
        changes = []

        if old.current_hotkey != new.current_hotkey:
            changes.append(
                ChangedCommand(
                    command=new.name,
                    category=new.category,
                    change_type=ChangeType.HOTKEY_CHANGED,
                    old_value=old.current_hotkey,
                    new_value=new.current_hotkey,
                )
            )

        if old.category != new.category:
            changes.append(
                ChangedCommand(
                    command=new.name,
                    category=new.category,
                    change_type=ChangeType.CATEGORY_CHANGED,
                    old_value=old.category,
                    new_value=new.category,
                )
            )

        return changes

    def export_markdown(self, result: ComparisonResult, output_path: str) -> str:
        lines = []
        lines.append("# Сравнение версий БАЗИС-Мебельщик")
        lines.append("")

        summary = result.summary
        lines.append("## Итого")
        lines.append(f"- Было команд: {summary['old_total']}")
        lines.append(f"- Стало команд: {summary['new_total']}")
        lines.append(f"- Добавлено: {summary['added']}")
        lines.append(f"- Удалено: {summary['removed']}")
        lines.append(f"- Изменено: {summary['changed']}")
        lines.append(f"- Без изменений: {summary['unchanged']}")
        lines.append("")

        if result.added:
            lines.append("## Добавлены новые команды")
            lines.append("")
            for cmd in result.added:
                hk = cmd.new_value or "—"
                lines.append(f"- **{cmd.command}** ({cmd.category}) → {hk}")
            lines.append("")

        if result.removed:
            lines.append("## Удалены команды")
            lines.append("")
            for cmd in result.removed:
                hk = cmd.old_value or "—"
                lines.append(f"- **{cmd.command}** ({cmd.category}) → {hk}")
            lines.append("")

        if result.changed:
            lines.append("## Изменены комбинации")
            lines.append("")
            lines.append("| Команда | Было | Стало |")
            lines.append("|---------|------|-------|")
            for cmd in result.changed:
                old = cmd.old_value or "—"
                new = cmd.new_value or "—"
                lines.append(f"| {cmd.command} | {old} | {new} |")
            lines.append("")

        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Сравнение экспортировано: {output_path}")
        return output_path
