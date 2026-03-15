import re

class TokenType:
    SPACE = 0
    TAB = 20
    NEWLINE = 21

class Token:
    """Класс для хранения информации о лексеме"""

    def __init__(self, code, type_desc, value, line, start_pos, end_pos):
        self.code = code
        self.type_desc = type_desc
        self.value = value
        self.line = line
        self.start_pos = start_pos
        self.end_pos = end_pos

    def to_dict(self):
        """Преобразование в словарь для таблицы"""
        return {
            'code': self.code,
            'type_desc': self.type_desc,
            'value': self.value,
            'location': f"строка {self.line}, {self.start_pos}-{self.end_pos}",
            'line': self.line,
            'start': self.start_pos,
            'end': self.end_pos
        }


class Scanner:
    """Лексический анализатор с фильтрацией незначащих символов"""

    def __init__(self):
        # Ключевые слова и их коды
        self.keywords = {
            'if': (1, "ключевое слово if"),
            'else': (2, "ключевое слово else")
        }

        # Операторы (односимвольные)
        self.operators = {
            '=': (4, "оператор присваивания"),
            '+': (11, "арифметический оператор +"),
            '-': (12, "арифметический оператор -"),
            '*': (13, "арифметический оператор *"),
            '/': (14, "арифметический оператор /"),
            '(': (15, "открывающая скобка"),
            ')': (16, "закрывающая скобка"),
            '{': (17, "открывающая фигурная скобка"),
            '}': (18, "закрывающая фигурная скобка"),
            ';': (19, "конец оператора")
        }

        # Двухсимвольные операторы
        self.two_char_operators = {
            '>=': (7, "оператор сравнения >="),
            '<=': (8, "оператор сравнения <="),
            '==': (9, "оператор сравнения =="),
            '!=': (10, "оператор сравнения !=")
        }

        # Односимвольные операторы сравнения
        self.compare_ops = {
            '>': (5, "оператор сравнения >"),
            '<': (6, "оператор сравнения <")
        }

    def is_letter(self, ch):
        """Проверка, является ли символ буквой или подчеркиванием"""
        return ch.isalpha() or ch == '_'

    def is_letter_or_digit(self, ch):
        """Проверка, является ли символ буквой, цифрой или подчеркиванием"""
        return ch.isalpha() or ch.isdigit() or ch == '_'

    def is_digit(self, ch):
        """Проверка, является ли символ цифрой"""
        return ch.isdigit()

    def is_whitespace(self, ch):
        """Проверка, является ли символ незначащим (пробел, табуляция, перенос строки)"""
        return ch in ' \t\n\r'

    def scan(self, text):
        """
        Принимает текст, возвращает (токены, ошибки)
        Незначащие символы (пробелы, табуляции, переносы строк) игнорируются
        """
        tokens = []
        errors = []

        # Отфильтрованная строка без незначащих символов
        filtered_text = ""

        i = 0
        line = 1
        line_start = 0
        n = len(text)

        print("Процесс сканирования")

        while i < n:
            ch = text[i]
            pos = i - line_start + 1  # позиция в строке (с 1)

            # Отслеживание переноса строки (для подсчета строк при ошибках)
            if ch == '\n':
                line += 1
                line_start = i + 1
                i += 1
                continue  # Пропускаем перевод строки

            # Пропускаем пробелы и табуляции
            if ch == ' ' or ch == '\t':
                i += 1
                continue

            # Если дошли до этого места, значит символ значимый
            # Добавляем его в отфильтрованную строку
            filtered_text += ch

            # Обработка значимых символов

            # Идентификаторы и ключевые слова
            if self.is_letter(ch):
                start_i = i
                start_line = line
                start_pos = pos
                value = ""

                while i < n and self.is_letter_or_digit(text[i]):
                    value += text[i]
                    i += 1

                if value in self.keywords:
                    code, desc = self.keywords[value]
                    tokens.append(Token(code, desc, value, start_line, start_pos, start_pos + len(value) - 1))
                    print(f"Найден токен: {desc} '{value}' (строка {start_line}, поз.{start_pos})")
                else:
                    tokens.append(Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                    print(f"Найден токен: идентификатор '{value}' (строка {start_line}, поз.{start_pos})")

            # Числа
            elif self.is_digit(ch):
                start_i = i
                start_line = line
                start_pos = pos
                value = ""

                while i < n and self.is_digit(text[i]):
                    value += text[i]
                    i += 1

                tokens.append(Token(22, "число", value, start_line, start_pos, start_pos + len(value) - 1))
                print(f"Найден токен: число '{value}' (строка {start_line}, поз.{start_pos})")

            # Двухсимвольные операторы
            elif i + 1 < n and text[i:i + 2] in self.two_char_operators:
                two_chars = text[i:i + 2]
                code, desc = self.two_char_operators[two_chars]
                tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                print(f"Найден токен: {desc} '{two_chars}' (строка {line}, поз.{pos})")
                i += 2

            # Односимвольные операторы сравнения
            elif ch in self.compare_ops:
                code, desc = self.compare_ops[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                print(f"Найден токен: {desc} '{ch}' (строка {line}, поз.{pos})")
                i += 1

            # Остальные операторы и разделители
            elif ch in self.operators:
                code, desc = self.operators[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                print(f"Найден токен: {desc} '{ch}' (строка {line}, поз.{pos})")
                i += 1

            # Нераспознанный символ - ошибка
            else:
                errors.append({
                    'line': line,
                    'pos': pos,
                    'char': ch,
                    'message': f"Недопустимый символ '{ch}'"
                })
                print(f"!!! Ошибка: недопустимый символ '{ch}' (строка {line}, поз.{pos})")
                i += 1

        print(f"\nРезультат")
        print(f"Исходный текст ({len(text)} символов):")
        print(repr(text))
        print(f"\nОтфильтрованный текст (только значимые символы, {len(filtered_text)} символов):")
        print(filtered_text)
        print(f"Найдено токенов: {len(tokens)}, ошибок: {len(errors)}")

        return tokens, errors, filtered_text

    def get_table_data(self, tokens, errors):
        """Подготовка данных для таблицы"""
        data = []
        for token in tokens:
            data.append(token.to_dict())
        for error in errors:
            data.append({
                'code': -1,
                'type_desc': 'Ошибка',
                'value': error['char'],
                'location': f"строка {error['line']}, позиция {error['pos']}",
                'line': error['line'],
                'start': error['pos'],
                'end': error['pos'],
                'is_error': True,
                'message': error['message']
            })
        return data


# Тестирование
if __name__ == "__main__":
    scanner = Scanner()

    # Тестовый пример из задания
    test_code = """if (a > b) {
    max = a;
} else {
    max = b;
};"""

    print("Тестирование сканера с фильтрацией")
    print("=" * 50)

    tokens, errors, filtered = scanner.scan(test_code)

    print("\n=== ТОКЕНЫ ===")
    for token in tokens:
        print(
            f"{token.code:3d} | {token.type_desc:25} | '{token.value}' | строка {token.line}, {token.start_pos}-{token.end_pos}")

    if errors:
        print("\nОшибки")
        for error in errors:
            print(f"Строка {error['line']}, поз.{error['pos']}: {error['message']}")

if __name__ == "__main__":
    scanner = Scanner()
    test = "if (a > b) {\n    max = a;\n}"
    tokens, errors = scanner.scan(test)
    for t in tokens:
        print(f"{t.code}: {t.value} - {t.type_desc} [строка {t.line}, {t.start_pos}-{t.end_pos}]")
    for e in errors:
        print(f"Ошибка: {e['message']} в строке {e['line']}, позиция {e['pos']}")