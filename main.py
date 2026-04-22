import sys
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget,
    QMenu, QToolBar, QFileDialog, QMessageBox, QSplitter, QDialog,
    QLabel, QDialogButtonBox, QHBoxLayout, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtGui import QAction, QIcon, QTextCursor, QColor, QTextCharFormat, QBrush
from PyQt6.QtCore import Qt, QSize


class VisaCardAutomaton:
    """Автомат для номеров Visa (13, 16, 18, 19 цифр) со строгой проверкой формата."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 0
        self.digit_count = 0
        self.match_start = -1
        self.chars_since_space = 0  # Счетчик символов после последнего пробела

    def is_digit(self, char):
        return '0' <= char <= '9'

    def find_all_matches(self, text):
        matches = []
        self.reset()

        i = 0
        while i < len(text):
            char = text[i]

            if self.state == 0:
                # Ищем начало: '4' и перед ней не цифра
                if char == '4' and (i == 0 or not text[i - 1].isdigit()):
                    self.state = 1
                    self.digit_count = 1
                    self.match_start = i
                    self.chars_since_space = 1
                i += 1

            elif self.state == 1:
                if self.is_digit(char):
                    self.digit_count += 1
                    self.chars_since_space += 1
                    i += 1
                elif char == ' ':
                    # Пробел допустим только после группы цифр
                    # Проверяем формат в зависимости от текущего количества цифр
                    if self.digit_count == 4:
                        # После первых 4 цифр пробел допустим всегда
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 10 and self.chars_since_space == 6:
                        # Для 13 цифр: после 10 цифр пробел (формат 4-6-3)
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 8 and self.chars_since_space == 4:
                        # Для 16 цифр: после 8 цифр пробел
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 12 and self.chars_since_space == 4:
                        # Для 16 цифр: после 12 цифр пробел
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 10 and self.chars_since_space == 6:
                        # Для 18 цифр: после 10 цифр пробел
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 16 and self.chars_since_space == 6:
                        # Для 18 цифр: после 16 цифр пробел
                        self.chars_since_space = 0
                        i += 1
                    elif self.digit_count == 16 and self.chars_since_space == 4:
                        # Для 19 цифр: после 16 цифр пробел
                        self.chars_since_space = 0
                        i += 1
                    else:
                        # Пробел в неположенном месте — сброс
                        if self.digit_count in (13, 16, 18, 19):
                            matches.append({
                                'text': text[self.match_start:i],
                                'start': self.match_start,
                                'length': i - self.match_start
                            })
                        self.state = 0
                        self.digit_count = 0
                        # Не увеличиваем i, проверяем текущий символ заново
                else:
                    # Встретили не цифру и не пробел
                    if self.digit_count in (13, 16, 18, 19):
                        matches.append({
                            'text': text[self.match_start:i],
                            'start': self.match_start,
                            'length': i - self.match_start
                        })
                    self.state = 0
                    self.digit_count = 0
                    # Проверяем, может это начало нового номера
                    if char == '4':
                        self.state = 1
                        self.digit_count = 1
                        self.match_start = i
                        self.chars_since_space = 1
                    i += 1

        # Проверка в конце текста
        if self.state == 1 and self.digit_count in (13, 16, 18, 19):
            matches.append({
                'text': text[self.match_start:len(text)],
                'start': self.match_start,
                'length': len(text) - self.match_start
            })

        return matches


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.search_results = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 4. Поиск подстрок с РВ [*]")
        self.setGeometry(100, 100, 1400, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        main_splitter = QSplitter(Qt.Orientation.Vertical)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        main_splitter.addWidget(self.editor)

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        results_group = QGroupBox("Результаты поиска")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Найденная подстрока", "Позиция", "Длина"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.itemSelectionChanged.connect(self.highlight_selected_match)
        results_layout.addWidget(self.results_table)

        bottom_layout.addWidget(results_group)

        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Область вывода результатов...")
        self.output_area.setReadOnly(True)
        self.output_area.setMaximumHeight(100)
        bottom_layout.addWidget(self.output_area)

        main_splitter.addWidget(bottom_widget)
        main_splitter.setSizes([500, 300])
        main_layout.addWidget(main_splitter)

        self.result_count_label = QLabel("Найдено: 0")
        self.statusBar().addPermanentWidget(self.result_count_label)

        self.create_menus()
        self.create_toolbar()
        self.statusBar().showMessage("Готов к работе")

    def perform_search(self):
        text = self.editor.toPlainText()

        self.clear_highlighting()
        self.results_table.setRowCount(0)
        self.search_results = []

        if not text:
            QMessageBox.information(self, "Поиск", "Нет данных для поиска")
            self.result_count_label.setText("Найдено: 0")
            return

        search_type = self.search_type_combo.currentIndex()

        self.output_area.clear()
        self.output_area.append(f"Тип поиска: {self.search_type_combo.currentText()}")
        self.output_area.append("-" * 50)

        try:
            matches = []

            if search_type == 3:
                automaton = VisaCardAutomaton()
                matches = automaton.find_all_matches(text)
                self.output_area.append("Метод поиска: Конечный автомат (ДКА)")
                self.output_area.append("Состояния: 0-21, принимающие: 15, 18, 21")
            else:
                patterns = self.get_regex_patterns()
                pattern = patterns[search_type]
                regex = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                matches_iter = list(regex.finditer(text))

                for match in matches_iter:
                    matches.append({
                        'text': match.group(),
                        'start': match.start(),
                        'length': len(match.group())
                    })

                self.output_area.append("Метод поиска: Регулярное выражение")
                self.output_area.append(f"Шаблон: {pattern}")

            if not matches:
                self.output_area.append("Совпадений не найдено")
                self.result_count_label.setText("Найдено: 0")
                return

            self.results_table.setRowCount(len(matches))

            for i, match in enumerate(matches):
                matched_text = match['text']
                start_pos = match['start']
                length = match['length']

                line_num, col_num = self.get_line_column(text, start_pos)

                self.search_results.append({
                    'text': matched_text,
                    'start': start_pos,
                    'length': length,
                    'line': line_num,
                    'column': col_num
                })

                self.results_table.setItem(i, 0, QTableWidgetItem(matched_text))
                self.results_table.setItem(i, 1, QTableWidgetItem(f"{line_num}:{col_num}"))
                self.results_table.setItem(i, 2, QTableWidgetItem(str(length)))

            self.result_count_label.setText(f"Найдено: {len(matches)}")
            self.output_area.append(f"Найдено совпадений: {len(matches)}")
            self.statusBar().showMessage(f"Поиск завершен. Найдено {len(matches)} совпадений", 3000)

        except re.error as e:
            QMessageBox.critical(self, "Ошибка регулярного выражения", f"Неверное регулярное выражение:\n{e}")
            self.result_count_label.setText("Ошибка")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске:\n{e}")
            self.result_count_label.setText("Ошибка")

    def get_regex_patterns(self):
        return [
            # Числа
            r'(?<![,.\d!?\-])(?<!\d)\d+(?:,\d+)?(?![\d!?\-])(?![,.\d!?\-])',

            # Visa (РВ) - 13, 16, 18, 19 цифр
            r'\b4\d{18}\b|'  # 19 цифр слитно
            r'\b4\d{3} \d{4} \d{4} \d{4} \d{3}\b|'  # 19 цифр с пробелами
            r'\b4\d{17}\b|'  # 18 цифр слитно
            r'\b4\d{3} \d{6} \d{6}\b|'  # 18 цифр с пробелами
            r'\b4\d{15}\b|'  # 16 цифр слитно
            r'\b4\d{3} \d{4} \d{4} \d{4}\b|'  # 16 цифр с пробелами
            r'\b4\d{12}\b|'  # 13 цифр слитно
            r'\b4\d{3} \d{6} \d{3}\b',  # 13 цифр с пробелами

            # IPv6
            r'(?<![0-9A-Fa-f:])((?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,7}:|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,5}(?::[0-9A-Fa-f]{1,4}){1,2}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,4}(?::[0-9A-Fa-f]{1,4}){1,3}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,3}(?::[0-9A-Fa-f]{1,4}){1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,2}(?::[0-9A-Fa-f]{1,4}){1,5}|'
            r'[0-9A-Fa-f]{1,4}:(?::[0-9A-Fa-f]{1,4}){1,6}|'
            r':(?::[0-9A-Fa-f]{1,4}){1,7}|'
            r'::ffff:(?:[0-9]{1,3}\.){3}[0-9]{1,3}|'
            r'::|'
            r'::1)'
            r'/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8])(?![0-9])'
        ]

    def get_line_column(self, text, position):
        line_num = text.count('\n', 0, position) + 1
        last_newline = text.rfind('\n', 0, position)
        if last_newline == -1:
            col_num = position + 1
        else:
            col_num = position - last_newline
        return line_num, col_num

    def highlight_selected_match(self):
        selected_row = self.results_table.currentRow()
        if selected_row < 0 or selected_row >= len(self.search_results):
            return

        self.clear_highlighting()

        match_data = self.search_results[selected_row]
        start = match_data['start']
        length = match_data['length']

        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)

        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QBrush(QColor(255, 255, 0)))

        cursor.mergeCharFormat(format_highlight)

        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def clear_highlighting(self):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        format_clear = QTextCharFormat()
        format_clear.setBackground(QBrush(Qt.GlobalColor.white))
        cursor.mergeCharFormat(format_clear)

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
        text_items = ["Постановка задачи", "Грамматика", "Классификация грамматики",
                      "Метод анализа", "Тестовый пример", "Список литературы",
                      "Исходный код программы"]
        for item_text in text_items:
            action = QAction(item_text, self)
            action.triggered.connect(lambda checked, text=item_text: self.show_text_info(text))
            text_menu.addAction(action)

        run_menu = menubar.addMenu("Пуск")
        self.run_action = QAction("Запуск поиска", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.perform_search)
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

        run_tb = QAction(load_icon("run.png"), "Пуск (F5)", self)
        run_tb.triggered.connect(self.perform_search)
        toolbar.addAction(run_tb)

        toolbar.addSeparator()

        help_tb = QAction(load_icon("help.png"), "Справка", self)
        help_tb.triggered.connect(self.show_help)
        toolbar.addAction(help_tb)

        about_tb = QAction(load_icon("info.png"), "О программе", self)
        about_tb.triggered.connect(self.show_about)
        toolbar.addAction(about_tb)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("  Поиск: "))
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            "Числа",
            "Visa (РВ)",
            "IPv6",
            "[ДОП] Visa (автомат)"
        ])
        self.search_type_combo.setMinimumWidth(160)
        toolbar.addWidget(self.search_type_combo)


    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.current_file = None
            self.setWindowTitle("Лабораторная работа 4. Поиск подстрок с РВ [*]")
            self.setWindowModified(False)
            self.statusBar().showMessage("Новый файл создан")
            self.clear_highlighting()
            self.results_table.setRowCount(0)
            self.result_count_label.setText("Найдено: 0")

    def open_file(self):
        if self.maybe_save():
            test_files_path = os.path.join(os.getcwd(), "TestFiles")
            if not os.path.exists(test_files_path):
                test_files_path = os.getcwd()

            file_path, _ = QFileDialog.getOpenFileName(
                self, "Открыть файл", test_files_path,
                "Текстовые файлы (*.txt);;Все файлы (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.editor.setPlainText(content)
                    self.current_file = file_path
                    self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 4. Поиск подстрок с РВ[*]")
                    self.setWindowModified(False)
                    self.statusBar().showMessage(f"Файл загружен: {file_path}")
                    self.output_area.append(f"# Файл загружен: {file_path}\n")
                    self.clear_highlighting()
                    self.results_table.setRowCount(0)
                    self.result_count_label.setText("Найдено: 0")
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
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 4. Поиск подстрок с РВ[*]")
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
            return self.save_file_as()
        elif ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def show_text_info(self, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"<b>{title}</b>\n\nЭтот раздел будет реализован в следующих лабораторных работах.")
        label.setWordWrap(True)
        layout.addWidget(label)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        dialog.exec()

    def show_help(self):
        help_text = """
        <h2>Руководство пользователя</h2>
        <h3>Лабораторная работа 4: Поиск подстрок с регулярными выражениями</h3>
        <p><b>Доступные типы поиска:</b></p>
        <ul>
            <li><b>Числа:</b> целые и с плавающей точкой (разделитель запятая)</li>
            <li><b>Visa (РВ):</b> номера карт Visa через регулярное выражение</li>
            <li><b>IPv6:</b> адреса с префиксом /0-/128</li>
            <li><b>[ДОП] Visa (автомат):</b> номера карт Visa через конечный автомат</li>
        </ul>
        <p><b>Горячие клавиши:</b> F5 - запуск поиска</p>
        """
        self.output_area.setHtml(help_text)

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 4</b><br>"
            "Реализация алгоритма поиска подстрок с помощью регулярных выражений<br><br>"
            "<b>Варианты:</b><br>"
            "• Блок 1, Вариант 21: Числа<br>"
            "• Блок 2, Вариант 5: Номера карт Visa<br>"
            "• Блок 3, Вариант 3: IPv6 адрес с префиксом<br><br>"
            "<b>Дополнительное задание:</b> поиск Visa через конечный автомат<br><br>"
            "<b>Автор:</b> Топоев Максим<br>"
            "<b>Группа:</b> АП-327<br>"
            "<b>Год:</b> 2026"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())