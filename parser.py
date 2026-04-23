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
    TOK_LPAREN = 15
    TOK_RPAREN = 16
    TOK_LBRACE = 17
    TOK_RBRACE = 18
    TOK_SEMICOLON = 19
    TOK_NUM = 22
    TOK_AND = 23
    TOK_OR = 24
    TOK_NOT = 25

    COMPARE_OPS = {TOK_GT, TOK_LT, TOK_GE, TOK_LE, TOK_EQ, TOK_NE}
    LOGICAL_OPS = {TOK_AND, TOK_OR}
    NOT_OPS = {TOK_NOT}
    SYNC_TOKENS = {TOK_IF, TOK_ELSE, TOK_LBRACE, TOK_RBRACE, TOK_SEMICOLON, TOK_RPAREN}

    def __init__(self, tokens, has_lexical_errors=False):
        self.tokens = tokens
        self.position = 0
        self.errors = []
        self.total_tokens = len(tokens)
        self.has_lexical_errors = has_lexical_errors
        self.in_error_recovery = False

    def current_token(self):
        if self.position < self.total_tokens:
            return self.tokens[self.position]
        return None

    def prev_token(self):
        if self.position > 0 and self.position - 1 < self.total_tokens:
            return self.tokens[self.position - 1]
        return None

    def get_token_line(self):
        token = self.current_token()
        if token:
            return token.line
        prev = self.prev_token()
        if prev:
            return prev.line
        return 1

    def get_token_pos(self):
        token = self.current_token()
        prev = self.prev_token()
        if prev:
            return prev.end_pos + 1
        elif token:
            return token.start_pos
        else:
            return 1

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

    def parse_start(self):
        return self.parse_if_construction()

    def parse_if_construction(self):
        # === 1. Ключевое слово if ===
        if not self.match(self.TOK_IF):
            self.add_error("Ожидается 'if'")
            # Восстановление: ищем '(', '{' или идентификатор
            self.skip_until({self.TOK_LPAREN, self.TOK_LBRACE, self.TOK_ID})
            if not self.current_token():
                return False

        # === 2. Открывающая скобка ( ===
        if not self.match(self.TOK_LPAREN):
            self.add_error("Ожидается '('")
            # Восстановление: ищем начало выражения или '{'
            self.skip_until({self.TOK_ID, self.TOK_NUM, self.TOK_NOT, self.TOK_LBRACE})
            if not self.current_token():
                return False

        # === 3. Логическое выражение ===
        self.parse_logical_exp()

        # === 4. Закрывающая скобка ) ===
        if not self.match(self.TOK_RPAREN):
            self.add_error("Ожидается ')'")
            # Восстановление: ищем '{'
            self.skip_until({self.TOK_LBRACE})
            if not self.current_token():
                return False

        # === 5. Открывающая фигурная скобка { ===
        if not self.match(self.TOK_LBRACE):
            self.add_error("Ожидается '{'")
            # Восстановление: ищем идентификатор или '}'
            self.skip_until({self.TOK_ID, self.TOK_RBRACE})
            if not self.current_token():
                return False

        # === 6. Инструкция в then-ветке ===
        self.parse_instr()

        # === 7. Закрывающая фигурная скобка } ===
        if not self.match(self.TOK_RBRACE):
            self.add_error("Ожидается '}'")
            # Восстановление: ищем 'else' или ';'
            self.skip_until({self.TOK_ELSE, self.TOK_SEMICOLON})
            # Если нашли 'else' — продолжаем, иначе выходим
            if not self.current_token():
                return False

        # === 8. Ключевое слово else ===
        if not self.match(self.TOK_ELSE):
            self.add_error("Ожидается 'else'")
            # Восстановление: ищем '{' или ';'
            self.skip_until({self.TOK_LBRACE, self.TOK_SEMICOLON})
            if not self.current_token():
                return False
            # Если нашли '{', значит else пропущен, но блок есть — обработаем ниже
            # Если нашли ';', значит конструкция закончена

        # === 9. Открывающая фигурная скобка { для else ===
        if self.current_token() and self.current_token().code == self.TOK_LBRACE:
            self.match(self.TOK_LBRACE)  # потребляем '{', если есть
        else:
            # Если нет '{', но мы не в конце — возможно, пропущена
            if self.current_token() and self.current_token().code != self.TOK_SEMICOLON:
                self.add_error("Ожидается '{'")
                self.skip_until({self.TOK_ID, self.TOK_RBRACE, self.TOK_SEMICOLON})

        # === 10. Инструкция в else-ветке (только если мы внутри блока) ===
        if self.current_token() and self.current_token().code == self.TOK_ID:
            self.parse_instr()
        elif self.current_token() and self.current_token().code == self.TOK_RBRACE:
            # Пустой блок — ошибка
            self.add_error("Ожидается инструкция")
            self.match(self.TOK_RBRACE)  # потребляем '}'
        else:
            # Нет инструкции — возможно, конец файла
            pass

        # === 11. Закрывающая фигурная скобка } для else ===
        if self.current_token() and self.current_token().code == self.TOK_RBRACE:
            self.match(self.TOK_RBRACE)
        elif self.current_token() and self.current_token().code != self.TOK_SEMICOLON:
            self.add_error("Ожидается '}'")
            self.skip_until({self.TOK_SEMICOLON})

        # === 12. Точка с запятой ; ===
        if not self.match(self.TOK_SEMICOLON):
            self.add_error("Ожидается ';'")

        return True

    def parse_logical_exp(self):
        if not self.parse_compare_exp():
            return False
        return self.parse_logical_exp_tail()

    def parse_logical_exp_tail(self):
        token = self.current_token()
        if not token or token.code not in self.LOGICAL_OPS:
            return True
        self.position += 1
        if not self.parse_compare_exp():
            self.add_error("Ожидается выражение")
            self.skip_until({self.TOK_RPAREN, self.TOK_LBRACE})
            return False
        return self.parse_logical_exp_tail()

    def parse_compare_exp(self):
        token = self.current_token()
        if not token:
            self.add_error("Неожиданный конец файла")
            return False
        if token.code in self.NOT_OPS:
            self.position += 1
            return self.parse_compare_exp()
        if token.code == self.TOK_LPAREN:
            self.position += 1
            self.parse_logical_exp()
            self.expect(self.TOK_RPAREN, "Ожидается ')'")
            return True
        return self.parse_exp()

    def parse_exp(self):
        token = self.current_token()
        if not token:
            return False

        first_is_id = (token.code == self.TOK_ID)
        first_is_num = (token.code == self.TOK_NUM)

        if not (first_is_id or first_is_num):
            if token.code in self.COMPARE_OPS:
                self.add_error("Ожидается идентификатор или число")
            else:
                self.add_error("Ожидается идентификатор или число")
            self.in_error_recovery = True
            return False

        first_token = token
        self.position += 1

        token = self.current_token()
        if not token or token.code not in self.COMPARE_OPS:
            self.add_error("Ожидается оператор сравнения")
            self.in_error_recovery = True
            return False

        self.position += 1
        token = self.current_token()
        if not token:
            self.add_error("Неожиданный конец файла")
            return False

        second_is_id = (token.code == self.TOK_ID)
        second_is_num = (token.code == self.TOK_NUM)

        if not (second_is_id or second_is_num):
            self.add_error("Ожидается идентификатор или число")
            self.in_error_recovery = True
            return False

        if first_is_num and second_is_num:
            self.add_error("Сравнение чисел недопустимо")

        self.position += 1
        return True

    def parse_instr(self):
        token = self.current_token()
        if not token:
            return False

        if token.code == -1:
            self.skip_until({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current_token() and self.current_token().code == self.TOK_SEMICOLON:
                self.position += 1
            return False

        if token.code != self.TOK_ID:
            self.add_error("Ожидается идентификатор")
            self.skip_until({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current_token() and self.current_token().code == self.TOK_SEMICOLON:
                self.position += 1
            return False

        self.position += 1
        token = self.current_token()
        if not token or token.code != self.TOK_ASSIGN:
            if token and token.code == -1:
                self.position += 1
            self.add_error("Ожидается '='")
            self.skip_until({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current_token() and self.current_token().code == self.TOK_SEMICOLON:
                self.position += 1
            return False

        self.position += 1
        token = self.current_token()
        if not token:
            self.add_error("Ожидается значение")
            return False

        if token.code == -1:
            self.position += 1
            self.skip_until({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current_token() and self.current_token().code == self.TOK_SEMICOLON:
                self.position += 1
            return False

        if token.code in {self.TOK_ID, self.TOK_NUM}:
            self.position += 1
        else:
            self.add_error("Ожидается значение")

        if not self.match(self.TOK_SEMICOLON):
            self.add_error("Ожидается ';'")
            self.skip_until({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current_token() and self.current_token().code == self.TOK_SEMICOLON:
                self.position += 1

        return True

    def parse(self):
        self.parse_start()
        success = (len(self.errors) == 0 and not self.has_lexical_errors)
        return success, self.errors


def parse_tokens(tokens, has_lexical_errors=False):
    parser = Parser(tokens, has_lexical_errors)
    success, errors = parser.parse()
    return success, errors