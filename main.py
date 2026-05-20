# main.py - ПОЛНЫЙ ФАЙЛ

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenu, QToolBar, QFileDialog, QMessageBox, QSplitter, QDialog,
    QLabel, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QGroupBox
)
from PyQt6.QtGui import QAction, QIcon, QTextCursor, QColor
from PyQt6.QtCore import Qt, QSize

from scanner import Scanner
from parser import parse_tokens
from ast_nodes import ASTPrinter
from semantic import SemanticAnalyzer


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_dir = None
        self.scanner = Scanner()
        self.semantic = SemanticAnalyzer()
        self.init_ui()
        self.init_save_dir()

    def init_save_dir(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_dir = os.path.join(base_dir, "Save_Files")
        if not os.path.exists(self.default_dir):
            os.makedirs(self.default_dir, exist_ok=True)
        self.current_dir = self.default_dir

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 5. Семантический анализатор [*]")
        self.setGeometry(100, 100, 1400, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # === ВЕРХНЯЯ ЧАСТЬ: два редактора ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Область для объявления переменных
        decl_group = QGroupBox("Объявление переменных (int имя = значение;)")
        decl_layout = QVBoxLayout(decl_group)
        self.decl_editor = QTextEdit()
        self.decl_editor.setPlaceholderText("int a = 5;\nint b = 10;\nint max;")
        self.decl_editor.setMaximumHeight(120)
        decl_layout.addWidget(self.decl_editor)
        top_layout.addWidget(decl_group)

        # Область для основного кода (if-else)
        code_group = QGroupBox("Основной код (if-else конструкция)")
        code_layout = QVBoxLayout(code_group)
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("if (a > b) {\n    max = a;\n} else {\n    max = b;\n};")
        code_layout.addWidget(self.code_editor)
        top_layout.addWidget(code_group)

        # === НИЖНЯЯ ЧАСТЬ: вкладки с результатами ===
        right_widget = QTabWidget()
        right_widget.setTabPosition(QTabWidget.TabPosition.North)

        self.lexer_output = QTextEdit()
        self.lexer_output.setPlaceholderText("Вывод лексического анализатора...")
        self.lexer_output.setReadOnly(True)
        right_widget.addTab(self.lexer_output, "Лексический анализатор")

        self.parser_output = QTextEdit()
        self.parser_output.setPlaceholderText("Вывод синтаксического анализатора...")
        self.parser_output.setReadOnly(True)
        right_widget.addTab(self.parser_output, "Синтаксический анализатор")

        self.ast_output = QTextEdit()
        self.ast_output.setPlaceholderText("Абстрактное синтаксическое дерево...")
        self.ast_output.setReadOnly(True)
        right_widget.addTab(self.ast_output, "AST (синтаксическое дерево)")

        self.semantic_output = QTextEdit()
        self.semantic_output.setPlaceholderText("Семантические ошибки...")
        self.semantic_output.setReadOnly(True)
        right_widget.addTab(self.semantic_output, "Семантический анализатор")

        # Таблица ошибок
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Неверный фрагмент", "Местоположение", "Описание ошибки", "Тип"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.itemClicked.connect(self.on_table_item_clicked)

        # Сплиттер
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.addWidget(self.results_table)
        main_splitter.setSizes([300, 400, 200])

        layout.addWidget(main_splitter)

        self.create_menus()
        self.create_toolbar()
        self.statusBar().showMessage("Готов к работе")

    def get_full_code(self):
        """Объединяет объявления переменных и основной код"""
        decl_code = self.decl_editor.toPlainText().strip()
        main_code = self.code_editor.toPlainText().strip()

        if decl_code and main_code:
            return decl_code + "\n\n" + main_code
        elif decl_code:
            return decl_code
        else:
            return main_code

    def create_menus(self):
        menubar = self.menuBar()

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

        edit_menu = menubar.addMenu("Правка")
        self.undo_action = QAction("Отменить", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(lambda: self.code_editor.undo())
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Повторить", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(lambda: self.code_editor.redo())
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()
        self.cut_action = QAction("Вырезать", self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.triggered.connect(lambda: self.code_editor.cut())
        edit_menu.addAction(self.cut_action)

        self.copy_action = QAction("Копировать", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(lambda: self.code_editor.copy())
        edit_menu.addAction(self.copy_action)

        self.paste_action = QAction("Вставить", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(lambda: self.code_editor.paste())
        edit_menu.addAction(self.paste_action)

        delete_action = QAction("Удалить", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(lambda: self.code_editor.insertPlainText(""))
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()
        select_all_action = QAction("Выделить все", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(lambda: self.code_editor.selectAll())
        edit_menu.addAction(select_all_action)

        text_menu = menubar.addMenu("Текст")
        text_items = [
            "Постановка задачи",
            "Грамматика",
            "Классификация грамматики",
            "Метод анализа",
            "Тестовый пример",
            "Список литературы",
            "Исходный код программы"
        ]
        for item_text in text_items:
            action = QAction(item_text, self)
            action.triggered.connect(lambda checked, text=item_text: self.show_text_info(text))
            text_menu.addAction(action)

        run_menu = menubar.addMenu("Пуск")
        self.run_action = QAction("Запуск анализатора", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.run_analyzer)
        run_menu.addAction(self.run_action)

        help_menu = menubar.addMenu("Справка")
        self.help_action = QAction("Вызов справки", self)
        self.help_action.setShortcut("F1")
        self.help_action.triggered.connect(self.show_help)
        help_menu.addAction(self.help_action)

        help_menu.addSeparator()
        self.about_action = QAction("О программе", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

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
        undo_tb.triggered.connect(lambda: self.code_editor.undo())
        toolbar.addAction(undo_tb)

        redo_tb = QAction(load_icon("redo.png"), "Повторить", self)
        redo_tb.triggered.connect(lambda: self.code_editor.redo())
        toolbar.addAction(redo_tb)

        toolbar.addSeparator()
        cut_tb = QAction(load_icon("cut.png"), "Вырезать", self)
        cut_tb.triggered.connect(lambda: self.code_editor.cut())
        toolbar.addAction(cut_tb)

        copy_tb = QAction(load_icon("copy.png"), "Копировать", self)
        copy_tb.triggered.connect(lambda: self.code_editor.copy())
        toolbar.addAction(copy_tb)

        paste_tb = QAction(load_icon("paste.png"), "Вставить", self)
        paste_tb.triggered.connect(lambda: self.code_editor.paste())
        toolbar.addAction(paste_tb)

        toolbar.addSeparator()
        run_tb = QAction(load_icon("run.png"), "Пуск", self)
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
            self.decl_editor.clear()
            self.code_editor.clear()
            self.current_file = None
            self.setWindowTitle("Лабораторная работа 5. Семантический анализатор[*]")
            self.setWindowModified(False)
            self.clear_results()
            self.statusBar().showMessage("Новый файл создан")

    def open_file(self):
        if self.maybe_save():
            start_dir = self.current_dir if self.current_dir else self.default_dir
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Открыть файл", start_dir, "Текстовые файлы (*.txt);;Все файлы (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Разделяем содержимое на объявления и код (упрощённо)
                    self.decl_editor.setPlainText(content)
                    self.code_editor.clear()
                    self.current_file = file_path
                    self.current_dir = os.path.dirname(file_path)
                    self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 5[*]")
                    self.setWindowModified(False)
                    self.clear_results()
                    self.statusBar().showMessage(f"Файл загружен: {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def save_file(self):
        if self.current_file:
            return self._save_to_file(self.current_file)
        else:
            return self.save_file_as()

    def save_file_as(self):
        start_dir = self.current_dir if self.current_dir else self.default_dir
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл как", start_dir, "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        if file_path:
            return self._save_to_file(file_path)
        return False

    def _save_to_file(self, file_path):
        try:
            full_code = self.get_full_code()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            self.current_file = file_path
            self.current_dir = os.path.dirname(file_path)
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 5[*]")
            self.setWindowModified(False)
            self.statusBar().showMessage(f"Файл сохранен: {file_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
            return False

    def maybe_save(self):
        if not self.code_editor.document().isModified() and not self.decl_editor.document().isModified():
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

    def clear_results(self):
        self.results_table.setRowCount(0)
        self.parser_output.clear()
        self.lexer_output.clear()
        self.ast_output.clear()
        self.semantic_output.clear()

    def _set_row_color(self, row, bg_color, fg_color):
        for col in range(self.results_table.columnCount()):
            item = self.results_table.item(row, col)
            if item:
                item.setBackground(bg_color)
                item.setForeground(fg_color)

    def run_analyzer(self):
        full_code = self.get_full_code()

        if not full_code.strip():
            QMessageBox.information(self, "Анализатор", "Нет текста для анализа.")
            return

        self.clear_results()

        tokens, lex_errors, filtered_text = self.scanner.scan(full_code)

        # Лексический анализатор
        self.lexer_output.append("Результаты лексического анализа:")
        self.lexer_output.append(f"Токенов: {len(tokens)}")

        if lex_errors:
            self.lexer_output.append(f"\nЛексических ошибок: {len(lex_errors)}")
            for err in lex_errors:
                line = err.get('line', 1)
                pos = err.get('pos_start', 1)
                char = err.get('char', '?')
                msg = err.get('message', '')
                self.lexer_output.append(f"  [{line}:{pos}] '{char}' - {msg}")
        else:
            self.lexer_output.append("\nЛексических ошибок не обнаружено.")

        if tokens:
            self.lexer_output.append("\nТокены:")
            for tok in tokens:
                self.lexer_output.append(f"  [{tok.line}:{tok.start_pos}] {tok.type_desc}: '{tok.value}'")

        # Синтаксический анализатор
        syntax_errors = []
        parse_success = True
        ast = None

        try:
            parse_success, syntax_errors, ast = parse_tokens(tokens, len(lex_errors) > 0)
        except Exception as e:
            self.parser_output.append(f"Ошибка парсера: {e}")
            import traceback
            traceback.print_exc()

        if parse_success and not syntax_errors:
            self.parser_output.append("Синтаксический анализ успешно завершен. Ошибок не найдено.")
        else:
            self.parser_output.append(f"Найдено синтаксических ошибок: {len(syntax_errors)}")
            for err in syntax_errors:
                self.parser_output.append(f"  [{err.line}:{err.pos}] '{err.fragment}' — {err.message}")

        # AST
        self.ast_output.clear()
        if ast and ast.nodes:
            ast_text = ASTPrinter.print(ast)
            self.ast_output.append("Абстрактное синтаксическое дерево (AST)")
            self.ast_output.append("")
            self.ast_output.append(ast_text)
        elif ast:
            ast_text = ASTPrinter.print(ast)
            self.ast_output.append("AST (частичный, с ошибками)")
            self.ast_output.append("")
            self.ast_output.append(ast_text)
        else:
            self.ast_output.append("AST не построен (синтаксические ошибки)")

        # Семантический анализатор
        semantic_errors = []
        if ast and parse_success and not lex_errors:
            self.semantic_output.append("Семантический анализ")
            self.semantic_output.append("")
            semantic_errors = self.semantic.analyze(ast)
            if semantic_errors:
                self.semantic_output.append(f"Найдено семантических ошибок: {len(semantic_errors)}")
                for err in semantic_errors:
                    self.semantic_output.append(f"  [{err.line}:{err.pos}] '{err.fragment}' — {err.message}")
            else:
                self.semantic_output.append("Семантических ошибок не обнаружено.")
        else:
            self.semantic_output.append("Семантический анализ не выполнен (есть лексические или синтаксические ошибки)")

        # Таблица ошибок
        all_rows = []
        for err in lex_errors:
            all_rows.append({
                'fragment': err.get('char', '?'),
                'line': err.get('line', 1),
                'pos': err.get('pos_start', 1),
                'message': err.get('message', ''),
                'type': 'Лексическая'
            })
        for err in syntax_errors:
            all_rows.append({
                'fragment': err.fragment,
                'line': err.line,
                'pos': err.pos,
                'message': err.message,
                'type': 'Синтаксическая'
            })
        for err in semantic_errors:
            all_rows.append({
                'fragment': err.fragment,
                'line': err.line,
                'pos': err.pos,
                'message': err.message,
                'type': 'Семантическая'
            })

        all_rows.sort(key=lambda r: (r['line'], r['pos']))

        self.results_table.setRowCount(len(all_rows))

        for row, entry in enumerate(all_rows):
            location = f"строка {entry['line']}, позиция {entry['pos']}"

            fragment_item = QTableWidgetItem(entry['fragment'])
            fragment_item.setFlags(fragment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            fragment_item.setData(Qt.ItemDataRole.UserRole, entry)

            location_item = QTableWidgetItem(location)
            location_item.setFlags(location_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            message_item = QTableWidgetItem(entry['message'])
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            type_item = QTableWidgetItem(entry['type'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.results_table.setItem(row, 0, fragment_item)
            self.results_table.setItem(row, 1, location_item)
            self.results_table.setItem(row, 2, message_item)
            self.results_table.setItem(row, 3, type_item)

            if entry['type'] == 'Лексическая':
                bg = QColor(255, 255, 200)
            elif entry['type'] == 'Синтаксическая':
                bg = QColor(255, 200, 200)
            else:
                bg = QColor(200, 200, 255)
            self._set_row_color(row, bg, QColor(0, 0, 0))

        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.statusBar().showMessage(
            f"Анализ завершен. Ошибок: лекс={len(lex_errors)}, синт={len(syntax_errors)}, сем={len(semantic_errors)}",
            5000)

    def on_table_item_clicked(self, item):
        row = item.row()
        data_item = self.results_table.item(row, 0)
        if not data_item:
            return
        entry = data_item.data(Qt.ItemDataRole.UserRole)
        if not entry:
            return
        line = entry.get('line', 1)
        pos = entry.get('pos', 1)
        self.go_to_position(line, pos)
        self.statusBar().showMessage(f"{entry.get('type', 'Ошибка')}: {entry.get('message', '')}", 3000)

    def go_to_position(self, line, column):
        decl_code = self.decl_editor.toPlainText()
        decl_lines = len(decl_code.split('\n')) if decl_code else 0

        if line <= decl_lines:
            cursor = self.decl_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            if line > 1:
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line - 1)
            if column > 1:
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, column - 1)
            self.decl_editor.setTextCursor(cursor)
            self.decl_editor.setFocus()
        else:
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            new_line = line - decl_lines
            if new_line > 1:
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, new_line - 1)
            if column > 1:
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, column - 1)
            self.code_editor.setTextCursor(cursor)
            self.code_editor.setFocus()

    def show_text_info(self, title):
        if title == "Тестовый пример":
            self.decl_editor.setPlainText("int a = 5;\nint b = 10;\nint max;")
            self.code_editor.setPlainText("if (a > b) {\n    max = a;\n} else {\n    max = b;\n};")
            self.statusBar().showMessage("Тестовый пример загружен в редактор", 3000)
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        if title == "Постановка задачи":
            text_edit.setPlainText("""Постановка задачи

Разработать лексический, синтаксический и семантический анализатор для конструкции if-else с блоком действий и объявлениями переменных.

Семантические проверки:
1. Уникальность имён переменных
2. Совместимость типов
3. Допустимые значения (диапазон int)
4. Использование объявленных переменных""")
        elif title == "Грамматика":
            text_edit.setPlainText("""Грамматика G[START]

<START> → (<DECL> | <IF>)*

<DECL> → "int" <id> ("=" <VALUE>)? ";"

<VALUE> → <num> | "true" | "false" | <id>

<IF> → "if" "(" <LOGIC> ")" "{" <ASSIGN>* "}" ("else" "{" <ASSIGN>* "}")? ";"

<ASSIGN> → <id> "=" <VALUE> ";"

<LOGIC> → <COMPARE> (<LOGIC_OP> <COMPARE>)*

<COMPARE> → <NOT>* <ATOM> (<COMPARE_OP> <ATOM>)?

<ATOM> → <id> | <num> | "(" <LOGIC> ")"

<NOT> → "!" | "not"
<LOGIC_OP> → "&&" | "and" | "||" | "or"
<COMPARE_OP> → ">" | "<" | ">=" | "<=" | "==" | "!=" """)

    def show_help(self):
        help_text = """<h2>Руководство пользователя</h2>
<p><b>Пуск (F5):</b> Запуск полного анализа</p>
<p><b>Семантические проверки:</b></p>
<ul>
<li>Уникальность имён переменных</li>
<li>Совместимость типов</li>
<li>Диапазон int (-2147483648..2147483647)</li>
<li>Использование объявленных переменных</li>
</ul>"""
        self.semantic_output.setHtml(help_text)

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 5</b><br>"
            "<b>Автор:</b> Топоев Максим<br>"
            "<b>Группа:</b> АП-327<br>"
            "<b>Преподаватель:</b> Антонянц Егор Николаевич<br>"
            "<b>Кафедра:</b> АСУ<br>"
            "<b>Год:</b> 2026"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())