from enum import Enum
from dataclasses import dataclass
from typing import List


class TokenType(Enum):
    NUMBER = "число"
    IDENTIFIER = "идентификатор"
    PLUS = "плюс"
    MINUS = "минус"
    MULTIPLY = "умножение"
    DIVIDE = "деление"
    MOD = "остаток"
    LPAREN = "левая_скобка"
    RPAREN = "правая_скобка"
    END = "конец"
    ERROR = "ошибка"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return f"{self.type.value}: '{self.value}' [{self.line}:{self.column}]"


class Scanner:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = text[0] if text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        self.pos += 1
        self.column += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_number(self) -> Token:
        start_col = self.column
        num = ""
        while self.current_char and self.current_char.isdigit():
            num += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, num, self.line, start_col)

    def read_identifier(self) -> Token:
        start_col = self.column
        ident = ""
        while self.current_char and (self.current_char.isalnum()):
            ident += self.current_char
            self.advance()
        return Token(TokenType.IDENTIFIER, ident, self.line, start_col)

    def get_next_token(self) -> Token:
        if not self.current_char:
            return Token(TokenType.END, "", self.line, self.column)

        self.skip_whitespace()

        if not self.current_char:
            return Token(TokenType.END, "", self.line, self.column)

        if self.current_char.isdigit():
            return self.read_number()

        if self.current_char.isalpha():
            return self.read_identifier()

        char = self.current_char
        col = self.column
        line = self.line
        self.advance()

        ops = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '%': TokenType.MOD,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
        }
        if char in ops:
            return Token(ops[char], char, line, col)

        return Token(TokenType.ERROR, char, line, col)

    def tokenize(self) -> List[Token]:
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.END:
                break
        return tokens

    def tokenize_with_details(self) -> dict:
        tokens = self.tokenize()
        return {
            "tokens": tokens,
            "has_errors": any(t.type == TokenType.ERROR for t in tokens),
            "errors": [t for t in tokens if t.type == TokenType.ERROR],
            "numbers": [t for t in tokens if t.type == TokenType.NUMBER],
            "identifiers": [t for t in tokens if t.type == TokenType.IDENTIFIER],
            "operators": [t for t in tokens if t.type in (
                TokenType.PLUS, TokenType.MINUS,
                TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD
            )],
        }