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
            'else': (2, "ключевое слово else")
        }

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

        self.two_char_operators = {
            '>=': (7, "оператор сравнения >="),
            '<=': (8, "оператор сравнения <="),
            '==': (9, "оператор сравнения =="),
            '!=': (10, "оператор сравнения !=")
        }

        self.compare_ops = {
            '>': (5, "оператор сравнения >"),
            '<': (6, "оператор сравнения <")
        }

    def is_letter(self, ch):
        return ch.isalpha() or ch == '_'

    def is_letter_or_digit(self, ch):
        return ch.isalpha() or ch.isdigit() or ch == '_'

    def is_digit(self, ch):
        return ch.isdigit()

    def scan(self, text):
        tokens = []
        errors = []

        i = 0
        line = 1
        line_start = 0
        n = len(text)

        while i < n:
            ch = text[i]
            pos = i - line_start + 1

            if ch == '\n':
                tokens.append(Token(21, "новая строка", ch, line, pos, pos))
                line += 1
                line_start = i + 1
                i += 1

            elif ch == ' ':
                tokens.append(Token(0, "пробел", ch, line, pos, pos))
                i += 1

            elif ch == '\t':
                tokens.append(Token(20, "табуляция", ch, line, pos, pos))
                i += 1

            elif self.is_letter(ch):
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
                else:
                    tokens.append(Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))

            elif self.is_digit(ch):
                start_i = i
                start_line = line
                start_pos = pos
                value = ""

                while i < n and self.is_digit(text[i]):
                    value += text[i]
                    i += 1

                tokens.append(Token(22, "число", value, start_line, start_pos, start_pos + len(value) - 1))

            elif i + 1 < n and text[i:i+2] in self.two_char_operators:
                two_chars = text[i:i+2]
                code, desc = self.two_char_operators[two_chars]
                tokens.append(Token(code, desc, two_chars, line, pos, pos + 1))
                i += 2

            elif ch in self.compare_ops:
                code, desc = self.compare_ops[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                i += 1

            elif ch in self.operators:
                code, desc = self.operators[ch]
                tokens.append(Token(code, desc, ch, line, pos, pos))
                i += 1

            else:
                errors.append({
                    'line': line,
                    'pos': pos,
                    'char': ch,
                    'message': f"Недопустимый символ '{ch}'"
                })
                i += 1

        return tokens, errors

    def get_table_data(self, tokens, errors):
        data = []
        for token in tokens:
            data.append(token.to_dict())
        for error in errors:
            data.append({
                'code': -1,
                'type_desc': 'ОШИБКА',
                'value': error['char'],
                'location': f"строка {error['line']}, позиция {error['pos']}",
                'line': error['line'],
                'start': error['pos'],
                'end': error['pos'],
                'is_error': True,
                'message': error['message']
            })
        return data


if __name__ == "__main__":
    scanner = Scanner()
    test = "if (a > b) {\n    max = a;\n}"
    tokens, errors = scanner.scan(test)
    for t in tokens:
        print(f"{t.code}: {t.value} - {t.type_desc} [строка {t.line}, {t.start_pos}-{t.end_pos}]")
    for e in errors:
        print(f"Ошибка: {e['message']} в строке {e['line']}, позиция {e['pos']}")