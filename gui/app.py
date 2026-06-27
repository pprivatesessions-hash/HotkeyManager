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
from ..models.command import Command, RawCommand
from ..pdf_parser import parse_pdf, _extract_commands
from ..ocr.tesseract_provider import TesseractProvider
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)


class CategoryBlock:
    def __init__(self, name: str):
        self.name = name
        self.commands: list[RawCommand] = []
        self.collapsed = False


class HotkeyManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HotkeyManager — БАЗИС-Мебельщик")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.config = load_config()
        self.result: AnalysisResult | None = None
        self.checker = WindowsConflictChecker()
        self._categories: list[CategoryBlock] = []
        self._generated = False

        self._setup_ui()

    def _setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
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

        self._status_label = ttk.Label(top_frame, text="Нажмите на заголовок столбца для добавления данных")
        self._status_label.pack(side=tk.LEFT)

        self._btn_generate = ttk.Button(
            top_frame, text="⚡ Генерировать", command=self._generate, state=tk.DISABLED
        )
        self._btn_generate.pack(side=tk.RIGHT, padx=5)

        self._btn_save = ttk.Button(
            top_frame, text="💾 Сохранить", command=self._save, state=tk.DISABLED
        )
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self._canvas.yview)

        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._table_frame = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._table_frame, anchor="nw")

        self._table_frame.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._header_frame = ttk.Frame(self._table_frame)
        self._header_frame.pack(fill=tk.X)

        headers = [("category", "Категория", 200), ("commands", "Команда", 350), ("hotkeys", "Горячие клавиши", 200)]
        for col_id, text, width in headers:
            btn = tk.Button(
                self._header_frame,
                text=text,
                font=("Arial", 10, "bold"),
                bg="#4472C4",
                fg="white",
                relief=tk.RAISED,
                width=width // 10,
                command=lambda c=col_id: self._on_header_click(c),
            )
            btn.pack(side=tk.LEFT, padx=1, pady=2)

        self._data_frame = ttk.Frame(self._table_frame)
        self._data_frame.pack(fill=tk.BOTH, expand=True)

        self._bottom_frame = ttk.Frame(main_frame)
        self._bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self._stats_label = ttk.Label(self._bottom_frame, text="Категорий: 0 | Команд: 0")
        self._stats_label.pack(side=tk.LEFT)

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_header_click(self, col_id: str):
        if col_id == "category":
            self._add_category_from_file()
        elif col_id == "commands":
            self._add_commands_to_category()
        elif col_id == "hotkeys":
            self._status_label.config(text="Клавиши назначаются автоматически при генерации")

    def _add_category_from_file(self):
        path = filedialog.askopenfilename(
            title="Выберите файл для извлечения категорий",
            filetypes=[
                ("Все поддерживаемые", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ],
        )
        if not path:
            return

        try:
            raw_commands = self._parse_file(path)
            found_categories: dict[str, list[RawCommand]] = {}
            for cmd in raw_commands:
                cat = cmd.category or "Без категории"
                if cat not in found_categories:
                    found_categories[cat] = []
                found_categories[cat].append(cmd)

            existing_names = {c.name for c in self._categories}
            added = 0
            for cat_name, cmds in found_categories.items():
                if cat_name not in existing_names:
                    block = CategoryBlock(cat_name)
                    block.commands = cmds
                    self._categories.append(block)
                    added += 1
                else:
                    for block in self._categories:
                        if block.name == cat_name:
                            existing_cmd_names = {c.name for c in block.commands}
                            for cmd in cmds:
                                if cmd.name not in existing_cmd_names:
                                    block.commands.append(cmd)
                                    existing_cmd_names.add(cmd.name)

            self._generated = False
            self._btn_generate.config(state=tk.NORMAL if self._categories else tk.DISABLED)
            self._btn_save.config(state=tk.DISABLED)
            self._rebuild_table()
            self._status_label.config(text=f"Добавлено категорий: {added}, всего команд: {sum(len(c.commands) for c in self._categories)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _add_commands_to_category(self):
        if not self._categories:
            messagebox.showinfo("Информация", "Сначала добавьте категории через заголовок 'Категория'")
            return

        select_window = tk.Toplevel(self.root)
        select_window.title("Выберите категорию")
        select_window.geometry("350x250")
        select_window.transient(self.root)
        select_window.grab_set()

        ttk.Label(select_window, text="Выберите категорию для добавления команд:", padding=10).pack()

        listbox = tk.Listbox(select_window, font=("Arial", 11))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for cat in self._categories:
            listbox.insert(tk.END, f"{cat.name} ({len(cat.commands)} команд)")

        def on_select():
            selection = listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            cat_name = self._categories[idx].name
            select_window.destroy()
            self._import_commands_to(cat_name)

        ttk.Button(select_window, text="Выбрать", command=on_select).pack(pady=10)

    def _import_commands_to(self, category_name: str):
        path = filedialog.askopenfilename(
            title=f"Выберите файл для категории: {category_name}",
            filetypes=[
                ("Все поддерживаемые", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ],
        )
        if not path:
            return

        try:
            raw_commands = self._parse_file(path)

            for block in self._categories:
                if block.name == category_name:
                    existing_names = {c.name for c in block.commands}
                    added = 0
                    for cmd in raw_commands:
                        if cmd.name not in existing_names:
                            block.commands.append(cmd)
                            existing_names.add(cmd.name)
                            added += 1
                    self._status_label.config(
                        text=f"В '{category_name}' добавлено {added} команд"
                    )
                    break

            self._generated = False
            self._btn_generate.config(state=tk.NORMAL)
            self._btn_save.config(state=tk.DISABLED)
            self._rebuild_table()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта:\n{e}")

    def _parse_file(self, path: str) -> list[RawCommand]:
        ext = Path(path).suffix.lower()

        if ext == ".pdf":
            return parse_pdf(path, config=self.config)
        elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            ocr = TesseractProvider(
                languages=self.config.ocr.languages,
                dpi=self.config.ocr.dpi,
                preprocess=self.config.ocr.preprocess,
            )
            from PIL import Image
            img = Image.open(path)
            text = ocr.recognize(img)
            return _extract_commands([text])
        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")

    def _toggle_category(self, cat_name: str):
        for block in self._categories:
            if block.name == cat_name:
                block.collapsed = not block.collapsed
                break
        self._rebuild_table()

    def _generate(self):
        if not self._categories:
            return

        all_commands = []
        for block in self._categories:
            for cmd in block.commands:
                all_commands.append(Command(
                    category=block.name,
                    name=cmd.name,
                    current_hotkey=cmd.hotkey,
                ))

        self.result = AnalysisResult(commands=all_commands)
        self.result = generate_hotkeys(self.result, self.config)

        hotkey_map: dict[str, str] = {}
        for cmd in self.result.commands:
            if cmd.suggested_hotkey:
                hotkey_map[cmd.name] = cmd.suggested_hotkey
            elif cmd.current_hotkey:
                hotkey_map[cmd.name] = cmd.current_hotkey

        for block in self._categories:
            for cmd in block.commands:
                if cmd.name in hotkey_map:
                    cmd.hotkey = hotkey_map[cmd.name]

        self._generated = True
        self._btn_save.config(state=tk.NORMAL)
        self._rebuild_table()
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

    def _rebuild_table(self):
        for widget in self._data_frame.winfo_children():
            widget.destroy()

        if not self._categories:
            ttk.Label(self._data_frame, text="Нет данных. Нажмите на заголовок столбца для добавления.", font=("Arial", 11)).pack(pady=50)
            self._stats_label.config(text="Категорий: 0 | Команд: 0")
            return

        total_commands = 0
        for block in self._categories:
            cat_frame = ttk.Frame(self._data_frame)
            cat_frame.pack(fill=tk.X, padx=2, pady=2)

            cat_label_frame = tk.Frame(cat_frame, bg="#E8F0FE", relief=tk.RAISED, bd=1)
            cat_label_frame.pack(fill=tk.X)

            icon = "▸" if block.collapsed else "▼"
            toggle_btn = tk.Button(
                cat_label_frame,
                text=f"{icon} {block.name}",
                font=("Arial", 10, "bold"),
                bg="#4472C4",
                fg="white",
                anchor="w",
                relief=tk.FLAT,
                command=lambda n=block.name: self._toggle_category(n),
            )
            toggle_btn.pack(fill=tk.X, padx=2, pady=2)

            if not block.collapsed:
                for cmd in block.commands:
                    cmd_frame = ttk.Frame(cat_frame)
                    cmd_frame.pack(fill=tk.X, padx=(20, 2), pady=1)

                    name_label = ttk.Label(cmd_frame, text=cmd.name, font=("Arial", 10), width=40, anchor="w")
                    name_label.pack(side=tk.LEFT, padx=5)

                    hotkey = cmd.hotkey or "—"
                    hotkey_color = "green" if cmd.hotkey and not self._generated else "black"
                    if self._generated and cmd.hotkey:
                        hotkey_color = "#0066CC"

                    hotkey_label = ttk.Label(
                        cmd_frame, text=hotkey, font=("Arial", 10, "bold"), width=25, anchor="w",
                    )
                    hotkey_label.pack(side=tk.LEFT, padx=5)

                    total_commands += 1

        self._stats_label.config(text=f"Категорий: {len(self._categories)} | Команд: {total_commands}")

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

    def _export_excel(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить Excel", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")], initialfile="Hotkeys.xlsx",
        )
        if path:
            export_excel(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def _export_md(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить Markdown", defaultextension=".md",
            filetypes=[("Markdown files", "*.md")], initialfile="Hotkeys.md",
        )
        if path:
            export_markdown(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def _export_json(self):
        if not self.result:
            messagebox.showwarning("Внимание", "Сначала сгенерируйте данные")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить JSON", defaultextension=".json",
            filetypes=[("JSON files", "*.json")], initialfile="hotkeys.json",
        )
        if path:
            export_json(self.result, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")

    def run(self):
        self.root.mainloop()
