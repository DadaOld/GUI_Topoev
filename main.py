import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenu, QToolBar, QFileDialog, QSplitter
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        # Настройки окна
        self.setWindowTitle("Лабораторная работа 1. Текстовый редактор")
        self.setGeometry(100, 100, 1000, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Разделитель
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Область редактирования
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")

        # Область вывода
        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Область вывода результатов...")
        self.output_area.setReadOnly(True)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.output_area)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

        # Создаем меню
        self.create_menus()

        # Пустая панель инструментов (пока без кнопок)
        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)

    def create_menus(self):
        menubar = self.menuBar()

        # === МЕНЮ ФАЙЛ ===
        file_menu = menubar.addMenu("Файл")

        # Создать
        new_action = QAction("Создать", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Открыть
        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Сохранить
        save_action = QAction("Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Сохранить как
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Выход
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # === МЕНЮ ПРАВКА ===
        edit_menu = menubar.addMenu("Правка")

        # Отмена
        undo_action = QAction("Отменить", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        # Повтор
        redo_action = QAction("Повторить", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Вырезать
        cut_action = QAction("Вырезать", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        # Копировать
        copy_action = QAction("Копировать", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        # Вставить
        paste_action = QAction("Вставить", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        # Удалить
        delete_action = QAction("Удалить", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(lambda: self.editor.insertPlainText(""))
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        # Выделить все
        select_all_action = QAction("Выделить все", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Пустые меню для структуры
        menubar.addMenu("Текст")
        menubar.addMenu("Пуск")
        menubar.addMenu("Справка")

    # Методы для работы с файлами
    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.setWindowTitle("Лабораторная работа 1. Текстовый редактор")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setPlainText(content)
                self.current_file = file_path
                self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 1. Текстовый редактор")
            except Exception as e:
                print(f"Ошибка: {e}")

    def save_file(self):
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл как", "", "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        if file_path:
            self._save_to_file(file_path)

    def _save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.current_file = file_path
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 1. Текстовый редактор")
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())