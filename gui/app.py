import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..ai.engine import AIEngine
from ..analyzer import analyze_commands
from ..compare.comparator import HotkeyComparator
from ..config import load_config
from ..exporter_excel import export_excel
from ..exporter_json import export_json
from ..exporter_md import export_markdown
from ..generator import generate_hotkeys
from ..models.analysis import AnalysisResult
from ..pdf_parser import parse_pdf
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)


class HotkeyManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HotkeyManager — БАЗИС-Мебельщик")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        self.config = load_config()
        self.result: AnalysisResult | None = None
        self.checker = WindowsConflictChecker()
        self._collapsed_categories: set[str] = set()

        self._setup_ui()

    def _setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть PDF", command=self._open_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт Excel", command=self._export_excel)
        file_menu.add_command(label="Экспорт Markdown", command=self._export_md)
        file_menu.add_command(label="Экспорт JSON", command=self._export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Сравнить версии", command=self._compare_versions)
        tools_menu.add_command(label="Проверить конфликты", command=self._check_conflicts)

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self._pdf_label = ttk.Label(top_frame, text="PDF не загружен")
        self._pdf_label.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_frame, text="Загрузить PDF", command=self._open_pdf).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(top_frame, text="Генерировать", command=self._generate).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(top_frame, text="AI режим", command=self._generate_ai).pack(side=tk.LEFT, padx=5)

        self._status_label = ttk.Label(top_frame, text="")
        self._status_label.pack(side=tk.RIGHT)

        columns = ("category", "name", "current", "suggested", "status")
        self._tree = ttk.Treeview(
            main_frame, columns=columns, show="headings", selectmode="extended"
        )

        self._tree.heading("category", text="Категория")
        self._tree.heading("name", text="Команда")
        self._tree.heading("current", text="Текущая клавиша")
        self._tree.heading("suggested", text="Новая клавиша")
        self._tree.heading("status", text="Статус")

        self._tree.column("category", width=120)
        self._tree.column("name", width=250)
        self._tree.column("current", width=120)
        self._tree.column("suggested", width=120)
        self._tree.column("status", width=150)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<Double-1>", self._on_tree_click)

        self._tree.tag_configure("category_header", background="#4472C4", foreground="white", font=("Arial", 10, "bold"))
        self._tree.tag_configure("category_collapsed", background="#5B9BD5", foreground="white", font=("Arial", 10, "bold"))
        self._tree.tag_configure("assigned", background="#C6EFCE")
        self._tree.tag_configure("needs_assignment", background="#FFEB9C")
        self._tree.tag_configure("duplicate", background="#FFC7CE")
        self._tree.tag_configure("safe", background="#C6EFCE")
        self._tree.tag_configure("risky", background="#FFEB9C")
        self._tree.tag_configure("forbidden", background="#FFC7CE")

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self._stats_label = ttk.Label(bottom_frame, text="Команд: 0")
        self._stats_label.pack(side=tk.LEFT)

    def _open_pdf(self):
        path = filedialog.askopenfilename(
            title="Выберите PDF файл",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not path:
            return

        self._pdf_label.config(text=f"PDF: {Path(path).name}")
        self._status_label.config(text="Загрузка...")
        self.root.update()

        try:
            raw_commands = parse_pdf(path, config=self.config)
            self.result = analyze_commands(raw_commands)
            self._update_tree()
            self._status_label.config(text=f"Загружено: {len(self.result.commands)} команд")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить PDF:\n{e}")
            self._status_label.config(text="Ошибка загрузки")

    def _generate(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала загрузите PDF")
            return

        self._status_label.config(text="Генерация...")
        self.root.update()

        self.result = generate_hotkeys(self.result, self.config)
        self._update_tree()
        self._status_label.config(text="Генерация завершена")

    def _generate_ai(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала загрузите PDF")
            return

        self._status_label.config(text="AI генерация...")
        self.root.update()

        ai_engine = AIEngine(self.config)
        self.result = ai_engine.generate(self.result)
        self._update_tree()
        self._status_label.config(text="AI генерация завершена")

    def _on_tree_click(self, event):
        item = self._tree.selection()
        if not item:
            return

        values = self._tree.item(item[0], "values")
        tags = self._tree.item(item[0], "tags")

        if "category_header" in tags or "category_collapsed" in tags:
            cat_name = values[0].replace("📁 ", "").replace("▸ ", "")
            if cat_name in self._collapsed_categories:
                self._collapsed_categories.discard(cat_name)
            else:
                self._collapsed_categories.add(cat_name)
            self._update_tree()

    def _update_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        if not self.result:
            return

        categories: dict[str, list] = {}
        for cmd in self.result.commands:
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)

        for cat_name, cmds in categories.items():
            is_collapsed = cat_name in self._collapsed_categories
            icon = "▸" if is_collapsed else "📁"
            tag = "category_collapsed" if is_collapsed else "category_header"

            self._tree.insert(
                "",
                tk.END,
                values=(f"{icon} {cat_name}", "", "", "", f"{len(cmds)} команд"),
                tags=(tag,),
            )

            if not is_collapsed:
                for cmd in cmds:
                    current = cmd.current_hotkey or "—"
                    suggested = cmd.suggested_hotkey or "—"

                    status_map = {
                        "assigned": "✅ Назначена",
                        "needs_assignment": "🔄 Требует назначения",
                        "duplicate": "⚠️ Дубликат",
                    }
                    status = status_map.get(cmd.status, cmd.status)
                    tag = cmd.status

                    self._tree.insert(
                        "",
                        tk.END,
                        values=("", cmd.name, current, suggested, status),
                        tags=(tag,),
                    )

        summary = self.result.summary()
        self._stats_label.config(
            text=f"Команд: {summary['total']} | "
            f"Назначено: {summary['assigned']} | "
            f"Свободно: {summary['free']} | "
            f"Дубликатов: {summary['duplicates']}"
        )

    def _export_excel(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="Hotkeys.xlsx",
        )
        if path:
            export_excel(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def _export_md(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить Markdown",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md")],
            initialfile="Hotkeys.md",
        )
        if path:
            export_markdown(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def _export_json(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Нет данных для экспорта")
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="hotkeys.json",
        )
        if path:
            export_json(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def _compare_versions(self):
        old_path = filedialog.askopenfilename(
            title="Выберите старый PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not old_path:
            return

        new_path = filedialog.askopenfilename(
            title="Выберите новый PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not new_path:
            return

        self._status_label.config(text="Сравнение версий...")
        self.root.update()

        try:
            old_raw = parse_pdf(old_path, config=self.config)
            old_commands = analyze_commands(old_raw)

            new_raw = parse_pdf(new_path, config=self.config)
            new_commands = analyze_commands(new_raw)

            comparator = HotkeyComparator()
            result = comparator.compare(old_commands.commands, new_commands.commands)

            save_path = filedialog.asksaveasfilename(
                title="Сохранить результат сравнения",
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md")],
                initialfile="comparison.md",
            )
            if save_path:
                comparator.export_markdown(result, save_path)
                messagebox.showinfo("Готово", f"Сравнение сохранено: {save_path}")

            self._status_label.config(text="Сравнение завершено")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сравнения:\n{e}")

    def _check_conflicts(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала загрузите данные")
            return

        conflicts = []
        for cmd in self.result.commands:
            if cmd.suggested_hotkey:
                check = self.checker.check(cmd.suggested_hotkey)
                if not check.is_available:
                    conflicts.append(f"{cmd.name}: {cmd.suggested_hotkey} — {check.reason}")

        if conflicts:
            msg = "Найдены конфликты:\n\n" + "\n".join(conflicts[:20])
            if len(conflicts) > 20:
                msg += f"\n... и ещё {len(conflicts) - 20}"
            messagebox.showwarning("Конфликты", msg)
        else:
            messagebox.showinfo("Проверка", "Конфликтов не найдено")

    def run(self):
        self.root.mainloop()
