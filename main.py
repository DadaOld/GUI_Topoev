import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenu, QToolBar, QFileDialog, QMessageBox, QSplitter, QDialog,
    QLabel, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtGui import QAction, QIcon, QTextCursor
from PyQt6.QtCore import Qt, QSize

from scanner import Scanner
from parser import parse_tokens


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.scanner = Scanner()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 3. Синтаксический анализатор [*]")
        self.setGeometry(100, 100, 1400, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")
        self.editor.document().modificationChanged.connect(self.setWindowModified)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Код", "Тип лексемы", "Лексема", "Местоположение"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.itemClicked.connect(self.on_table_item_clicked)

        top_splitter.addWidget(self.editor)
        top_splitter.addWidget(self.results_table)
        top_splitter.setSizes([700, 700])

        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Область вывода результатов...")
        self.output_area.setReadOnly(True)

        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.output_area)
        main_splitter.setSizes([500, 200])

        layout.addWidget(main_splitter)

        self.create_menus()
        self.create_toolbar()
        self.statusBar().showMessage("Готов к работе")

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
            self.editor.clear()
            self.current_file = None
            self.setWindowTitle("Лабораторная работа 3. Синтаксический анализатор[*]")
            self.setWindowModified(False)
            self.clear_results()
            self.statusBar().showMessage("Новый файл создан")

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
                    self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 3[*]")
                    self.setWindowModified(False)
                    self.clear_results()
                    self.statusBar().showMessage(f"Файл загружен: {file_path}")
                    self.output_area.append(f"# Файл загружен: {file_path}\n")
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
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 3[*]")
            self.setWindowModified(False)
            self.statusBar().showMessage(f"Файл сохранен: {file_path}")
            self.output_area.append(f"# Файл сохранен: {file_path}")
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

    def clear_results(self):
        self.results_table.setRowCount(0)
        self.output_area.clear()

    def run_analyzer(self):
        text = self.editor.toPlainText()

        if not text:
            QMessageBox.information(self, "Анализатор", "Нет текста для анализа.")
            return

        self.clear_results()
        self.output_area.clear()

        tokens, lex_errors, filtered_text = self.scanner.scan(text)

        syntax_errors = []
        parse_success = True

        if tokens:
            try:
                parse_success, syntax_errors = parse_tokens(tokens, len(lex_errors) > 0)
            except Exception as e:
                self.output_area.append(f"Ошибка парсера: {e}")
                syntax_errors = []

        total_errors = len(lex_errors) + len(syntax_errors)

        if total_errors == 0:
            self.output_area.append("Анализ успешно завершен.")
            self.output_area.append(f"Токенов: {len(tokens)}")
            self.output_area.append("Ошибок не найдено.")
        else:
            self.output_area.append("Анализ завершен с ошибками.")

            if lex_errors:
                self.output_area.append("\nЛексические ошибки:")
                for err in lex_errors:
                    line = err.get('line', 1)
                    pos = err.get('pos_start', 1)
                    char = err.get('char', '?')
                    msg = err.get('message', 'неизвестная ошибка')
                    self.output_area.append(f"  строка {line}, позиция {pos}: '{char}' - {msg}")

            if syntax_errors:
                self.output_area.append("\nСинтаксические ошибки:")
                for err in syntax_errors:
                    line = err.line
                    pos = err.pos
                    fragment = err.fragment
                    msg = err.message
                    self.output_area.append(f"  строка {line}, позиция {pos}: '{fragment}' - {msg}")

            self.output_area.append(
                f"\nВсего ошибок: {total_errors} (лексических: {len(lex_errors)}, синтаксических: {len(syntax_errors)})")

        self.results_table.setRowCount(len(syntax_errors))
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Строка", "Позиция", "Сообщение"])

        for row, err in enumerate(syntax_errors):
            line_item = QTableWidgetItem(str(err.line))
            line_item.setFlags(line_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            line_item.setBackground(Qt.GlobalColor.red)
            line_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 0, line_item)

            pos_item = QTableWidgetItem(str(err.pos))
            pos_item.setFlags(pos_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            pos_item.setBackground(Qt.GlobalColor.red)
            pos_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 1, pos_item)

            msg_item = QTableWidgetItem(err.message)
            msg_item.setFlags(msg_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            msg_item.setBackground(Qt.GlobalColor.red)
            msg_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 2, msg_item)

            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, {
                'line': err.line,
                'start': err.pos,
                'end': err.pos,
                'is_error': True,
                'message': err.message
            })

        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.statusBar().showMessage(
            f"Анализ завершен. Ошибок: {total_errors}",
            5000
        )

    def on_table_item_clicked(self, item):
        row = item.row()
        data_item = self.results_table.item(row, 0)
        if data_item:
            token_data = data_item.data(Qt.ItemDataRole.UserRole)
            if token_data:
                line = token_data.get('line', 1)
                start = token_data.get('start', 1)
                self.go_to_position(line, start)
                if token_data.get('is_error', False):
                    self.statusBar().showMessage(
                        f"{'Лексическая' if token_data.get('is_lexical', True) else 'Синтаксическая'} ошибка: {token_data.get('message', 'Неизвестная ошибка')}",
                        3000
                    )

    def go_to_position(self, line, column):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        if line > 1:
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line - 1)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, column - 1)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def show_text_info(self, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        if title == "Постановка задачи":
            text_edit.setPlainText("""
    Постановка задачи

    Разработать лексический и синтаксический анализатор для конструкции if-else с блоком действий.

    Язык должен поддерживать:
    1. Ключевые слова: if, else
    2. Логические операторы: and, or, not, &&, ||, !
    3. Операторы сравнения: >, <, >=, <=, ==, !=
    4. Арифметические операторы: +, -, *, /
    5. Присваивание: =
    6. Разделители: (, ), {, }, ;
    7. Идентификаторы и числа

    Пример корректной программы:
    if (a > b) {
        max = a;
    } else {
        max = b;
    };

    Задача: выделить все лексемы из входного текста и проверить синтаксическую правильность конструкции.
    """)

        elif title == "Грамматика":
            text_edit.setPlainText("""
    Грамматика G[START] для конструкции if-else

    1) <START> → <IF_construction> <END>

    2) <IF_construction> → if ( <LOGICAL_EXP> ) { <INSTR> } else { <INSTR> } ;

    3) <LOGICAL_EXP> → <COMPARE_EXP> <LOGICAL_EXP_TAIL>

    4) <LOGICAL_EXP_TAIL> → <LOGICAL_OP> <COMPARE_EXP> <LOGICAL_EXP_TAIL> | ε

    5) <LOGICAL_OP> → && | and | || | or

    6) <NOT_OP> → ! | not

    7) <COMPARE_EXP> → <NOT_OP> <COMPARE_EXP> | ( <LOGICAL_EXP> ) | <EXP>

    8) <EXP> → <id> <COMPARE> <id> | <id> <COMPARE> <num> | <num> <COMPARE> <id>

    9) <COMPARE> → > | < | >= | <= | == | !=

    10) <INSTR> → <id> = <id> ; | <id> = <num> ;

    11) <id> → <letter> <ID_TAIL>

    12) <ID_TAIL> → <letter> <ID_TAIL> | <digit> <ID_TAIL> | ε

    13) <num> → <digit> <NUM_TAIL>

    14) <NUM_TAIL> → <digit> <NUM_TAIL> | ε

    15) <letter> → a | b | c | ... | z | A | B | C | ... | Z

    16) <digit> → 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9

    17) <END> → ε
    """)

        elif title == "Классификация грамматики":
            text_edit.setPlainText("""
    Классификация грамматики по Хомскому

    Данная грамматика относится к типу 2 (контекстно-свободная).

    Обоснование:
    1. Все правила имеют вид A → α, где A - нетерминал, α - строка из терминалов и нетерминалов
    2. Отсутствуют контекстно-зависимые правила (нет ограничений на окружение)
    3. Грамматика содержит рекурсивные правила (<LOGICAL_EXP_TAIL> может содержать себя)

    КС-грамматики достаточны для описания большинства конструкций языков программирования, включая вложенные структуры и сбалансированные скобки.

    Грамматика преобразована к LL(1)-виду (устранена левая рекурсия):
    - <LOGICAL_EXP> → <COMPARE_EXP> <LOGICAL_EXP_TAIL> (вместо леворекурсивного правила)
    - <id> → <letter> <ID_TAIL>
    - <num> → <digit> <NUM_TAIL>
    """)

        elif title == "Метод анализа":
            text_edit.setPlainText("""
    Метод анализа

    Для синтаксического анализа используется метод рекурсивного спуска.

    Особенности:
    1. Каждому нетерминалу грамматики соответствует своя функция
    2. Анализ выполняется слева направо (LL-анализ)
    3. Для восстановления после ошибок используется метод Айронса

    Метод Айронса:
    - При обнаружении ошибки парсер не останавливается
    - Ошибочный фрагмент пропускается до ближайшего синхронизирующего токена (if, else, {, }, ;)
    - Анализ продолжается с этого места

    Преимущества рекурсивного спуска:
    - Простота реализации
    - Наглядность (код соответствует грамматике)
    - Удобная обработка ошибок
    - Естественная поддержка рекурсивных конструкций
    """)

        elif title == "Тестовый пример":
            text_edit.setPlainText("""
    Тестовый пример

    Корректная программа:

    if (a > b) {
        max = a;
    } else {
        max = b;
    };

    Результат лексического анализа:

    Код | Тип лексемы              | Лексема
    ----|--------------------------|--------
    1   | ключевое слово if        | if
    15  | открывающая скобка       | (
    3   | идентификатор            | a
    5   | оператор сравнения >     | >
    3   | идентификатор            | b
    23  | логическое и             | and
    15  | открывающая скобка       | (
    3   | идентификатор            | a
    5   | оператор сравнения >     | >
    3   | идентификатор            | c
    24  | логическое или           | or
    25  | логическое не            | not
    15  | открывающая скобка       | (
    3   | идентификатор            | b
    6   | оператор сравнения <     | <
    3   | идентификатор            | c
    16  | закрывающая скобка       | )
    16  | закрывающая скобка       | )
    17  | открывающая фигурная     | {
    3   | идентификатор            | a
    4   | оператор присваивания    | =
    22  | число                    | 1
    19  | конец оператора          | ;
    18  | закрывающая фигурная     | }
    2   | ключевое слово else      | else
    17  | открывающая фигурная     | {
    3   | идентификатор            | b
    4   | оператор присваивания    | =
    3   | идентификатор            | c
    19  | конец оператора          | ;
    18  | закрывающая фигурная     | }
    19  | конец оператора          | ;

    Результат синтаксического анализа: ошибок не обнаружено.
    """)

        elif title == "Список литературы":
            text_edit.setPlainText("""
    Список литературы

    1. Ахо А., Лам М., Сети Р., Ульман Д. Компиляторы: принципы, технологии и инструментарий. — 2-е изд. — М.: Вильямс, 2008. — 1175 с.

    2. Вирт Н. Построение компиляторов. — М.: ДМК Пресс, 2010. — 192 с.

    3. Грис Д. Конструирование компиляторов для цифровых вычислительных машин. — М.: Мир, 1975. — 544 с.

    4. Карпов Ю. Г. Теория автоматов. — СПб.: Питер, 2002. — 206 с.

    5. Шорников Ю. В. Теория языков программирования: проектирование и реализация. — Новосибирск: Изд-во НГТУ, 2022. — 290 с.

    6. Шорников Ю. В. Теория и практика языковых процессоров. — Новосибирск: Изд-во НГТУ, 2004. — 204 с.

    7. Свердлов С. З. Языки программирования и методы трансляции. — СПб.: Лань, 2019. — 564 с.

    8. Гордеев А. В., Молчанов А. Ю. Системное программное обеспечение. — СПб.: Питер, 2001. — 734 с.
    """)

        elif title == "Исходный код программы":
            text_edit.setPlainText("""
    Исходный код программы

    Программа состоит из следующих модулей:

    1. main.py - графический интерфейс пользователя (GUI)
       - Редактор текста
       - Таблица результатов
       - Меню и панель инструментов

    2. scanner.py - лексический анализатор
       - Распознавание ключевых слов if, else
       - Распознавание логических операторов and, or, not, &&, ||, !
       - Распознавание операторов сравнения
       - Распознавание идентификаторов и чисел
       - Фильтрация незначащих символов
       - Группировка подряд идущих ошибок

    3. parser.py - синтаксический анализатор
       - Рекурсивный спуск по грамматике
       - Обработка синтаксических ошибок (метод Айронса)
       - Восстановление после ошибок

    Основные классы:
    - Token - хранение информации о лексеме
    - Scanner - лексический анализ
    - Parser - синтаксический анализ
    - SyntaxError - хранение информации об ошибке

    Полный исходный код доступен в файлах проекта.
    """)

        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def show_help(self):
        help_text = """
        <h2>Руководство пользователя</h2>
        <p><b>Меню "Файл":</b></p>
        <ul>
            <li><b>Создать (Ctrl+N)</b> - новый файл</li>
            <li><b>Открыть (Ctrl+O)</b> - открыть файл</li>
            <li><b>Сохранить (Ctrl+S)</b> - сохранить изменения</li>
            <li><b>Сохранить как (Ctrl+Shift+S)</b> - сохранить в новый файл</li>
            <li><b>Выход (Ctrl+Q)</b> - закрыть программу</li>
        </ul>
        <p><b>Меню "Правка":</b></p>
        <ul>
            <li><b>Отмена (Ctrl+Z), Повтор (Ctrl+Y)</b></li>
            <li><b>Вырезать (Ctrl+X), Копировать (Ctrl+C), Вставить (Ctrl+V)</b></li>
            <li><b>Удалить (Del), Выделить все (Ctrl+A)</b></li>
        </ul>
        <p><b>Меню "Пуск" (F5):</b> запускает лексический и синтаксический анализаторы.</p>

        <h3>Особенности работы:</h3>
        <ul>
            <li><b>Незначащие символы</b> (пробелы, табуляции, переносы строк) автоматически удаляются</li>
            <li><b>Отфильтрованный текст</b> отображается в области вывода</li>
            <li><b>Навигация:</b> клик по строке таблицы перемещает курсор на соответствующую позицию</li>
            <li><b>Лексические ошибки</b> выделяются красным цветом в таблице</li>
            <li><b>Синтаксические ошибки</b> также отображаются в таблице</li>
        </ul>

        <h3>Коды лексем:</h3>
        <ul>
            <li><b>1</b> - ключевое слово if</li>
            <li><b>2</b> - ключевое слово else</li>
            <li><b>3</b> - идентификатор</li>
            <li><b>4</b> - оператор присваивания (=)</li>
            <li><b>5</b> - оператор сравнения ></li>
            <li><b>6</b> - оператор сравнения <</li>
            <li><b>7</b> - оператор сравнения >=</li>
            <li><b>8</b> - оператор сравнения <=</li>
            <li><b>9</b> - оператор сравнения ==</li>
            <li><b>10</b> - оператор сравнения !=</li>
            <li><b>11</b> - арифметический оператор +</li>
            <li><b>12</b> - арифметический оператор -</li>
            <li><b>13</b> - арифметический оператор *</li>
            <li><b>14</b> - арифметический оператор /</li>
            <li><b>15</b> - открывающая скобка (</li>
            <li><b>16</b> - закрывающая скобка )</li>
            <li><b>17</b> - открывающая фигурная скобка {</li>
            <li><b>18</b> - закрывающая фигурная скобка }</li>
            <li><b>19</b> - конец оператора ;</li>
            <li><b>22</b> - число</li>
            <li><b>23</b> - логическое И (&&, and)</li>
            <li><b>24</b> - логическое ИЛИ (||, or)</li>
            <li><b>25</b> - логическое НЕ (!, not)</li>
            <li><b>-1</b> - ошибка</li>
        </ul>
        """
        self.output_area.setHtml(help_text)

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 3</b><br>"
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