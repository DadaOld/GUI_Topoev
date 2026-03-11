# scanner.py - ЭТАП 1: Пробелы и базовая структура

class TokenType:
    """Типы лексем с числовыми кодами"""
    # Пробельные символы
    SPACE = 0  # пробел
    TAB = 20  # табуляция
    NEWLINE = 21  # новая строка


# scanner.py - ЭТАП 1: Пробелы
# Просто создай этот файл в той же папке, где лежит main.py

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
    """Лексический анализатор - ЭТАП 1 (только пробелы)"""

    def scan(self, text):
        """
        Принимает текст, возвращает (токены, ошибки)
        На этом этапе распознаем только пробелы, табуляции и переносы строк
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

            if ch == '\n':
                # Новая строка
                tokens.append(Token(21, "новая строка", ch, line, pos, pos))
                line += 1
                line_start = i + 1
                i += 1

            elif ch == ' ':
                # Пробел
                tokens.append(Token(0, "пробел", ch, line, pos, pos))
                i += 1

            elif ch == '\t':
                # Табуляция
                tokens.append(Token(20, "табуляция", ch, line, pos, pos))
                i += 1

            else:
                # Все остальные символы пока игнорируем
                # (на следующих этапах здесь будет анализ)
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