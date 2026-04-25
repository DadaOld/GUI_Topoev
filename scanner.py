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

        self.ALLOWED_CHARS = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_"
            "=+-*/(){};<>!&|."
        )

    def is_valid_identifier_char(self, ch):
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

            if ch == '\n':
                line += 1
                line_start = i + 1
                i += 1
                continue

            if ch in ' \t':
                i += 1
                continue

            if ch.isascii() and (ch.isalpha() or ch == '_'):
                start_line = line
                start_pos = pos
                value = ""

                while i < n and self.is_valid_identifier_char(text[i]):
                    value += text[i]
                    i += 1

                if value in self.keywords:
                    code, desc = self.keywords[value]
                    tokens.append(Token(code, desc, value, start_line, start_pos, start_pos + len(value) - 1))
                    filtered_text += value
                else:
                    tokens.append(Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                    filtered_text += value
                continue

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

            if i + 1 < n and text[i:i + 2] in self.two_char_operators:
                two_chars = text[i:i + 2]
                code, desc = self.two_char_operators[two_chars]
                tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                filtered_text += two_chars
                i += 2
                continue

            if ch in self.compare_ops:
                code, desc = self.compare_ops[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                filtered_text += ch
                i += 1
                continue

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

            if ch == '&':
                if i + 1 < n and text[i + 1] == '&':
                    two_chars = text[i:i + 2]
                    code, desc = self.two_char_operators[two_chars]
                    tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                    filtered_text += two_chars
                    i += 2
                else:
                    errors.append({
                        'line': line,
                        'pos_start': pos,
                        'pos_end': pos,
                        'char': '&',
                        'message': "недопустимый символ '&'"
                    })
                    tokens.append(Token(-1, "ошибка", '&', line, pos, pos))
                    filtered_text += '&'
                    i += 1
                continue

            if ch == '|':
                if i + 1 < n and text[i + 1] == '|':
                    two_chars = text[i:i + 2]
                    code, desc = self.two_char_operators[two_chars]
                    tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                    filtered_text += two_chars
                    i += 2
                else:
                    errors.append({
                        'line': line,
                        'pos_start': pos,
                        'pos_end': pos,
                        'char': '|',
                        'message': "недопустимый символ '|'"
                    })
                    tokens.append(Token(-1, "ошибка", '|', line, pos, pos))
                    filtered_text += '|'
                    i += 1
                continue

            if ch in self.symbols:
                code, desc = self.symbols[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                filtered_text += ch
                i += 1
                continue

            errors.append({
                'line': line,
                'pos_start': pos,
                'pos_end': pos,
                'char': ch,
                'message': f"недопустимый символ '{ch}'"
            })
            tokens.append(Token(-1, "ошибка", ch, line, pos, pos))
            filtered_text += ch
            i += 1

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