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


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.scanner = Scanner()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Лабораторная работа 2. Лексический анализатор [*]")
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
            self.setWindowTitle("Лабораторная работа 2. Лексический анализатор[*]")
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
                    self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 2[*]")
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
            self.setWindowTitle(f"{os.path.basename(file_path)} - Лабораторная работа 2[*]")
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

        self.output_area.append("Запуск лексического анализатора\n")

        # Запускаем сканер (теперь он возвращает еще и отфильтрованный текст)
        tokens, errors, filtered_text = self.scanner.scan(text)
        table_data = self.scanner.get_table_data(tokens, errors)

        # Выводим отфильтрованный текст
        self.output_area.append("Текст после удаления незначащих символов:")
        self.output_area.append(filtered_text)
        self.output_area.append("-" * 50)

        self.results_table.setRowCount(len(table_data))

        for row, item in enumerate(table_data):
            code_item = QTableWidgetItem(str(item['code']))
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.get('is_error', False):
                code_item.setBackground(Qt.GlobalColor.red)
                code_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 0, code_item)

            type_item = QTableWidgetItem(item['type_desc'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.get('is_error', False):
                type_item.setBackground(Qt.GlobalColor.red)
                type_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 1, type_item)

            value_item = QTableWidgetItem(repr(item['value']))
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.get('is_error', False):
                value_item.setBackground(Qt.GlobalColor.red)
                value_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 2, value_item)

            loc_item = QTableWidgetItem(item['location'])
            loc_item.setFlags(loc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.get('is_error', False):
                loc_item.setBackground(Qt.GlobalColor.red)
                loc_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, 3, loc_item)

            if not item.get('is_error', False):
                item['is_error'] = False
            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item)

        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setStretchLastSection(True)

        self.output_area.append(f"Найдено токенов: {len(tokens)}")
        self.output_area.append(f"Ошибок: {len(errors)}")
        self.output_area.append("\nАнализ завершен")

        self.statusBar().showMessage(f"Анализ завершен. Найдено токенов: {len(tokens)}, Ошибок: {len(errors)}", 3000)

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
                    self.statusBar().showMessage(f"Ошибка: {token_data.get('message', 'Неизвестная ошибка')}", 3000)

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
        <p><b>Меню "Пуск" (F5):</b> запускает лексический анализатор.</p>

        <h3>Особенности работы:</h3>
        <ul>
            <li><b>Незначащие символы</b> (пробелы, табуляции, переносы строк) автоматически удаляются</li>
            <li><b>Отфильтрованный текст</b> отображается в области вывода</li>
            <li><b>Навигация:</b> клик по строке таблицы перемещает курсор на соответствующую позицию</li>
            <li><b>Ошибки</b> выделяются красным цветом в таблице</li>
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
            <li><b>-1</b> - ошибка</li>
        </ul>
        """
        self.output_area.setHtml(help_text)

    def show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            "<b>Лабораторная работа 2</b><br>"
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