import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..ai.engine import AIEngine
from ..analyzer import analyze_commands
from ..config import load_config
from ..exporter_excel import export_excel
from ..exporter_json import export_json
from ..exporter_md import export_markdown
from ..generator import generate_hotkeys
from ..models.analysis import AnalysisResult
from ..models.command import Command
from ..pdf_parser import parse_pdf, _extract_commands
from ..ocr.tesseract_provider import TesseractProvider
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)


class HotkeyManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HotkeyManager — БАЗИС-Мебельщик")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.config = load_config()
        self.result: AnalysisResult | None = None
        self.checker = WindowsConflictChecker()
        self._collapsed_categories: set[str] = set()
        self._manual_commands: list[dict] = []
        self._generated = False

        self._setup_ui()

    def _setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Импорт из PDF", command=self._import_pdf)
        file_menu.add_command(label="Импорт из изображения", command=self._import_image)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт Excel", command=self._export_excel)
        file_menu.add_command(label="Экспорт Markdown", command=self._export_md)
        file_menu.add_command(label="Экспорт JSON", command=self._export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Проверить конфликты", command=self._check_conflicts)

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self._status_label = ttk.Label(top_frame, text="Добавьте команды в таблицу")
        self._status_label.pack(side=tk.LEFT)

        self._btn_add_row = ttk.Button(top_frame, text="+ Добавить строку", command=self._add_empty_row)
        self._btn_add_row.pack(side=tk.RIGHT, padx=5)

        self._btn_generate = ttk.Button(top_frame, text="⚡ Генерировать", command=self._generate, state=tk.DISABLED)
        self._btn_generate.pack(side=tk.RIGHT, padx=5)

        self._btn_save = ttk.Button(top_frame, text="💾 Сохранить", command=self._save, state=tk.DISABLED)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("category", "name", "current", "suggested", "status")
        self._tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended"
        )

        self._tree.heading("category", text="Категория", command=self._sort_by_category)
        self._tree.heading("name", text="Команда")
        self._tree.heading("current", text="Текущая клавиша")
        self._tree.heading("suggested", text="Новая клавиша")
        self._tree.heading("status", text="Статус")

        self._tree.column("category", width=140)
        self._tree.column("name", width=280)
        self._tree.column("current", width=140)
        self._tree.column("suggested", width=140)
        self._tree.column("status", width=160)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<Double-1>", self._on_tree_click)
        self._tree.bind("<Button-3>", self._on_right_click)

        self._tree.tag_configure("category_header", background="#4472C4", foreground="white", font=("Arial", 10, "bold"))
        self._tree.tag_configure("category_collapsed", background="#5B9BD5", foreground="white", font=("Arial", 10, "bold"))
        self._tree.tag_configure("assigned", background="#C6EFCE")
        self._tree.tag_configure("needs_assignment", background="#FFEB9C")
        self._tree.tag_configure("duplicate", background="#FFC7CE")
        self._tree.tag_configure("editable", background="#E8F4FD")

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self._stats_label = ttk.Label(bottom_frame, text="Команд: 0")
        self._stats_label.pack(side=tk.LEFT)

        self._context_menu = tk.Menu(self.root, tearoff=0)
        self._context_menu.add_command(label="Редактировать", command=self._edit_selected)
        self._context_menu.add_command(label="Удалить", command=self._delete_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Импорт из PDF в эту строку", command=self._import_to_selected)
        self._context_menu.add_command(label="Импорт из изображения в эту строку", command=self._import_image_to_selected)

    def _add_empty_row(self):
        self._manual_commands.append({
            "category": "",
            "name": "",
            "current": "",
            "suggested": "",
            "status": "editable",
        })
        self._generated = False
        self._btn_generate.config(state=tk.NORMAL)
        self._btn_save.config(state=tk.DISABLED)
        self._update_tree()

    def _on_tree_click(self, event):
        item = self._tree.selection()
        if not item:
            return

        tags = self._tree.item(item[0], "tags")
        values = self._tree.item(item[0], "values")

        if "category_header" in tags or "category_collapsed" in tags:
            cat_name = values[0].replace("📁 ", "").replace("▸ ", "")
            if cat_name in self._collapsed_categories:
                self._collapsed_categories.discard(cat_name)
            else:
                self._collapsed_categories.add(cat_name)
            self._update_tree()
        elif "editable" in tags or "assigned" in tags or "needs_assignment" in tags:
            self._edit_row_by_item(item[0])

    def _on_right_click(self, event):
        item = self._tree.identify_row(event.y)
        if item:
            self._tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _edit_selected(self):
        item = self._tree.selection()
        if item:
            self._edit_row_by_item(item[0])

    def _delete_selected(self):
        item = self._tree.selection()
        if not item:
            return

        values = self._tree.item(item[0], "values")
        tags = self._tree.item(item[0], "tags")

        if "category_header" in tags or "category_collapsed" in tags:
            return

        row_idx = self._tree.index(item[0])
        if 0 <= row_idx < len(self._manual_commands):
            del self._manual_commands[row_idx]
            self._update_tree()
            self._check_generate_button()

    def _edit_row_by_item(self, item_id):
        values = self._tree.item(item_id, "values")
        row_idx = self._tree.index(item_id)

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактировать команду")
        edit_window.geometry("400x200")
        edit_window.transient(self.root)
        edit_window.grab_set()

        fields = [
            ("Категория:", 0),
            ("Команда:", 1),
            ("Текущая клавиша:", 2),
        ]

        entries = {}
        for label, idx in fields:
            frame = ttk.Frame(edit_window, padding=5)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=label, width=18).pack(side=tk.LEFT)
            entry = ttk.Entry(frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entry.insert(0, values[idx] if values[idx] != "—" else "")
            entries[idx] = entry

        def save():
            new_values = [entries[i].get() for i in range(3)]
            if row_idx < len(self._manual_commands):
                self._manual_commands[row_idx]["category"] = new_values[0]
                self._manual_commands[row_idx]["name"] = new_values[1]
                self._manual_commands[row_idx]["current"] = new_values[2]
            self._update_tree()
            self._check_generate_button()
            edit_window.destroy()

        btn_frame = ttk.Frame(edit_window, padding=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)

    def _import_to_selected(self):
        item = self._tree.selection()
        if not item:
            return

        row_idx = self._tree.index(item[0])
        path = filedialog.askopenfilename(
            title="Выберите PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return

        try:
            raw_commands = parse_pdf(path, config=self.config)
            if raw_commands:
                cmd = raw_commands[0]
                if row_idx < len(self._manual_commands):
                    self._manual_commands[row_idx]["category"] = cmd.category
                    self._manual_commands[row_idx]["name"] = cmd.name
                    self._manual_commands[row_idx]["current"] = cmd.hotkey or ""
                    self._update_tree()
                    self._check_generate_button()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _import_image_to_selected(self):
        item = self._tree.selection()
        if not item:
            return

        row_idx = self._tree.index(item[0])
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            ocr = TesseractProvider(
                languages=self.config.ocr.languages,
                dpi=self.config.ocr.dpi,
                preprocess=self.config.ocr.preprocess,
            )
            from PIL import Image
            img = Image.open(path)
            text = ocr.recognize(img)
            raw_commands = _extract_commands([text])

            if raw_commands:
                cmd = raw_commands[0]
                if row_idx < len(self._manual_commands):
                    self._manual_commands[row_idx]["category"] = cmd.category
                    self._manual_commands[row_idx]["name"] = cmd.name
                    self._manual_commands[row_idx]["current"] = cmd.hotkey or ""
                    self._update_tree()
                    self._check_generate_button()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _import_pdf(self):
        path = filedialog.askopenfilename(
            title="Выберите PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return

        try:
            raw_commands = parse_pdf(path, config=self.config)
            for cmd in raw_commands:
                self._manual_commands.append({
                    "category": cmd.category,
                    "name": cmd.name,
                    "current": cmd.hotkey or "",
                    "suggested": "",
                    "status": "editable",
                })
            self._generated = False
            self._btn_generate.config(state=tk.NORMAL)
            self._btn_save.config(state=tk.DISABLED)
            self._update_tree()
            self._status_label.config(text=f"Импортировано: {len(raw_commands)} команд")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _import_image(self):
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            ocr = TesseractProvider(
                languages=self.config.ocr.languages,
                dpi=self.config.ocr.dpi,
                preprocess=self.config.ocr.preprocess,
            )
            from PIL import Image
            img = Image.open(path)
            text = ocr.recognize(img)
            raw_commands = _extract_commands([text])

            for cmd in raw_commands:
                self._manual_commands.append({
                    "category": cmd.category,
                    "name": cmd.name,
                    "current": cmd.hotkey or "",
                    "suggested": "",
                    "status": "editable",
                })
            self._generated = False
            self._btn_generate.config(state=tk.NORMAL)
            self._btn_save.config(state=tk.DISABLED)
            self._update_tree()
            self._status_label.config(text=f"Импортировано: {len(raw_commands)} команд из изображения")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _check_generate_button(self):
        has_data = any(c["name"] for c in self._manual_commands)
        self._btn_generate.config(state=tk.NORMAL if has_data else tk.DISABLED)

    def _generate(self):
        if not self._manual_commands:
            messagebox.showwarning("Внимание", "Нет данных для генерации")
            return

        raw_commands = []
        for c in self._manual_commands:
            if c["name"]:
                raw_commands.append(Command(
                    category=c["category"] or "Без категории",
                    name=c["name"],
                    current_hotkey=c["current"] or None,
                ))

        self.result = AnalysisResult(commands=raw_commands)
        self.result = generate_hotkeys(self.result, self.config)

        for i, cmd in enumerate(self.result.commands):
            if i < len(self._manual_commands):
                self._manual_commands[i]["suggested"] = cmd.suggested_hotkey or ""
                self._manual_commands[i]["status"] = cmd.status

        self._generated = True
        self._btn_save.config(state=tk.NORMAL)
        self._update_tree()
        self._status_label.config(text="Генерация завершена")

    def _save(self):
        if not self.result:
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("Markdown files", "*.md"),
                ("JSON files", "*.json"),
            ],
            initialfile="Hotkeys",
        )
        if not path:
            return

        ext = Path(path).suffix.lower()
        try:
            if ext == ".xlsx":
                export_excel(self.result, path)
            elif ext == ".md":
                export_markdown(self.result, path)
            elif ext == ".json":
                export_json(self.result, path)
            else:
                export_excel(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")

    def _export_excel(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
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
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
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
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
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

    def _check_conflicts(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
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

    def _sort_by_category(self):
        self._manual_commands.sort(key=lambda c: c["category"])
        self._update_tree()

    def _update_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        if not self._manual_commands:
            return

        if self._generated and self.result:
            self._update_tree_generated()
        else:
            self._update_tree_editable()

        self._stats_label.config(text=f"Команд: {len(self._manual_commands)}")

    def _update_tree_editable(self):
        for i, cmd in enumerate(self._manual_commands):
            current = cmd["current"] or "—"
            suggested = cmd["suggested"] or "—"

            status_map = {
                "editable": "✏️ Редактируется",
                "assigned": "✅ Назначена",
                "needs_assignment": "🔄 Требует назначения",
                "duplicate": "⚠️ Дубликат",
            }
            status = status_map.get(cmd["status"], cmd["status"])
            tag = "editable" if cmd["status"] == "editable" else cmd["status"]

            self._tree.insert(
                "",
                tk.END,
                values=(cmd["category"], cmd["name"], current, suggested, status),
                tags=(tag,),
            )

    def _update_tree_generated(self):
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

    def run(self):
        self.root.mainloop()
