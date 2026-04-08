import re

class TokenType:
    SPACE = 0
    TAB = 20
    NEWLINE = 21


class Token:
    def __init__(self, code, type_desc, value, line, start_pos, end_pos):
        self.code = code
        self.type_desc = type_desc
        self.value = value
        self.line = line
        self.start_pos = start_pos
        self.end_pos = end_pos

    def to_dict(self):
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
    def __init__(self):
        self.keywords = {
            'if': (1, "ключевое слово if"),
            'else': (2, "ключевое слово else"),
            'and': (23, "логическое и"),
            'or': (24, "логическое или"),
            'not': (25, "логическое не")
        }

        self.symbols = {
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

        self.two_char_operators = {
            '>=': (7, "оператор сравнения >="),
            '<=': (8, "оператор сравнения <="),
            '==': (9, "оператор сравнения =="),
            '!=': (10, "оператор сравнения !="),
            '&&': (23, "логическое и"),
            '||': (24, "логическое или")
        }

        self.compare_ops = {
            '>': (5, "оператор сравнения >"),
            '<': (6, "оператор сравнения <")
        }

        # Все допустимые символы языка (только ASCII)
        self.ALLOWED_CHARS = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_"
            "=+-*/(){};<>!&|."
        )

    def is_valid_identifier_char(self, ch):
        """Проверка символа для идентификатора (только латиница, цифры, _)"""
        return ch.isascii() and (ch.isalnum() or ch == '_')

    def scan(self, text):
        tokens = []
        errors = []
        filtered_text = ""

        i = 0
        line = 1
        line_start = 0
        n = len(text)

        while i < n:
            ch = text[i]
            pos = i - line_start + 1

            # Обработка переноса строки
            if ch == '\n':
                line += 1
                line_start = i + 1
                i += 1
                continue

            # Пропуск пробелов и табуляций
            if ch in ' \t':
                i += 1
                continue

            # Идентификаторы и ключевые слова (ТОЛЬКО латиница и _ в начале)
            if ch.isascii() and (ch.isalpha() or ch == '_'):
                start_line = line
                start_pos = pos
                value = ""
                has_error = False
                error_chars = ""

                # Собираем всё до пробела или оператора
                while i < n and text[i] not in ' \t\n(){};=<>!&|':
                    char = text[i]
                    if char.isascii() and (char.isalnum() or char == '_'):
                        if not has_error:
                            value += char
                        else:
                            error_chars += char
                    else:
                        has_error = True
                        if value:
                            # Сначала добавляем корректную часть как идентификатор
                            tokens.append(
                                Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                            filtered_text += value
                            value = ""
                        error_chars += char
                    i += 1

                if has_error:
                    # Вся оставшаяся часть — ошибка
                    if value:
                        tokens.append(
                            Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                        filtered_text += value
                    if error_chars:
                        errors.append({
                            'line': start_line,
                            'pos_start': start_pos + len(value),
                            'pos_end': start_pos + len(value) + len(error_chars) - 1,
                            'char': error_chars,
                            'message': f"недопустимые символы '{error_chars}'"
                        })
                        filtered_text += error_chars
                else:
                    if value in self.keywords:
                        code, desc = self.keywords[value]
                        tokens.append(Token(code, desc, value, start_line, start_pos, start_pos + len(value) - 1))
                    else:
                        tokens.append(
                            Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                    filtered_text += value
                continue

            # Числа
            if ch.isdigit():
                start_line = line
                start_pos = pos
                value = ""

                while i < n and text[i].isdigit():
                    value += text[i]
                    i += 1

                tokens.append(Token(22, "целое число", value, start_line, start_pos, start_pos + len(value) - 1))
                filtered_text += value
                continue

            # Двухсимвольные операторы
            if i + 1 < n and text[i:i + 2] in self.two_char_operators:
                two_chars = text[i:i + 2]
                code, desc = self.two_char_operators[two_chars]
                tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                filtered_text += two_chars
                i += 2
                continue

            # Односимвольные операторы сравнения
            if ch in self.compare_ops:
                code, desc = self.compare_ops[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                filtered_text += ch
                i += 1
                continue

            # Логическое НЕ
            if ch == '!':
                if i + 1 < n and text[i + 1] == '=':
                    two_chars = text[i:i + 2]
                    code, desc = self.two_char_operators[two_chars]
                    tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                    filtered_text += two_chars
                    i += 2
                else:
                    tokens.append(Token(25, "логическое не", ch, line, pos, pos))
                    filtered_text += ch
                    i += 1
                continue

            # Логическое И (одиночный &)
            if ch == '&':
                if i + 1 < n and text[i + 1] == '&':
                    two_chars = text[i:i + 2]
                    code, desc = self.two_char_operators[two_chars]
                    tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                    filtered_text += two_chars
                    i += 2
                else:
                    # Одиночный & - ошибка
                    errors.append({
                        'line': line,
                        'pos_start': pos,
                        'pos_end': pos,
                        'char': '&',
                        'message': "недопустимый символ '&'"
                    })
                    filtered_text += '&'
                    i += 1
                continue

            # Логическое ИЛИ (одиночный |)
            if ch == '|':
                if i + 1 < n and text[i + 1] == '|':
                    two_chars = text[i:i + 2]
                    code, desc = self.two_char_operators[two_chars]
                    tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                    filtered_text += two_chars
                    i += 2
                else:
                    # Одиночный | - ошибка
                    errors.append({
                        'line': line,
                        'pos_start': pos,
                        'pos_end': pos,
                        'char': '|',
                        'message': "недопустимый символ '|'"
                    })
                    filtered_text += '|'
                    i += 1
                continue

            # Остальные операторы и разделители
            if ch in self.symbols:
                code, desc = self.symbols[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                filtered_text += ch
                i += 1
                continue

            # ВСЕ ОСТАЛЬНЫЕ СИМВОЛЫ - ОШИБКА
            # Собираем последовательность недопустимых символов
            error_start_line = line
            error_start_pos = pos
            error_chars = ""

            while i < n:
                next_ch = text[i]
                # Останавливаемся на пробеле, переносе строки
                if next_ch in ' \t\n':
                    break
                # Останавливаемся на допустимом символе
                if next_ch in self.ALLOWED_CHARS:
                    break
                # Собираем недопустимый символ
                error_chars += next_ch
                i += 1

            if error_chars:
                errors.append({
                    'line': error_start_line,
                    'pos_start': error_start_pos,
                    'pos_end': error_start_pos + len(error_chars) - 1,
                    'char': error_chars,
                    'message': f"недопустимые символы '{error_chars}'"
                })
                filtered_text += error_chars

        return tokens, errors, filtered_text

    def get_table_data(self, tokens, errors):
        data = []

        for token in tokens:
            data.append(token.to_dict())

        for error in errors:
            char = error['char']
            pos_start = error.get('pos_start', 1)
            pos_end = error.get('pos_end', pos_start)

            data.append({
                'code': -1,
                'type_desc': 'ошибка',
                'value': char,
                'location': f"строка {error['line']}, {pos_start}-{pos_end}",
                'line': error['line'],
                'start': pos_start,
                'end': pos_end,
                'is_error': True,
                'is_lexical': True,
                'message': error['message']
            })

        return data


if __name__ == "__main__":
    scanner = Scanner()

    print("Тест сканера:")
    test = "if (a > b) { max = a; } else { max = b; };"
    print(f"Вход: {test}")
    tokens, errors, filtered = scanner.scan(test)
    print(f"Отфильтровано: {filtered}")
    print("Токены:")
    for t in tokens:
        print(f"  {t.code:3d} | {t.type_desc:25} | '{t.value}'")
    if errors:
        print("Ошибки:")
        for e in errors:
            print(f"  строка {e['line']}, {e['pos_start']}-{e['pos_end']}: {e['message']}")