import logging
from pathlib import Path

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QAction, QColor, QFont, QIcon
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMenu,
        QMenuBar,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QStatusBar,
        QTableWidget,
        QTableWidgetItem,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False

from ..ai.engine import AIEngine
from ..analyzer import analyze_commands
from ..compare.comparator import HotkeyComparator
from ..config import HotkeyConfig, load_config
from ..exporter_excel import export_excel
from ..exporter_json import export_json
from ..exporter_md import export_markdown
from ..generator import generate_hotkeys
from ..models.analysis import AnalysisResult
from ..pdf_parser import parse_pdf
from ..windows_conflicts.checker import WindowsConflictChecker

logger = logging.getLogger(__name__)


class LoadWorker(QThread):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, pdf_path: str, config: HotkeyConfig):
        super().__init__()
        self.pdf_path = pdf_path
        self.config = config

    def run(self):
        try:
            self.progress.emit("Загрузка PDF...")
            raw_commands = parse_pdf(self.pdf_path, config=self.config)
            self.progress.emit("Анализ команд...")
            result = analyze_commands(raw_commands)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class GenerateWorker(QThread):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, result: AnalysisResult, config: HotkeyConfig, use_ai: bool = False):
        super().__init__()
        self.result = result
        self.config = config
        self.use_ai = use_ai

    def run(self):
        try:
            if self.use_ai:
                self.progress.emit("AI генерация...")
                ai_engine = AIEngine(self.config)
                result = ai_engine.generate(self.result)
            else:
                self.progress.emit("Генерация клавиш...")
                result = generate_hotkeys(self.result, self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class QtHotkeyManagerApp(QMainWindow):
    def __init__(self):
        if not HAS_PYSIDE6:
            raise ImportError("PySide6 не установлен. Установите: pip install PySide6")

        super().__init__()
        self.setWindowTitle("HotkeyManager — БАЗИС-Мебельщик")
        self.setGeometry(100, 100, 1200, 800)

        self.config = load_config()
        self.result: AnalysisResult | None = None
        self.checker = WindowsConflictChecker()

        self._setup_ui()

    def _setup_ui(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Открыть PDF", self._open_pdf, "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Экспорт Excel", self._export_excel, "Ctrl+E")
        file_menu.addAction("Экспорт Markdown", self._export_md)
        file_menu.addAction("Экспорт JSON", self._export_json)
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close, "Ctrl+Q")

        tools_menu = menubar.addMenu("Инструменты")
        tools_menu.addAction("Сравнить версии", self._compare_versions)
        tools_menu.addAction("Проверить конфликты", self._check_conflicts)

        toolbar = QToolBar("Главная")
        self.addToolBar(toolbar)

        toolbar.addAction("📂 Загрузить", self._open_pdf)
        toolbar.addSeparator()
        toolbar.addAction("⚡ Генерировать", self._generate)
        toolbar.addAction("🤖 AI", self._generate_ai)
        toolbar.addSeparator()
        toolbar.addAction("📊 Excel", self._export_excel)
        toolbar.addAction("📝 Markdown", self._export_md)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        info_layout = QHBoxLayout()
        self.pdf_label = QLabel("PDF не загружен")
        self.pdf_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.pdf_label)
        info_layout.addStretch()
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(self.stats_label)
        layout.addLayout(info_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Категория", "Команда", "Текущая клавиша", "Новая клавиша", "Статус"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
                gridline-color: #ddd;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        layout.addWidget(self.table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.statusBar().showMessage("Готово")

    def _open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF files (*.pdf);;All files (*.*)"
        )
        if not path:
            return

        self.pdf_label.setText(f"PDF: {Path(path).name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = LoadWorker(path, self.config)
        self.worker.finished.connect(self._on_load_finished)
        self.worker.error.connect(self._on_load_error)
        self.worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.worker.start()

    def _on_load_finished(self, result: AnalysisResult):
        self.result = result
        self._update_table()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"Загружено: {len(result.commands)} команд")

    def _on_load_error(self, error: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить PDF:\n{error}")
        self.statusBar().showMessage("Ошибка загрузки")

    def _generate(self, use_ai: bool = False):
        if not self.result:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите PDF")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = GenerateWorker(self.result, self.config, use_ai)
        self.worker.finished.connect(self._on_generate_finished)
        self.worker.error.connect(self._on_generate_error)
        self.worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.worker.start()

    def _generate_ai(self):
        self._generate(use_ai=True)

    def _on_generate_finished(self, result: AnalysisResult):
        self.result = result
        self._update_table()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Генерация завершена")

    def _on_generate_error(self, error: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Ошибка", f"Ошибка генерации:\n{error}")

    def _update_table(self):
        if not self.result:
            return

        self.table.setRowCount(len(self.result.commands))

        status_colors = {
            "assigned": QColor("#C6EFCE"),
            "needs_assignment": QColor("#FFEB9C"),
            "duplicate": QColor("#FFC7CE"),
        }

        status_labels = {
            "assigned": "✅ Назначена",
            "needs_assignment": "🔄 Требует назначения",
            "duplicate": "⚠️ Дубликат",
        }

        for row, cmd in enumerate(self.result.commands):
            items = [
                cmd.category,
                cmd.name,
                cmd.current_hotkey or "—",
                cmd.suggested_hotkey or "—",
                status_labels.get(cmd.status, cmd.status),
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if cmd.status in status_colors:
                    item.setBackground(status_colors[cmd.status])
                self.table.setItem(row, col, item)

        summary = self.result.summary()
        self.stats_label.setText(
            f"Команд: {summary['total']} | "
            f"Назначено: {summary['assigned']} | "
            f"Свободно: {summary['free']} | "
            f"Дубликатов: {summary['duplicates']}"
        )

    def _export_excel(self):
        if not self.result:
            QMessageBox.warning(self, "Внимание", "Нет данных для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить Excel", "Hotkeys.xlsx", "Excel files (*.xlsx)"
        )
        if path:
            export_excel(self.result, path)
            QMessageBox.information(self, "Готово", f"Сохранено: {path}")

    def _export_md(self):
        if not self.result:
            QMessageBox.warning(self, "Внимание", "Нет данных для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить Markdown", "Hotkeys.md", "Markdown files (*.md)"
        )
        if path:
            export_markdown(self.result, path)
            QMessageBox.information(self, "Готово", f"Сохранено: {path}")

    def _export_json(self):
        if not self.result:
            QMessageBox.warning(self, "Внимание", "Нет данных для экспорта")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить JSON", "hotkeys.json", "JSON files (*.json)"
        )
        if path:
            export_json(self.result, path)
            QMessageBox.information(self, "Готово", f"Сохранено: {path}")

    def _compare_versions(self):
        old_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите старый PDF", "", "PDF files (*.pdf)"
        )
        if not old_path:
            return

        new_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите новый PDF", "", "PDF files (*.pdf)"
        )
        if not new_path:
            return

        self.statusBar().showMessage("Сравнение версий...")

        try:
            old_raw = parse_pdf(old_path, config=self.config)
            old_commands = analyze_commands(old_raw)

            new_raw = parse_pdf(new_path, config=self.config)
            new_commands = analyze_commands(new_raw)

            comparator = HotkeyComparator()
            result = comparator.compare(old_commands.commands, new_commands.commands)

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить результат", "comparison.md", "Markdown files (*.md)"
            )
            if save_path:
                comparator.export_markdown(result, save_path)
                QMessageBox.information(self, "Готово", f"Сравнение сохранено: {save_path}")

            self.statusBar().showMessage("Сравнение завершено")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сравнения:\n{e}")

    def _check_conflicts(self):
        if not self.result:
            QMessageBox.warning(self, "Внимание", "Сначала загрузите данные")
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
            QMessageBox.warning(self, "Конфликты", msg)
        else:
            QMessageBox.information(self, "Проверка", "Конфликтов не найдено")


def run_qt_app():
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = QtHotkeyManagerApp()
    window.show()
    sys.exit(app.exec())
