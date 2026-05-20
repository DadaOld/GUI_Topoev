# scanner.py - полная версия

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
            'int': (30, "тип int"),
            'double': (31, "тип double"),
            'boolean': (32, "тип boolean"),
            'String': (33, "тип String"),
            'true': (40, "логическое значение true"),
            'false': (41, "логическое значение false")
        }

        self.symbols = {
            '=': (4, "оператор присваивания"),
            '(': (15, "открывающая скобка"),
            ')': (16, "закрывающая скобка"),
            '{': (17, "открывающая фигурная скобка"),
            '}': (18, "закрывающая фигурная скобка"),
            ';': (19, "конец оператора"),
            '"': (50, "кавычка")
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

            # Строковые литералы
            if ch == '"':
                start_line = line
                start_pos = pos
                value = '"'
                i += 1
                while i < n and text[i] != '"':
                    value += text[i]
                    i += 1
                if i < n and text[i] == '"':
                    value += '"'
                    i += 1
                else:
                    errors.append({
                        'line': line,
                        'pos_start': start_pos,
                        'pos_end': pos,
                        'char': value,
                        'message': "незакрытая строка"
                    })
                tokens.append(Token(51, "строковый литерал", value, start_line, start_pos, start_pos + len(value) - 1))
                filtered_text += value
                continue

            # Идентификаторы и ключевые слова
            if ch.isalpha() or ch == '_':
                start_line = line
                start_pos = pos
                value = ""

                while i < n and (text[i].isalnum() or text[i] == '_'):
                    value += text[i]
                    i += 1

                if value in self.keywords:
                    code, desc = self.keywords[value]
                    tokens.append(Token(code, desc, value, start_line, start_pos, start_pos + len(value) - 1))
                else:
                    tokens.append(Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))
                filtered_text += value
                continue

            # Числа (целые и с плавающей точкой)
            if ch.isdigit():
                start_line = line
                start_pos = pos
                value = ""
                is_float = False

                while i < n and (text[i].isdigit() or text[i] == '.'):
                    if text[i] == '.':
                        if is_float:
                            break
                        is_float = True
                    value += text[i]
                    i += 1

                if is_float:
                    tokens.append(Token(52, "число с плавающей точкой", value, start_line, start_pos, start_pos + len(value) - 1))
                else:
                    tokens.append(Token(22, "целое число", value, start_line, start_pos, start_pos + len(value) - 1))
                filtered_text += value
                continue

            # Двухсимвольные операторы
            if i + 1 < n and text[i:i+2] in self.two_char_operators:
                two_chars = text[i:i+2]
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

            if ch == '!':
                if i + 1 < n and text[i+1] == '=':
                    two_chars = text[i:i+2]
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
                if i + 1 < n and text[i+1] == '&':
                    two_chars = text[i:i+2]
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
                    i += 1
                continue

            if ch == '|':
                if i + 1 < n and text[i+1] == '|':
                    two_chars = text[i:i+2]
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
            i += 1

        return tokens, errors, filtered_text