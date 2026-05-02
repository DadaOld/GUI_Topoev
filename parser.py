class ParseError:
    def __init__(self, line, pos, fragment, message):
        self.line = line
        self.pos = pos
        self.fragment = fragment
        self.message = message

    def to_dict(self):
        return {'line': self.line, 'pos': self.pos, 'fragment': self.fragment, 'message': self.message}


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

    def __init__(self, tokens, has_lexical_errors=False):
        self.tokens = tokens
        self.position = 0
        self.errors = []
        self.total_tokens = len(self.tokens)
        self.has_lexical_errors = has_lexical_errors
        self.parsing_stopped = False

    def current(self):
        if self.position < self.total_tokens:
            return self.tokens[self.position]
        return None

    def advance(self):
        tok = self.current()
        self.position += 1
        return tok

    def match(self, code):
        if self.current() and self.current().code == code:
            self.advance()
            return True
        return False

    def add_error(self, message):
        tok = self.current()
        if tok:
            self.errors.append(ParseError(tok.line, tok.start_pos, tok.value, message))
        else:
            prev = self.tokens[self.position - 1] if self.position > 0 else None
            line = prev.line if prev else 1
            pos = (prev.end_pos + 1) if prev else 1
            self.errors.append(ParseError(line, pos, 'конец файла', message))

    def expect(self, code, message):
        if self.parsing_stopped:
            return False
        if self.match(code):
            return True
        self.add_error(message)
        return False

    def skip_to(self, codes):
        while self.current() and self.current().code not in codes:
            self.advance()
        return self.current() is not None

    # ============================================================
    # <START> -> <IF_construction> <END>
    # ============================================================
    def parse_start(self):
        self.parse_if_construction()

        # Если разбор остановлен — дальше ничего не проверяем
        if self.parsing_stopped:
            return

        # Проверяем завершающий ';'
        if self.total_tokens > 0:
            last = self.tokens[-1]
            if last.code != self.TOK_SEMICOLON:
                self.add_error("Ожидается ';'")

    # ============================================================
    # <IF_construction> -> if ( <LOGICAL_EXP> ) { <INSTR> } else { <INSTR> } ;
    # ============================================================
    def parse_if_construction(self):
        if self.parsing_stopped:
            return

        tok = self.current()

        # ----- СЛУЧАЙ 1: программа пуста -----
        if not tok:
            self.add_error("Ожидается 'if'")
            self.parsing_stopped = True
            return

        # ----- СЛУЧАЙ 2: '(' или ';' -----
        if tok.code in {self.TOK_LPAREN, self.TOK_SEMICOLON}:
            self.add_error("Ожидается 'if'")
            self.parsing_stopped = True
            return

        # ----- СЛУЧАЙ 3: число -----
        if tok.code == self.TOK_NUM:
            self.add_error("Ожидается 'if'")
            self.parsing_stopped = True
            return

        # ----- СЛУЧАЙ 4: идентификатор -----
        if tok.code == self.TOK_ID:
            value = tok.value.lower()
            can_be_if = value.startswith('i') or ('i' in value and 'f' in value)

            if can_be_if:
                self.add_error("Ожидается 'if'")
                # Пропускаем все токены до '('
                while self.current():
                    self.advance()
                    if self.current() and self.current().code == self.TOK_LPAREN:
                        break
                    if self.current() and self.current().code in {self.TOK_LBRACE, self.TOK_SEMICOLON, self.TOK_IF}:
                        break
            else:
                self.add_error("Ожидается 'if'")
                self.parsing_stopped = True
                return

        # ----- Корректный 'if' -----
        if self.current() and self.current().code == self.TOK_IF:
            self.advance()

        # ----- Остальной разбор -----
        if not self.expect(self.TOK_LPAREN, "Ожидается '('"):
            self.skip_to({self.TOK_ID, self.TOK_NUM, self.TOK_NOT, self.TOK_RPAREN, self.TOK_LBRACE})

        self.parse_logical_exp()

        # )
        if self.current() and self.current().code == self.TOK_RPAREN:
            self.advance()
            if self.current() and self.current().code == self.TOK_RPAREN:
                self.add_error("Лишняя ')'")
                self.advance()
            if not self.expect(self.TOK_LBRACE, "Ожидается '{'"):
                self.skip_to({self.TOK_RBRACE, self.TOK_SEMICOLON})
        else:
            self.add_error("Ожидается ')'")
            self.skip_to({self.TOK_LBRACE, self.TOK_SEMICOLON})
            self.match(self.TOK_LBRACE)

        self.parse_instr()

        if not self.expect(self.TOK_RBRACE, "Ожидается '}'"):
            self.skip_to({self.TOK_ELSE, self.TOK_SEMICOLON})

        # else ОБЯЗАТЕЛЕН
        if not self.expect(self.TOK_ELSE, "Ожидается 'else'"):
            self.skip_to({self.TOK_LBRACE, self.TOK_SEMICOLON})
            if self.current() and self.current().code == self.TOK_LBRACE:
                self.advance()
                self.parse_instr()
                self.expect(self.TOK_RBRACE, "Ожидается '}'")
            return

        if not self.expect(self.TOK_LBRACE, "Ожидается '{'"):
            self.skip_to({self.TOK_ID, self.TOK_NUM, self.TOK_RBRACE})

        self.parse_instr()

        if not self.expect(self.TOK_RBRACE, "Ожидается '}'"):
            self.skip_to({self.TOK_SEMICOLON})

    # ============================================================
    # <LOGICAL_EXP> -> <COMPARE_EXP> <LOGICAL_EXP_TAIL>
    # ============================================================
    def parse_logical_exp(self):
        if self.parsing_stopped:
            return
        self.parse_compare_exp()
        self.parse_logical_exp_tail()

    # ============================================================
    # <LOGICAL_EXP_TAIL> -> <LOGICAL_OP> <COMPARE_EXP> <LOGICAL_EXP_TAIL> | eps
    # ============================================================
    def parse_logical_exp_tail(self):
        if self.parsing_stopped:
            return
        if self.current() and self.current().code in self.LOGICAL_OPS:
            self.advance()
            tok = self.current()
            if not tok or tok.code not in {self.TOK_ID, self.TOK_NUM, self.TOK_NOT, self.TOK_LPAREN}:
                self.add_error("Ожидается выражение после логического оператора")
                self.skip_to({self.TOK_RPAREN, self.TOK_LBRACE, self.TOK_SEMICOLON})
                return
            self.parse_compare_exp()
            self.parse_logical_exp_tail()

    # ============================================================
    # <COMPARE_EXP> -> <NOT_OP> <COMPARE_EXP> | ( <LOGICAL_EXP> ) | <EXP>
    # ============================================================
    def parse_compare_exp(self):
        if self.parsing_stopped:
            return
        tok = self.current()
        if not tok:
            self.add_error("Неожиданный конец файла")
            return

        if tok.code == self.TOK_NOT:
            self.advance()
            self.parse_compare_exp()
            return

        if tok.code == self.TOK_LPAREN:
            self.advance()
            self.parse_logical_exp()
            if not self.expect(self.TOK_RPAREN, "Ожидается ')'"):
                self.skip_to({self.TOK_LBRACE, self.TOK_SEMICOLON, self.TOK_RPAREN})
            return

        self.parse_exp()

    # ============================================================
    # <EXP> -> <id> <COMPARE> <id> | <id> <COMPARE> <num> | <num> <COMPARE> <id>
    # ============================================================
    def parse_exp(self):
        if self.parsing_stopped:
            return
        tok = self.current()
        if not tok:
            self.add_error("Неожиданный конец файла")
            return

        if tok.code not in {self.TOK_ID, self.TOK_NUM}:
            self.add_error("Ожидается идентификатор или число")
            return

        first_is_num = (tok.code == self.TOK_NUM)
        self.advance()

        tok = self.current()
        if not tok or tok.code not in self.COMPARE_OPS:
            self.add_error("Ожидается оператор сравнения")
            return

        self.advance()

        tok = self.current()
        if not tok:
            self.add_error("Неожиданный конец файла")
            return

        if tok.code not in {self.TOK_ID, self.TOK_NUM}:
            self.add_error("Ожидается идентификатор или число")
            return

        second_is_num = (tok.code == self.TOK_NUM)

        if first_is_num and second_is_num:
            self.add_error("Сравнение двух чисел недопустимо")

        self.advance()

    # ============================================================
    # <INSTR> -> <id> = <id> ; | <id> = <num> ;
    # ============================================================
    def parse_instr(self):
        if self.parsing_stopped:
            return
        tok = self.current()
        if not tok or tok.code == self.TOK_RBRACE:
            self.add_error("Ожидается инструкция присваивания")
            return

        if tok.code != self.TOK_ID:
            self.add_error("Ожидается идентификатор")
            self.skip_to({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()
            return

        # Пропускаем идентификатор
        id_token = tok
        self.advance()

        # Проверяем, не идёт ли сразу другой ID или NUM (испорченный идентификатор)
        tok = self.current()
        if tok and tok.code in {self.TOK_ID, self.TOK_NUM}:
            self.add_error("Ожидается '='")
            self.skip_to({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()
            return

        # Флаги для отслеживания найденных/отсутствующих частей
        has_assign = False
        has_value = False
        has_semicolon = False

        # Проверяем '='
        tok = self.current()
        if tok and tok.code == self.TOK_ASSIGN:
            self.advance()
            has_assign = True
        else:
            self.add_error("Ожидается '='")

        # Проверяем значение (если был '=' или если продолжаем)
        tok = self.current()
        if tok and tok.code in {self.TOK_ID, self.TOK_NUM}:
            self.advance()
            has_value = True
        elif tok and tok.code == self.TOK_SEMICOLON:
            if has_assign or not has_assign:
                self.add_error("Ожидается значение")
            self.advance()
            return
        elif tok and tok.code == self.TOK_RBRACE:
            self.add_error("Ожидается значение")
            self.add_error("Ожидается ';'")
            return
        else:
            if tok:
                self.add_error("Ожидается значение")
                self.advance()
            else:
                self.add_error("Ожидается значение")
                self.add_error("Ожидается ';'")
                return

        # Проверяем ';'
        tok = self.current()
        if tok and tok.code == self.TOK_SEMICOLON:
            self.advance()
            has_semicolon = True
        else:
            self.add_error("Ожидается ';'")
            self.skip_to({self.TOK_RBRACE, self.TOK_SEMICOLON})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()

    # ============================================================
    def parse(self):
        if not self.tokens and not self.has_lexical_errors:
            return True, []
        self.parse_start()
        success = len(self.errors) == 0 and not self.has_lexical_errors
        return success, self.errors


def parse_tokens(tokens, has_lexical_errors=False):
    parser = Parser(tokens, has_lexical_errors)
    return parser.parse()