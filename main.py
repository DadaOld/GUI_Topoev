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
    """
    Детерминированный конечный автомат для распознавания номеров карт Visa.

    Правила:
    - Начинается с границы слова (перед номером не цифра/разделитель)
    - Первая цифра: '4'
    - Затем 12 цифр (в сумме 13)
    - Опционально еще 0, 1 или 2 группы по 3 цифры (длина 13, 16 или 19)
    - Поддерживаются разделители: пробел и дефис
    - Заканчивается границей слова (после номера не цифра/разделитель)

    Состояния автомата:
    0 - начальное состояние (ожидание границы)
    1 - найдена граница (ожидание '4')
    2 - найдена '4' (ожидание 12 цифр)
    3-14 - подсчет 12 обязательных цифр
    15 - принимающее (13 цифр)
    16-17 - подсчет дополнительных 3 цифр
    18 - принимающее (16 цифр)
    19-20 - подсчет дополнительных 3 цифр
    21 - принимающее (19 цифр)
    """

    def __init__(self):
        # Состояния автомата
        self.STATE_START = 0
        self.STATE_BOUNDARY = 1
        self.STATE_FIRST_4 = 2
        # Состояния подсчета 12 цифр (3-14)
        self.STATE_ACCEPT_13 = 15
        self.STATE_GROUP1_1 = 16
        self.STATE_GROUP1_2 = 17
        self.STATE_ACCEPT_16 = 18
        self.STATE_GROUP2_1 = 19
        self.STATE_GROUP2_2 = 20
        self.STATE_ACCEPT_19 = 21

        # Принимающие состояния
        self.accepting_states = {
            self.STATE_ACCEPT_13,
            self.STATE_ACCEPT_16,
            self.STATE_ACCEPT_19
        }

        self.reset()

    def reset(self):
        """Сброс автомата в начальное состояние"""
        self.current_state = self.STATE_START
        self.digit_count = 0
        self.match_start = -1
        self.potential_start = -1
        self.in_match = False

    def is_digit(self, char):
        """Проверка, является ли символ цифрой"""
        return '0' <= char <= '9'

    def is_separator(self, char):
        """Проверка, является ли символ разделителем"""
        return char in ' -'

    def find_all_matches(self, text):
        """
        Поиск всех совпадений в тексте с помощью конечного автомата.

        Returns:
            list: список словарей с ключами 'text', 'start', 'length'
        """
        matches = []
        self.reset()

        i = 0
        while i < len(text):
            char = text[i]

            if self.current_state == self.STATE_START:
                # Ищем границу перед номером
                if not self.is_digit(char) and not self.is_separator(char):
                    self.current_state = self.STATE_BOUNDARY
                    self.potential_start = i + 1
                i += 1

            elif self.current_state == self.STATE_BOUNDARY:
                # Ожидаем первую цифру '4'
                if char == '4':
                    self.current_state = self.STATE_FIRST_4
                    self.digit_count = 1
                    self.match_start = i
                    i += 1
                elif not self.is_digit(char) and not self.is_separator(char):
                    self.potential_start = i + 1
                    i += 1
                else:
                    self.current_state = self.STATE_START
                    i += 1

            elif self.current_state == self.STATE_FIRST_4:
                # Первая цифра уже '4', ждем остальные 11 цифр
                if self.is_digit(char):
                    self.digit_count += 1
                    if self.digit_count == 13:
                        self.current_state = self.STATE_ACCEPT_13
                    else:
                        # Состояния 3-14
                        self.current_state = 2 + self.digit_count
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # Встретили не цифру и не разделитель - сброс
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif 3 <= self.current_state <= 14:
                # Подсчет 12 цифр после первой
                if self.is_digit(char):
                    self.digit_count += 1
                    if self.digit_count == 13:
                        self.current_state = self.STATE_ACCEPT_13
                    else:
                        self.current_state = 2 + self.digit_count
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_ACCEPT_13:
                # Проверяем, не продолжается ли номер (может быть 16 цифр)
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_GROUP1_1
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # Принимаем как 13-значный номер
                    matched_text = text[self.match_start:i]
                    matches.append({
                        'text': matched_text,
                        'start': self.match_start,
                        'length': len(matched_text)
                    })
                    self.reset()
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_GROUP1_1:
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_GROUP1_2
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # 14 цифр - невалидно, сброс
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_GROUP1_2:
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_ACCEPT_16
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # 15 цифр - невалидно, сброс
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_ACCEPT_16:
                # Проверяем, не продолжается ли номер (может быть 19 цифр)
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_GROUP2_1
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # Принимаем как 16-значный номер
                    matched_text = text[self.match_start:i]
                    matches.append({
                        'text': matched_text,
                        'start': self.match_start,
                        'length': len(matched_text)
                    })
                    self.reset()
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_GROUP2_1:
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_GROUP2_2
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # 17 цифр - невалидно, сброс
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_GROUP2_2:
                if self.is_digit(char):
                    self.digit_count += 1
                    self.current_state = self.STATE_ACCEPT_19
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # 18 цифр - невалидно, сброс
                    self.current_state = self.STATE_START
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1

            elif self.current_state == self.STATE_ACCEPT_19:
                if self.is_digit(char):
                    # Больше 19 цифр - невалидно, сброс
                    self.current_state = self.STATE_START
                    i += 1
                elif self.is_separator(char):
                    i += 1
                else:
                    # Принимаем как 19-значный номер
                    matched_text = text[self.match_start:i]
                    matches.append({
                        'text': matched_text,
                        'start': self.match_start,
                        'length': len(matched_text)
                    })
                    self.reset()
                    if not self.is_digit(char) and not self.is_separator(char):
                        self.current_state = self.STATE_BOUNDARY
                        self.potential_start = i + 1
                    i += 1
            else:
                i += 1

        # Проверка в конце текста
        if self.current_state in self.accepting_states:
            matched_text = text[self.match_start:len(text)]
            matches.append({
                'text': matched_text,
                'start': self.match_start,
                'length': len(matched_text)
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

        # Панель управления поиском
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_layout.addWidget(QLabel("Тип поиска:"))

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            "Числа (целые и с плавающей точкой)",
            "Номера карт Visa (автомат)",
            "IPv6 адрес с префиксом"
        ])
        self.search_type_combo.setMinimumWidth(280)
        search_layout.addWidget(self.search_type_combo)

        self.search_button = QPushButton("🔍 Найти")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        self.result_count_label = QLabel("Найдено: 0")
        search_layout.addWidget(self.result_count_label)

        search_layout.addStretch()
        main_layout.addWidget(search_panel)

        # Основной разделитель
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Область ввода текста...")
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        main_splitter.addWidget(self.editor)

        # Нижняя часть с результатами
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

        self.create_menus()
        self.create_toolbar()
        self.statusBar().showMessage("Готов к работе")

    def perform_search(self):
        """Выполняет поиск по выбранному типу"""
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

            if search_type == 1:  # Visa через автомат (доп. задание)
                automaton = VisaCardAutomaton()
                matches = automaton.find_all_matches(text)
                self.output_area.append("Метод поиска: Конечный автомат (ДКА)")
                self.output_area.append("Состояния автомата: 22")
                self.output_area.append("Принимающие состояния: 15 (13 цифр), 18 (16 цифр), 21 (19 цифр)")
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
        """Возвращает список регулярных выражений для вариантов"""
        return [
            # Вариант 21: Числа (целые и с плавающей точкой, разделитель запятая)
            r'(?<![,\d])\b\d+(?:,\d+)?\b(?![,\d])',

            # Вариант 5: Номера карт Visa (используется автомат, РВ для справки)
            r'(?<![-\s\d])4(?:[\s-]?\d){12}(?:(?:[\s-]?\d{3}){0,2})?(?![-\s\d])',

            # Вариант 3: IPv6 адрес с префиксом (/0 - /128)
            r'(?<![0-9A-Fa-f:])((?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,7}:|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,5}(?::[0-9A-Fa-f]{1,4}){1,2}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,4}(?::[0-9A-Fa-f]{1,4}){1,3}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,3}(?::[0-9A-Fa-f]{1,4}){1,4}|'
            r'(?:[0-9A-Fa-f]{1,4}:){1,2}(?::[0-9A-Fa-f]{1,4}){1,5}|'
            r'[0-9A-Fa-f]{1,4}:(?::[0-9A-Fa-f]{1,4}){1,6}|'
            r':(?::[0-9A-Fa-f]{1,4}){1,7})'
            r'/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8])(?![0-9])'
        ]

    def get_line_column(self, text, position):
        """Вычисляет номер строки и столбца по абсолютной позиции"""
        line_num = text.count('\n', 0, position) + 1
        last_newline = text.rfind('\n', 0, position)
        if last_newline == -1:
            col_num = position + 1
        else:
            col_num = position - last_newline
        return line_num, col_num

    def highlight_selected_match(self):
        """Подсвечивает выбранное совпадение в редакторе"""
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
        """Очищает всю подсветку в редакторе"""
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

        run_tb = QAction(load_icon("run.png"), "Найти", self)
        run_tb.triggered.connect(self.perform_search)
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
            self.setWindowTitle("Лабораторная работа 4. Поиск подстрок с РВ [*]")
            self.setWindowModified(False)
            self.statusBar().showMessage("Новый файл создан")
            self.clear_highlighting()
            self.results_table.setRowCount(0)
            self.result_count_label.setText("Найдено: 0")

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
                    self.setWindowTitle(
                        f"{os.path.basename(file_path)} - Лабораторная работа 4. Поиск подстрок с РВ[*]")
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

        label = QLabel(f"<b>{title}</b>\n\nЭтот раздел будет реализован в следующих лабораторных работах.\n\n"
                       f"Здесь будет размещена информация о грамматике, методе анализа и т.д.")
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
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
            <li><b>Номера карт Visa:</b> 13, 16 или 19 цифр, начинаются с 4 (реализовано через конечный автомат)</li>
            <li><b>IPv6 адрес с префиксом:</b> формат x:x:x:x:x:x:x:x/0-128</li>
        </ul>
        <p><b>Использование:</b></p>
        <ol>
            <li>Введите или загрузите текст в редактор</li>
            <li>Выберите тип поиска из выпадающего списка</li>
            <li>Нажмите кнопку "Найти" или F5</li>
            <li>Результаты отобразятся в таблице</li>
            <li>При выборе строки в таблице соответствующая подстрока подсветится в тексте</li>
        </ol>
        """
        self.output_area.setHtml(help_text)

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 4</b><br>"
            "Реализация алгоритма поиска подстрок с помощью регулярных выражений<br><br>"
            "<b>Варианты:</b><br>"
            "• Блок 1, Вариант 21: Числа (целые и с плавающей точкой)<br>"
            "• Блок 2, Вариант 5: Номера карт Visa (автомат)<br>"
            "• Блок 3, Вариант 3: IPv6 адрес с префиксом<br><br>"
            "<b>Дополнительное задание:</b> реализация поиска номеров Visa через конечный автомат<br><br>"
            "<b>Автор:</b> Топоев Максим<br>"
            "<b>Группа:</b> АП-327<br>"
            "<b>Год:</b> 2026"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())