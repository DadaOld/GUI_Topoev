import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenuBar, QMenu, QToolBar, QSplitter
)
from PyQt6.QtCore import Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Настройки окна
        self.setWindowTitle("Лабораторная работа 1. Топоев Максим, АП-327")
        self.setGeometry(100, 100, 1000, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем разделитель (splitter) для двух областей
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Область редактирования (верхняя)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")

        # Область вывода (нижняя)
        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Область вывода результатов...")
        self.output_area.setReadOnly(True)

        # Добавляем области в разделитель
        splitter.addWidget(self.editor)
        splitter.addWidget(self.output_area)

        # Устанавливаем начальное соотношение размеров (70% на 30%)
        splitter.setSizes([400, 200])

        # Добавляем разделитель на главный слой
        layout.addWidget(splitter)

        # Создаем пустое меню (заглушки)
        menubar = self.menuBar()

        # Пустые меню для структуры
        file_menu = menubar.addMenu("Файл")
        edit_menu = menubar.addMenu("Правка")
        text_menu = menubar.addMenu("Текст")
        run_menu = menubar.addMenu("Пуск")
        help_menu = menubar.addMenu("Справка")

        # Создаем пустую панель инструментов
        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())