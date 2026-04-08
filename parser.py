class SyntaxError:
    def __init__(self, line, pos, fragment, message):
        self.line = line
        self.pos = pos
        self.fragment = fragment
        self.message = message

    def to_dict(self):
        return {
            'line': self.line,
            'pos': self.pos,
            'fragment': self.fragment,
            'message': self.message
        }


class Parser:
    # Коды токенов (должны совпадать со scanner.py)
    TOK_IF = 1
    TOK_ELSE = 2
    TOK_ID = 3
    TOK_ASSIGN = 4
    TOK_GT = 5
    TOK_LT = 6
    TOK_GE = 7
    TOK_LE = 8
    TOK_EQ = 9
    TOK_NE = 10
    TOK_PLUS = 11
    TOK_MINUS = 12
    TOK_MUL = 13
    TOK_DIV = 14
    TOK_LPAREN = 15
    TOK_RPAREN = 16
    TOK_LBRACE = 17
    TOK_RBRACE = 18
    TOK_SEMICOLON = 19
    TOK_NUM = 22
    TOK_AND = 23
    TOK_OR = 24
    TOK_NOT = 25

    # Множества для проверок
    COMPARE_OPS = {TOK_GT, TOK_LT, TOK_GE, TOK_LE, TOK_EQ, TOK_NE}
    LOGICAL_OPS = {TOK_AND, TOK_OR}
    NOT_OPS = {TOK_NOT}

    def __init__(self, tokens, has_lexical_errors=False):
        self.tokens = tokens
        self.position = 0
        self.errors = []
        self.total_tokens = len(tokens)
        self.has_lexical_errors = has_lexical_errors

    def current_token(self):
        if self.position < self.total_tokens:
            return self.tokens[self.position]
        return None

    def get_token_line(self):
        token = self.current_token()
        return token.line if token else 1

    def get_token_pos(self):
        token = self.current_token()
        return token.start_pos if token else 1

    def get_token_value(self):
        token = self.current_token()
        return token.value if token else 'конец файла'

    def match(self, expected_code):
        token = self.current_token()
        if token and token.code == expected_code:
            self.position += 1
            return True
        return False

    def add_error(self, message):
        self.errors.append(SyntaxError(
            self.get_token_line(),
            self.get_token_pos(),
            self.get_token_value(),
            message
        ))

    def expect(self, expected_code, message):
        if self.match(expected_code):
            return True
        self.add_error(message)
        return False

    def skip_until(self, stop_codes):
        while self.current_token():
            if self.current_token().code in stop_codes:
                return True
            self.position += 1
        return False

    # === Правила грамматики ===

    def parse_start(self):
        return self.parse_if_construction()

    def parse_if_construction(self):
        # if
        if not self.match(self.TOK_IF):
            self.add_error("Программа должна начинаться с 'if'")
            self.skip_until({self.TOK_IF})
            if not self.current_token():
                return False
            return self.parse_if_construction()

        # (
        if not self.expect(self.TOK_LPAREN, "Ожидается '(' после 'if'"):
            self.skip_until({self.TOK_ID, self.TOK_NUM, self.TOK_LPAREN, self.TOK_NOT})

        # <LOGICAL_EXP>
        self.parse_logical_exp()

        # )
        if not self.expect(self.TOK_RPAREN, "Ожидается ')' после условия"):
            self.skip_until({self.TOK_LBRACE, self.TOK_RPAREN})

        # {
        if not self.expect(self.TOK_LBRACE, "Ожидается '{'"):
            self.skip_until({self.TOK_ID, self.TOK_RBRACE})

        # <INSTR> (then)
        self.parse_instr()

        # }
        if not self.expect(self.TOK_RBRACE, "Ожидается '}' после then-ветки"):
            self.skip_until({self.TOK_ELSE, self.TOK_RBRACE})

        # else
        if not self.expect(self.TOK_ELSE, "Ожидается 'else'"):
            self.skip_until({self.TOK_LBRACE})

        # {
        if not self.expect(self.TOK_LBRACE, "Ожидается '{' после else"):
            self.skip_until({self.TOK_ID, self.TOK_RBRACE})

        # <INSTR> (else)
        self.parse_instr()

        # }
        if not self.expect(self.TOK_RBRACE, "Ожидается '}' после else-ветки"):
            self.skip_until({self.TOK_SEMICOLON})

        # ;
        self.expect(self.TOK_SEMICOLON, "Ожидается ';' в конце конструкции")

        return True

    def parse_logical_exp(self):
        if not self.parse_compare_exp():
            return False
        return self.parse_logical_exp_tail()

    def parse_logical_exp_tail(self):
        token = self.current_token()
        if not token or token.code not in self.LOGICAL_OPS:
            return True  # ε

        self.position += 1

        if not self.parse_compare_exp():
            self.add_error("Ожидается выражение после логического оператора")
            self.skip_until({self.TOK_RPAREN, self.TOK_LBRACE})
            return False

        return self.parse_logical_exp_tail()

    def parse_compare_exp(self):
        token = self.current_token()
        if not token:
            self.add_error("Неожиданный конец файла в выражении")
            return False

        # <NOT_OP>
        if token.code in self.NOT_OPS:
            self.position += 1
            return self.parse_compare_exp()

        # ( <LOGICAL_EXP> )
        if token.code == self.TOK_LPAREN:
            self.position += 1
            self.parse_logical_exp()
            self.expect(self.TOK_RPAREN, "Ожидается ')'")
            return True

        # <EXP>
        return self.parse_exp()

    def parse_exp(self):
        token = self.current_token()
        if not token:
            return False

        first_token = token
        first_is_id = (token.code == self.TOK_ID)
        first_is_num = (token.code == self.TOK_NUM)

        if not (first_is_id or first_is_num):
            self.add_error(f"Ожидается идентификатор или число, получено '{token.value}'")
            self.position += 1
            return False

        self.position += 1

        token = self.current_token()
        if not token or token.code not in self.COMPARE_OPS:
            self.add_error("Ожидается оператор сравнения")
            return False

        compare_op = token
        self.position += 1

        token = self.current_token()
        if not token:
            self.add_error("Неожиданный конец файла")
            return False

        second_is_id = (token.code == self.TOK_ID)
        second_is_num = (token.code == self.TOK_NUM)

        if not (second_is_id or second_is_num):
            self.add_error(f"Ожидается идентификатор или число, получено '{token.value}'")
            self.position += 1
            return False

        if first_is_num and second_is_num:
            self.add_error(f"Недопустимое сравнение числа с числом: '{first_token.value}' и '{token.value}'")

        self.position += 1
        return True

    def parse_instr(self):
        token = self.current_token()
        if not token:
            return False

        if token.code != self.TOK_ID:
            self.add_error(f"Инструкция должна начинаться с идентификатора, получено '{token.value}'")
            return False

        self.position += 1

        if not self.expect(self.TOK_ASSIGN, "Ожидается '=' после идентификатора"):
            return False

        token = self.current_token()
        if not token or token.code not in {self.TOK_ID, self.TOK_NUM}:
            self.add_error("Ожидается идентификатор или число после '='")
            return False

        self.position += 1

        self.expect(self.TOK_SEMICOLON, "Ожидается ';' в конце инструкции")
        return True

    def parse(self):
        self.parse_start()

        # Успех только если нет синтаксических ошибок И не было лексических
        success = (len(self.errors) == 0 and not self.has_lexical_errors)
        return success, self.errors


def parse_tokens(tokens, has_lexical_errors=False):
    parser = Parser(tokens, has_lexical_errors)
    success, errors = parser.parse()
    return success, errors


if __name__ == "__main__":
    from scanner import Scanner

    scanner = Scanner()
    test = "if (a > b) { max = a; } else { max = b; };"
    tokens, lex_errors, filtered = scanner.scan(test)

    print(f"Тест парсера: {test}")
    print(f"Лексических ошибок: {len(lex_errors)}")

    success, errors = parse_tokens(tokens, len(lex_errors) > 0)

    print(f"Успех парсинга: {success}")
    if errors:
        print("Синтаксические ошибки:")
        for e in errors:
            print(f"  строка {e.line}, '{e.fragment}' - {e.message}")