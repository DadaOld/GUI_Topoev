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
        token = self.current_token()
        if_token_present = True

        # Проверяем, является ли первый токен лексической ошибкой, за которой идёт '('
        if token and token.code == -1:
            next_token = self.tokens[self.position + 1] if self.position + 1 < self.total_tokens else None
            if next_token and next_token.code == self.TOK_LPAREN:
                self.add_error("Ожидается 'if'")
                if_token_present = False
                self.position += 1
                token = self.current_token()
                if token and token.code == self.TOK_ID:
                    self.position += 1
            else:
                self.add_error("Ожидается 'if'")
                if_token_present = False
                self.position += 1
                while self.current_token():
                    t = self.current_token()
                    if t.code == self.TOK_LPAREN:
                        break
                    if t.code in {self.TOK_IF, self.TOK_ELSE, self.TOK_LBRACE, self.TOK_SEMICOLON}:
                        break
                    self.position += 1

        # Проверяем, является ли первый токен числом, за которым идёт '('
        elif token and token.code == self.TOK_NUM:
            next_token = self.tokens[self.position + 1] if self.position + 1 < self.total_tokens else None
            if next_token and next_token.code == self.TOK_LPAREN:
                # Число перед '(' — попытка написать 'if'
                self.add_error("Ожидается 'if'")
                if_token_present = False
                self.position += 1  # пропускаем число
            else:
                self.add_error("Ожидается 'if'")
                if_token_present = False
                self.position += 1
                while self.current_token():
                    t = self.current_token()
                    if t.code == self.TOK_LPAREN:
                        break
                    if t.code in {self.TOK_IF, self.TOK_ELSE, self.TOK_LBRACE, self.TOK_SEMICOLON}:
                        break
                    self.position += 1

        # Проверяем, является ли первый токен идентификатором, за которым идёт '('
        elif token and token.code == self.TOK_ID:
            next_token = self.tokens[self.position + 1] if self.position + 1 < self.total_tokens else None
            if next_token and next_token.code == self.TOK_LPAREN:
                if token.value != 'if':
                    self.add_error("Ожидается 'if'")
                if_token_present = False
                self.position += 1
            elif token.value.startswith('i'):
                self.add_error("Ожидается 'if'")
                if_token_present = False
                while self.current_token():
                    t = self.current_token()
                    if t.code == self.TOK_LPAREN:
                        break
                    if t.code in {self.TOK_IF, self.TOK_ELSE, self.TOK_LBRACE, self.TOK_SEMICOLON}:
                        break
                    self.position += 1
            else:
                self.add_error("Ожидается 'if'")
                if_token_present = False

        elif not self.match(self.TOK_IF):
            if token and token.code in {self.TOK_LPAREN}:
                self.add_error("Ожидается 'if'")
                if_token_present = False
            else:
                self.add_error("Ожидается 'if'")
                tok = self.current_token()
                if not tok:
                    return False
                if tok.code == self.TOK_SEMICOLON:
                    self.position += 1
                    return False
                self.position += 1

        # Проверяем '('
        token = self.current_token()
        if token and token.code == self.TOK_LPAREN:
            self.position += 1
        else:
            if if_token_present or token:
                self.add_error("Ожидается '('")
            self.skip_until({self.TOK_ID, self.TOK_NUM, self.TOK_LPAREN, self.TOK_NOT})

        # <LOGICAL_EXP>
        self.in_error_recovery = False
        self.parse_logical_exp()

        # )
        if not self.in_error_recovery:
            if not self.expect(self.TOK_RPAREN, "Ожидается ')'"):
                self.skip_until({self.TOK_LBRACE, self.TOK_SEMICOLON})
        else:
            self.skip_until({self.TOK_LBRACE, self.TOK_SEMICOLON})
            self.in_error_recovery = False

        # {
        if not self.expect(self.TOK_LBRACE, "Ожидается '{'"):
            self.skip_until({self.TOK_ID, self.TOK_RBRACE})

        # <INSTR> (then)
        self.parse_instr()

        # }
        if not self.expect(self.TOK_RBRACE, "Ожидается '}'"):
            self.skip_until({self.TOK_ELSE, self.TOK_SEMICOLON})

        # Проверяем, что идёт после }
        token = self.current_token()

        # Если сразу '{' без else — ошибка
        if token and token.code == self.TOK_LBRACE:
            self.add_error("Ожидается 'else'")
            self.position += 1
            self.parse_instr()
            self.expect(self.TOK_RBRACE, "Ожидается '}'")
            self.expect(self.TOK_SEMICOLON, "Ожидается ';'")
            return True

        # else
        if token:
            if token.code == self.TOK_ELSE:
                self.position += 1

                has_lbrace = self.match(self.TOK_LBRACE)
                if not has_lbrace:
                    self.add_error("Ожидается '{'")
                    self.skip_until({self.TOK_ID, self.TOK_RBRACE})

                self.parse_instr()

                if has_lbrace:
                    if not self.expect(self.TOK_RBRACE, "Ожидается '}'"):
                        self.skip_until({self.TOK_SEMICOLON})
                else:
                    self.match(self.TOK_RBRACE)

            elif token.code == self.TOK_ID and (token.value.startswith('e') or token.value.startswith('el')):
                self.add_error("Ожидается 'else' или ';'")
                self.position += 1
                self.skip_until({self.TOK_LBRACE, self.TOK_SEMICOLON})
                if self.current_token() and self.current_token().code == self.TOK_LBRACE:
                    self.position += 1
                    self.parse_instr()
                    self.expect(self.TOK_RBRACE, "Ожидается '}'")
            elif token.code == -1:
                self.position += 1
                self.skip_until({self.TOK_LBRACE, self.TOK_SEMICOLON})
                if self.current_token() and self.current_token().code == self.TOK_LBRACE:
                    self.position += 1
                    self.parse_instr()
                    self.expect(self.TOK_RBRACE, "Ожидается '}'")

        # ;
        self.expect(self.TOK_SEMICOLON, "Ожидается ';'")

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