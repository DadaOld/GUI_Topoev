# scanner.py - ЭТАП 1: Пробелы и базовая структура

class TokenType:
    """Типы лексем с числовыми кодами"""
    # Пробельные символы
    SPACE = 0  # пробел
    TAB = 20  # табуляция
    NEWLINE = 21  # новая строка


# scanner.py - ЭТАП 1: Пробелы
# Просто создай этот файл в той же папке, где лежит main.py

# scanner.py - ЭТАП 2: Идентификаторы и ключевые слова

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
    """Лексический анализатор - ЭТАП 2 (добавлены идентификаторы и ключевые слова)"""

    def __init__(self):
        # Ключевые слова и их коды
        self.keywords = {
            'if': (1, "ключевое слово if"),
            'else': (2, "ключевое слово else")
        }

    def is_letter(self, ch):
        """Проверка, является ли символ буквой или подчеркиванием"""
        return ch.isalpha() or ch == '_'

    def is_letter_or_digit(self, ch):
        """Проверка, является ли символ буквой, цифрой или подчеркиванием"""
        return ch.isalpha() or ch.isdigit() or ch == '_'

    def scan(self, text):
        """
        Принимает текст, возвращает (токены, ошибки)
        На этом этапе распознаем:
        - пробелы (0), табуляции (20), переносы строк (21)
        - ключевые слова if (1) и else (2)
        - идентификаторы (3)
        """
        tokens = []
        errors = []

        i = 0
        line = 1
        line_start = 0
        n = len(text)

        while i < n:
            ch = text[i]
            pos = i - line_start + 1  # позиция в строке (с 1)

            # Обработка пробельных символов
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

            # Обработка идентификаторов и ключевых слов
            elif self.is_letter(ch):
                # Начало идентификатора/ключа
                start_i = i
                start_line = line
                start_pos = pos
                value = ""

                # Считываем все буквы, цифры и подчеркивания
                while i < n and self.is_letter_or_digit(text[i]):
                    value += text[i]
                    i += 1

                # Проверяем, не ключевое ли это слово
                if value in self.keywords:
                    code, desc = self.keywords[value]
                    tokens.append(Token(code, desc, value, start_line, start_pos, start_pos + len(value) - 1))
                else:
                    # Обычный идентификатор
                    tokens.append(Token(3, "идентификатор", value, start_line, start_pos, start_pos + len(value) - 1))

            # Все остальные символы пока игнорируем
            else:
                i += 1

        return tokens, errors


# Для тестирования
if __name__ == "__main__":
    scanner = Scanner()

    # Тест 1: только пробелы
    test1 = " \t \n  \t"
    print("=== Тест 1: только пробелы ===")
    tokens, errors = scanner.scan(test1)
    for t in tokens:
        print(f"  {t.code}: '{t.value}' - {t.type_desc} [строка {t.line}, {t.start_pos}-{t.end_pos}]")

    # Тест 2: текст с пробелами
    test2 = "if (a > b) {\n    max = a;\n}"
    print("\n=== Тест 2: текст с пробелами (остальное игнорируется) ===")
    tokens, errors = scanner.scan(test2)
    for t in tokens:
        print(f"  {t.code}: '{t.value}' - {t.type_desc} [строка {t.line}, {t.start_pos}-{t.end_pos}]")