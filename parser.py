from scanner import TokenType, Token

ADDITIVE = (TokenType.PLUS, TokenType.MINUS)
MULTIPLICATIVE = (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD)
OPERAND_START = (TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.LPAREN)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
        self.errors = []
        self.temp_counter = 0
        self.triads = []

    def add_error(self, message: str):
        t = self.current_token
        if t and t.type != TokenType.END:
            self.errors.append(f"строка {t.line}, колонка {t.column}: {message}")
        else:
            self.errors.append(f"ошибка: {message}")

    def advance(self):
        tok = self.current_token
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        return tok

    def new_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def parse_E(self):
        left = self.parse_T()

        while self.current_token:
            ct = self.current_token.type
            if ct in ADDITIVE:
                op_tok = self.advance()
                if (not self.current_token or
                        self.current_token.type == TokenType.END or
                        self.current_token.type == TokenType.RPAREN):
                    self.add_error("ожидался операнд")
                    left = None
                    break
                right = self.parse_T()
                if left is not None and right is not None:
                    tmp = self.new_temp()
                    self.triads.append((op_tok.value, left, right, tmp))
                    left = tmp
                else:
                    left = None
            else:
                break

        return left

    def parse_T(self):
        left = self.parse_F()

        while self.current_token:
            ct = self.current_token.type
            if ct in MULTIPLICATIVE:
                op_tok = self.advance()
                if (not self.current_token or
                        self.current_token.type == TokenType.END or
                        self.current_token.type == TokenType.RPAREN):
                    self.add_error("ожидался операнд")
                    left = None
                    break
                right = self.parse_F()
                if left is not None and right is not None:
                    tmp = self.new_temp()
                    self.triads.append((op_tok.value, left, right, tmp))
                    left = tmp
                else:
                    left = None
            elif ct in OPERAND_START:
                # Два операнда подряд без оператора
                self.add_error("пропущен знак операции")
                self.advance()
                left = None
                break
            else:
                break

        return left

    def parse_F(self):
        if not self.current_token or self.current_token.type == TokenType.END:
            self.add_error("неожиданный конец строки")
            return None

        # ERROR токен - просто пропускаем, НЕ добавляем свою ошибку
        if self.current_token.type == TokenType.ERROR:
            self.advance()
            return None

        if self.current_token.type == TokenType.NUMBER:
            val = self.current_token.value
            self.advance()
            return val

        if self.current_token.type == TokenType.IDENTIFIER:
            val = self.current_token.value
            self.advance()
            return val

        if self.current_token.type == TokenType.LPAREN:
            self.advance()
            val = self.parse_E()
            if self.current_token and self.current_token.type == TokenType.RPAREN:
                self.advance()
            else:
                self.add_error("ожидалась ')'")
            return val

        if self.current_token.type == TokenType.RPAREN:
            self.add_error("лишняя ')'")
            self.advance()
            return None

        if self.current_token.type in ADDITIVE + MULTIPLICATIVE:
            self.add_error("ожидался операнд")
            self.advance()
            if self.current_token and self.current_token.type in OPERAND_START:
                return self.parse_F()
            return None

        self.add_error(f"неожиданный символ '{self.current_token.value}'")
        self.advance()
        return None

    def parse(self):
        self.errors = []
        self.temp_counter = 0
        self.triads = []

        if not self.tokens:
            return False, ["нет токенов для анализа"], [], None

        self.parse_E()

        while self.current_token and self.current_token.type != TokenType.END:
            if self.current_token.type == TokenType.RPAREN:
                self.add_error("лишняя ')'")
                self.advance()
            elif self.current_token.type == TokenType.ERROR:
                # Уже обработали выше, просто пропускаем
                self.advance()
            else:
                self.add_error(f"лишний символ '{self.current_token.value}'")
                self.advance()

        has_errors = len(self.errors) > 0
        return not has_errors, self.errors, ([] if has_errors else self.triads), ""