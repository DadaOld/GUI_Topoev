# parser.py - с поддержкой всех типов данных

from typing import List, Optional, Tuple
from ast_nodes import *


class ParseError:
    def __init__(self, line, pos, fragment, message):
        self.line = line
        self.pos = pos
        self.fragment = fragment
        self.message = message


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
    TOK_INT = 30
    TOK_DOUBLE = 31
    TOK_BOOLEAN = 32
    TOK_STRING = 33
    TOK_TRUE = 40
    TOK_FALSE = 41
    TOK_STRING_LIT = 51
    TOK_FLOAT_NUM = 52

    COMPARE_OPS = {TOK_GT, TOK_LT, TOK_GE, TOK_LE, TOK_EQ, TOK_NE}
    LOGICAL_OPS = {TOK_AND, TOK_OR}
    TYPES = {TOK_INT, TOK_DOUBLE, TOK_BOOLEAN, TOK_STRING}

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

    def parse_start(self) -> Program:
        program = Program()

        if self.parsing_stopped:
            return program

        while self.current() and not self.parsing_stopped:
            # Объявление переменной
            if self.current().code in self.TYPES:
                decl = self.parse_decl()
                if decl:
                    program.add(decl)
            # If-конструкция
            elif self.current().code == self.TOK_IF:
                if_node = self.parse_if()
                if if_node:
                    program.add(if_node)
            # Присваивание
            elif self.current().code == self.TOK_ID:
                # Смотрим, что идёт после идентификатора
                if self.position + 1 < self.total_tokens and self.tokens[self.position + 1].code == self.TOK_ASSIGN:
                    assign = self.parse_assign()
                    if assign:
                        program.add(assign)
                else:
                    # Пробуем как if для восстановления
                    if_node = self.parse_if()
                    if if_node:
                        program.add(if_node)
                    else:
                        self.advance()
            else:
                self.advance()

        return program

    def parse_decl(self) -> Optional[Decl]:
        if self.parsing_stopped:
            return None

        start_tok = self.current()
        if not start_tok or start_tok.code not in self.TYPES:
            return None

        # Определяем тип
        if start_tok.code == self.TOK_INT:
            var_type = "int"
        elif start_tok.code == self.TOK_DOUBLE:
            var_type = "double"
        elif start_tok.code == self.TOK_BOOLEAN:
            var_type = "boolean"
        elif start_tok.code == self.TOK_STRING:
            var_type = "String"
        else:
            var_type = "unknown"

        self.advance()

        # Имя переменной
        if not self.current() or self.current().code != self.TOK_ID:
            self.add_error("Ожидается имя переменной")
            return None

        name_tok = self.current()
        name = name_tok.value
        self.advance()

        # Значение (опционально)
        value = None
        if self.current() and self.current().code == self.TOK_ASSIGN:
            self.advance()
            value = self.parse_value()
            if not value:
                self.add_error("Ожидается значение")

        # ';'
        if not self.expect(self.TOK_SEMICOLON, "Ожидается ';'"):
            return None

        return Decl(start_tok.line, start_tok.start_pos, var_type, name, value)

    def parse_value(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        tok = self.current()
        if not tok:
            return None

        if tok.code == self.TOK_NUM:
            self.advance()
            return Num(tok.line, tok.start_pos, tok.value)

        if tok.code == self.TOK_FLOAT_NUM:
            self.advance()
            return Num(tok.line, tok.start_pos, tok.value)

        if tok.code == self.TOK_STRING_LIT:
            self.advance()
            value = tok.value[1:-1]  # Убираем кавычки
            return Str(tok.line, tok.start_pos, value)

        if tok.code == self.TOK_TRUE:
            self.advance()
            return Bool(tok.line, tok.start_pos, True)

        if tok.code == self.TOK_FALSE:
            self.advance()
            return Bool(tok.line, tok.start_pos, False)

        if tok.code == self.TOK_ID:
            var = Var(tok.line, tok.start_pos, tok.value)
            self.advance()
            return var

        return None

    def parse_if(self) -> Optional[If]:
        if self.parsing_stopped:
            return None

        start_line, start_pos = 1, 1
        tok = self.current()
        if tok:
            start_line, start_pos = tok.line, tok.start_pos

        if not tok or tok.code != self.TOK_IF:
            self.add_error("Ожидается 'if'")
            while self.current() and self.current().code != self.TOK_LPAREN:
                self.advance()
            if not self.current():
                self.parsing_stopped = True
                return None
        else:
            self.advance()

        if not self.expect(self.TOK_LPAREN, "Ожидается '('"):
            return None

        condition = self.parse_logic()
        if not condition:
            condition = Var(start_line, start_pos, "unknown")

        if not self.expect(self.TOK_RPAREN, "Ожидается ')'"):
            return None

        then_block = self.parse_block()
        if not then_block:
            return None

        else_block = None
        if self.current() and self.current().code == self.TOK_ELSE:
            self.advance()
            else_block = self.parse_block()

        self.match(self.TOK_SEMICOLON)

        return If(start_line, start_pos, condition, then_block, else_block)

    def parse_block(self) -> Optional[Block]:
        start_tok = self.current()
        if not start_tok:
            return None

        if not self.expect(self.TOK_LBRACE, "Ожидается '{'"):
            return None

        block = Block(start_tok.line, start_tok.start_pos)

        while self.current() and self.current().code != self.TOK_RBRACE:
            if self.current().code == self.TOK_ID:
                assign = self.parse_assign()
                if assign:
                    block.add(assign)
            else:
                break

        if not self.expect(self.TOK_RBRACE, "Ожидается '}'"):
            return None

        return block

    def parse_assign(self) -> Optional[Assign]:
        if self.parsing_stopped:
            return None

        start_tok = self.current()
        if not start_tok or start_tok.code != self.TOK_ID:
            self.add_error("Ожидается идентификатор")
            self.skip_to({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()
            return None

        left = Var(start_tok.line, start_tok.start_pos, start_tok.value)
        self.advance()

        if not self.expect(self.TOK_ASSIGN, "Ожидается '='"):
            return None

        right = self.parse_value()
        if not right:
            self.add_error("Ожидается значение")
            return None

        if not self.expect(self.TOK_SEMICOLON, "Ожидается ';'"):
            return None

        return Assign(start_tok.line, start_tok.start_pos, left, right)

    def parse_logic(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        left = self.parse_compare()
        if not left:
            return None

        while self.current() and self.current().code in self.LOGICAL_OPS:
            op_tok = self.current()
            op = Op(op_tok.line, op_tok.start_pos, op_tok.value)
            self.advance()

            right = self.parse_compare()
            if right:
                left = Logic(op_tok.line, op_tok.start_pos, left, op, right)
            else:
                self.add_error("Ожидается выражение")
                break

        return left

    def parse_compare(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        not_nodes = []
        while self.current() and self.current().code == self.TOK_NOT:
            tok = self.current()
            not_nodes.append(Not(tok.line, tok.start_pos, None))
            self.advance()

        expr = self.parse_atom()
        if not expr:
            return None

        for not_node in reversed(not_nodes):
            not_node.expr = expr
            expr = not_node

        if self.current() and self.current().code in self.COMPARE_OPS:
            op_tok = self.current()
            op = Op(op_tok.line, op_tok.start_pos, op_tok.value)
            self.advance()

            right = self.parse_atom()
            if right:
                expr = Compare(op_tok.line, op_tok.start_pos, expr, op, right)
            else:
                self.add_error("Ожидается выражение")

        return expr

    def parse_atom(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        tok = self.current()
        if not tok:
            return None

        if tok.code == self.TOK_ID:
            self.advance()
            return Var(tok.line, tok.start_pos, tok.value)

        if tok.code == self.TOK_NUM:
            self.advance()
            return Num(tok.line, tok.start_pos, tok.value)

        if tok.code == self.TOK_FLOAT_NUM:
            self.advance()
            return Num(tok.line, tok.start_pos, tok.value)

        if tok.code == self.TOK_STRING_LIT:
            self.advance()
            value = tok.value[1:-1]
            return Str(tok.line, tok.start_pos, value)

        if tok.code == self.TOK_TRUE:
            self.advance()
            return Bool(tok.line, tok.start_pos, True)

        if tok.code == self.TOK_FALSE:
            self.advance()
            return Bool(tok.line, tok.start_pos, False)

        if tok.code == self.TOK_LPAREN:
            self.advance()
            expr = self.parse_logic()
            if not self.expect(self.TOK_RPAREN, "Ожидается ')'"):
                return None
            return Paren(tok.line, tok.start_pos, expr)

        return None

    def parse(self) -> Tuple[bool, List[ParseError], Optional[Program]]:
        if not self.tokens and not self.has_lexical_errors:
            return True, [], Program()

        ast = self.parse_start()
        success = len(self.errors) == 0 and not self.has_lexical_errors
        return success, self.errors, ast


def parse_tokens(tokens, has_lexical_errors=False):
    parser = Parser(tokens, has_lexical_errors)
    return parser.parse()