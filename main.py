import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenu, QToolBar, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 1. Текстовый редактор")
        self.setGeometry(100, 100, 1000, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Разделитель
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")
        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Область вывода результатов...")
        self.output_area.setReadOnly(True)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.output_area)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

        # Создаем меню
        self.create_menus()

        # Создаем панель инструментов
        self.create_toolbar()

    def create_menus(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("Файл")

        self.new_action = QAction("Создать", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)

        self.open_action = QAction("Открыть...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)

        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction("Сохранить как...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(self.save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Правка
        edit_menu = menubar.addMenu("Правка")

        self.undo_action = QAction("Отменить", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Повторить", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        self.cut_action = QAction("Вырезать", self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(self.cut_action)

        self.copy_action = QAction("Копировать", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(self.copy_action)

        self.paste_action = QAction("Вставить", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(self.paste_action)

        delete_action = QAction("Удалить", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(lambda: self.editor.insertPlainText(""))
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Выделить все", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        # Текст (пустое)
        menubar.addMenu("Текст")

        # Пуск (пустое)
        menubar.addMenu("Пуск")

        # Справка
        help_menu = menubar.addMenu("Справка")

        self.help_action = QAction("Справка", self)
        self.help_action.triggered.connect(self.show_help)
        help_menu.addAction(self.help_action)

        help_menu.addSeparator()

        self.about_action = QAction("О программе", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)

        # Кнопки файлов
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()

        # Кнопки отмены/повтора
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()

        # Кнопки буфера обмена
        toolbar.addAction(self.cut_action)
        toolbar.addAction(self.copy_action)
        toolbar.addAction(self.paste_action)
        toolbar.addSeparator()

        # Заглушка для кнопки Пуск
        run_action = QAction("Пуск", self)
        run_action.triggered.connect(self.run_placeholder)
        toolbar.addAction(run_action)
        toolbar.addSeparator()

        # Кнопки справки
        toolbar.addAction(self.help_action)
        toolbar.addAction(self.about_action)

    # Методы файлов
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

    # Заглушка для кнопки Пуск
    def run_placeholder(self):
        self.output_area.append("Анализатор будет запущен здесь")

    # Методы справки
    def show_help(self):
        self.output_area.setPlainText(
            "Справка\n"
            "\n"
            "Файл: Создать (Ctrl+N), Открыть (Ctrl+O), Сохранить (Ctrl+S), Сохранить как (Ctrl+Shift+S), Выход (Ctrl+Q)\n"
            "Правка: Отмена (Ctrl+Z), Повторить (Ctrl+Y), Копировать (Ctrl+C), Вставить (Ctrl+V), Выделить все (Ctrl+A)\n"
            "Панель инструментов дублирует основные функции"
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "Лабораторная работа 1\n"
            "Автор: Топоев Максим\n"
            "Группа: АП-327\n"
            "Преподаватель: Антонянц Егор Николаевич\n"
            "Кафедра АСУ"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())