import os
import re
from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QToolBar, QFileDialog, QMessageBox, QSplitter, QDialog,
    QLabel, QDialogButtonBox, QTabWidget, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
)
from PyQt6.QtGui import QAction, QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize

from scanner import Scanner, TokenType
from parser import Parser
from rpn import RpnConverter


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 6 - Анализатор выражений [*]")
        self.setGeometry(100, 100, 1500, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Введите арифметическое выражение, например: a+b*c или (2+3)*4")
        self.editor.document().modificationChanged.connect(self.setWindowModified)

        self.error_table = QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels(["Тип", "Символ", "Строка", "Столбец", "Описание"])
        self.error_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.error_table.setAlternatingRowColors(True)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.error_table)
        splitter.setSizes([400, 300])

        left_layout.addWidget(splitter)

        self.info_tabs = QTabWidget()
        self.info_tabs.setMaximumWidth(550)

        self.lexer_output = QPlainTextEdit()
        self.lexer_output.setReadOnly(True)
        self.lexer_output.setFont(QFont("Courier New", 9))
        self.info_tabs.addTab(self.lexer_output, "Лексер")

        self.tokens_output = QPlainTextEdit()
        self.tokens_output.setReadOnly(True)
        self.tokens_output.setFont(QFont("Courier New", 9))
        self.info_tabs.addTab(self.tokens_output, "Токены")

        self.parser_output = QPlainTextEdit()
        self.parser_output.setReadOnly(True)
        self.parser_output.setFont(QFont("Courier New", 9))
        self.info_tabs.addTab(self.parser_output, "Парсер")

        self.triad_output = QPlainTextEdit()
        self.triad_output.setReadOnly(True)
        self.triad_output.setFont(QFont("Courier New", 9))
        self.info_tabs.addTab(self.triad_output, "Тетрады")

        self.rpn_output = QPlainTextEdit()
        self.rpn_output.setReadOnly(True)
        self.rpn_output.setFont(QFont("Courier New", 9))
        self.info_tabs.addTab(self.rpn_output, "ПОЛИЗ")


        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(self.info_tabs, 1)

        self.create_menus()
        self.create_toolbar()
        self.statusBar().showMessage("Готов к работе")

    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")

        new_action = QAction("Создать", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

        edit_menu.addSeparator()

        select_all_action = QAction("Выделить все", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_all_action)

        text_menu = menubar.addMenu("Текст")

        grammar_action = QAction("Грамматика", self)
        grammar_action.triggered.connect(self.show_grammar)
        text_menu.addAction(grammar_action)

        classification_action = QAction("Классификация грамматики", self)
        classification_action.triggered.connect(self.show_classification)
        text_menu.addAction(classification_action)

        method_action = QAction("Метод анализа", self)
        method_action.triggered.connect(self.show_method)
        text_menu.addAction(method_action)

        text_menu.addSeparator()

        examples_action = QAction("Тестовые примеры", self)
        examples_action.triggered.connect(self.show_examples)
        text_menu.addAction(examples_action)

        literature_action = QAction("Список литературы", self)
        literature_action.triggered.connect(self.show_literature)
        text_menu.addAction(literature_action)

        source_action = QAction("Исходный код программы", self)
        source_action.triggered.connect(self.show_source)
        text_menu.addAction(source_action)

        analyze_menu = menubar.addMenu("Анализ")

        self.run_action = QAction("Запустить анализатор", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.run_analyzer)
        analyze_menu.addAction(self.run_action)

        help_menu = menubar.addMenu("Справка")

        help_action = QAction("Вызов справки", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(24, 24))

        def load_icon(filename):
            icon_path = os.path.join("icons", filename)
            if os.path.exists(icon_path):
                return QIcon(icon_path)
            return QIcon()

        new_tb = QAction(load_icon("new.png"), "Создать", self)
        new_tb.triggered.connect(self.new_file)
        toolbar.addAction(new_tb)

        open_tb = QAction(load_icon("open.png"), "Открыть", self)
        open_tb.triggered.connect(self.open_file)
        toolbar.addAction(open_tb)

        save_tb = QAction(load_icon("save.png"), "Сохранить", self)
        save_tb.triggered.connect(self.save_file)
        toolbar.addAction(save_tb)

        toolbar.addSeparator()

        undo_tb = QAction(load_icon("undo.png"), "Отменить", self)
        undo_tb.triggered.connect(self.editor.undo)
        toolbar.addAction(undo_tb)

        redo_tb = QAction(load_icon("redo.png"), "Повторить", self)
        redo_tb.triggered.connect(self.editor.redo)
        toolbar.addAction(redo_tb)

        toolbar.addSeparator()

        cut_tb = QAction(load_icon("cut.png"), "Вырезать", self)
        cut_tb.triggered.connect(self.editor.cut)
        toolbar.addAction(cut_tb)

        copy_tb = QAction(load_icon("copy.png"), "Копировать", self)
        copy_tb.triggered.connect(self.editor.copy)
        toolbar.addAction(copy_tb)

        paste_tb = QAction(load_icon("paste.png"), "Вставить", self)
        paste_tb.triggered.connect(self.editor.paste)
        toolbar.addAction(paste_tb)

        toolbar.addSeparator()

        run_tb = QAction(load_icon("run.png"), "Запустить анализатор", self)
        run_tb.triggered.connect(self.run_analyzer)
        toolbar.addAction(run_tb)

        toolbar.addSeparator()

        help_tb = QAction(load_icon("help.png"), "Справка", self)
        help_tb.triggered.connect(self.show_help)
        toolbar.addAction(help_tb)

        about_tb = QAction(load_icon("info.png"), "О программе", self)
        about_tb.triggered.connect(self.show_about)
        toolbar.addAction(about_tb)

    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.setWindowTitle("Лабораторная работа 6 - Анализатор выражений [*]")
            self.setWindowModified(False)
            self.statusBar().showMessage("Новый файл создан")
            self.clear_output()

    def clear_output(self):
        self.error_table.setRowCount(0)
        self.lexer_output.clear()
        self.tokens_output.clear()
        self.parser_output.clear()
        self.triad_output.clear()
        self.rpn_output.clear()

    def add_error_to_table(self, error_type, symbol, line, column, description):
        row = self.error_table.rowCount()
        self.error_table.insertRow(row)

        error_item = QTableWidgetItem(error_type)
        error_item.setBackground(QColor(255, 200, 200))

        self.error_table.setItem(row, 0, error_item)
        self.error_table.setItem(row, 1, QTableWidgetItem(str(symbol)))
        self.error_table.setItem(row, 2, QTableWidgetItem(str(line)))
        self.error_table.setItem(row, 3, QTableWidgetItem(str(column)))
        self.error_table.setItem(row, 4, QTableWidgetItem(description))

    def open_file(self):
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Открыть файл", "", "Текстовые файлы (*.txt);;Все файлы (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.editor.setPlainText(content)
                    self.current_file = file_path
                    self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 6 [*]")
                    self.setWindowModified(False)
                    self.statusBar().showMessage(f"Файл загружен: {file_path}")
                    self.clear_output()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

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
            return True
        return False

    def _save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.current_file = file_path
            self.editor.document().setModified(False)
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 6 [*]")
            self.setWindowModified(False)
            self.statusBar().showMessage(f"Файл сохранен: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

    def maybe_save(self):
        if not self.editor.document().isModified():
            return True
        ret = QMessageBox.warning(
            self, "Сохранение",
            "Документ был изменен. Сохранить изменения?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def show_grammar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Грамматика")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 11))
        text.setPlainText("""
Грамматика арифметических выражений:

E -> T A
A -> eps | +TA | -TA
T -> F B
B -> eps | *FB | /FB | %FB
F -> число | идентификатор | (E)

Терминалы: +  -  *  /  %  (  )  число  идентификатор
Нетерминалы: E, A, T, B, F
Аксиома: E
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def show_classification(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Классификация грамматики")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 11))
        text.setPlainText("""
Классификация по Хомскому: Тип 2 (контекстно-свободная)

Обоснование:
  - Левая часть каждого правила содержит один нетерминал
  - Правая часть может содержать любую последовательность
    терминалов и нетерминалов

Свойства:
  - Допускает построение синтаксического дерева
  - Анализируется методом рекурсивного спуска
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def show_method(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Метод анализа")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 11))
        text.setPlainText("""
Метод: рекурсивный спуск

Функции для каждого нетерминала:
  parse_E()  - E -> T A
  parse_T()  - T -> F B
  parse_F()  - F -> число | id | (E)

Приоритет: * / % выше + -
Ассоциативность: левая

Преимущества:
  - Простота реализации
  - Наглядность
  - Удобство генерации тетрад при разборе
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def show_examples(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Тестовые примеры")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 11))
        text.setPlainText("""
Корректные:
  5, a, a+b, a+b*c, (a+b)*c, 2+3*4, (2+3)*4

С ошибками:
  a+        (неполное выражение)
  *a        (начинается с оператора)
  a++b      (два оператора подряд)
  (a+b      (нет закрывающей скобки)
  a@b       (неизвестный символ)
  a+*b      (оператор вместо операнда)
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def show_literature(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Список литературы")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 11))
        text.setPlainText("""
1. Ахо А., Ульман Дж., Сети Р. Компиляторы: принципы,
   технологии и инструменты. - М.: Вильямс, 2008.

2. Вирт Н. Построение компиляторов. - М.: ДМК Пресс, 2010.

3. Свердлов С.З. Языки программирования и методы трансляции.
   - СПб.: Питер, 2007.
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def show_source(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Исходный код программы")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 9))
        text.setPlainText("""
Модули программы:
  main.py     - точка входа
  editor.py   - графический интерфейс
  scanner.py  - лексический анализатор
  parser.py   - синтаксический анализатор
  rpn.py      - ПОЛИЗ и вычисления

Разработчик: Топоев Максим, АП-327, 2026
        """)
        layout.addWidget(text)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec()

    def run_analyzer(self):
        text = self.editor.toPlainText().strip()
        self.clear_output()

        if not text:
            QMessageBox.information(self, "Внимание", "Введите выражение для анализа")
            return

        scanner = Scanner(text)
        scan_result = scanner.tokenize_with_details()
        tokens = scan_result["tokens"]

        self.lexer_output.appendPlainText(f"Вход: {text}\n")

        temp_scanner = Scanner(text)
        while True:
            token = temp_scanner.get_next_token()
            if token.type == TokenType.END:
                self.lexer_output.appendPlainText("Конец")
                break
            elif token.type == TokenType.ERROR:
                self.lexer_output.appendPlainText(
                    f"ошибка: '{token.value}' [{token.line}:{token.column}]"
                )
            else:
                self.lexer_output.appendPlainText(
                    f"{token.type.value}: '{token.value}' [{token.line}:{token.column}]"
                )

        for err in scan_result["errors"]:
            self.add_error_to_table("Лексическая", err.value, err.line, err.column, "Неизвестный символ")

        self.tokens_output.appendPlainText("Токены:")
        for token in tokens:
            if token.type == TokenType.ERROR:
                self.tokens_output.appendPlainText(f"  Ошибка: '{token.value}' [{token.line}:{token.column}]")
            elif token.type != TokenType.END:
                self.tokens_output.appendPlainText(
                    f"  {token.type.value}: '{token.value}' [{token.line}:{token.column}]"
                )

        parser = Parser(tokens)
        success, syntax_errors, triads, _ = parser.parse()

        if success:
            self.parser_output.appendPlainText("Успешно — синтаксических ошибок нет")
        else:
            self.parser_output.appendPlainText(f"Ошибка — найдено синтаксических ошибок: {len(syntax_errors)}\n")
            for i, err in enumerate(syntax_errors, 1):
                self.parser_output.appendPlainText(f"  {i}: {err}")

        for err in syntax_errors:
            m = re.match(r'строка (\d+), колонка (\d+): (.+)', err)
            if m:
                self.add_error_to_table("Синтаксическая", "-", int(m.group(1)), int(m.group(2)), m.group(3))
            else:
                self.add_error_to_table("Синтаксическая", "-", 0, 0, err)

        if triads:
            self.triad_output.appendPlainText("Тетрады:")
            for i, (op, arg1, arg2, res) in enumerate(triads, 1):
                self.triad_output.appendPlainText(f"  {i}: ({op}, {arg1}, {arg2}, {res})")
        else:
            if success:
                self.triad_output.appendPlainText("Нет тетрад (одиночный операнд)")
            else:
                self.triad_output.appendPlainText("Тетрады не строятся при наличии ошибок")

        if not scan_result["has_errors"] and not syntax_errors:
            rpn_tokens, rpn_errors = RpnConverter.infix_to_rpn(tokens)
            rpn_str = ' '.join(rpn_tokens)
            self.rpn_output.appendPlainText(f"ПОЛИЗ: {rpn_str}")

            has_identifiers = any(t.type == TokenType.IDENTIFIER for t in tokens)
            if not has_identifiers:
                value, eval_errors = RpnConverter.evaluate_rpn(rpn_tokens)
                if eval_errors:
                    for err in eval_errors:
                        self.rpn_output.appendPlainText(f"Ошибка: {err}")
                else:
                    self.rpn_output.appendPlainText(f"Результат: {value}")
            else:
                self.rpn_output.appendPlainText("Вычисление невозможно (есть переменные)")
        else:
            self.rpn_output.appendPlainText("ПОЛИЗ не строится при наличии ошибок")


        if scan_result["has_errors"] or syntax_errors:
            self.statusBar().showMessage("Анализ завершен с ошибками", 3000)
        else:
            self.statusBar().showMessage("Анализ успешен", 3000)

    def show_help(self):
        self.clear_output()
        self.lexer_output.appendPlainText("""Как пользоваться:

1. Введите выражение в левой верхней области
2. Нажмите F5 или кнопку "Запустить анализатор"

Операции: +  -  *  /  %  ( )

Примеры:
  a+b*c
  (2+3)*4
  100+200-50
  a+*b (пример с ошибкой)""")

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 6</b><br>"
            "Синтаксический анализатор и внутреннее представление программы<br><br>"
            "<b>Разработчик:</b> Топоев Максим<br>"
            "<b>Группа:</b> АП-327<br>"
            "<b>Год:</b> 2026"
        )