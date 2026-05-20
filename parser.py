# parser.py - синтаксический анализатор с построением AST

from typing import List, Optional, Tuple
from ast_nodes import (
    ASTNode, ProgramNode, IfNode, BlockNode, AssignmentNode,
    IdentifierNode, NumberNode, LogicalExpNode, CompareExpNode,
    CompareOpNode, LogicalOpNode, NotOpNode, ParenExpNode, ASTPrinter
)


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
        self.in_error_recovery = False

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

    # <START> -> <IF_construction>
    def parse_start(self) -> ProgramNode:
        program = ProgramNode()

        if self.parsing_stopped:
            return program

        if_node = self.parse_if_construction()
        if if_node:
            program.add_child(if_node)

        # Проверяем завершающий ';' (уже обработано в parse_if_construction)
        return program

    # <IF_construction> -> if ( <LOGICAL_EXP> ) { <INSTR> } else { <INSTR> } ;
    def parse_if_construction(self) -> Optional[IfNode]:
        if self.parsing_stopped:
            return None

        tok = self.current()

        # Сохраняем позицию для узла
        start_line = 1
        start_pos = 1
        if tok:
            start_line = tok.line
            start_pos = tok.start_pos

        # СЛУЧАЙ 1: программа пуста
        if not tok:
            self.add_error("Ожидается 'if'")
            self.parsing_stopped = True
            return None

        # СЛУЧАЙ 2: '(' или ';'
        if tok.code in {self.TOK_LPAREN, self.TOK_SEMICOLON}:
            self.add_error("Ожидается 'if'")
            self.parsing_stopped = True
            return None

        # СЛУЧАЙ 3: число
        if tok.code == self.TOK_NUM:
            self.add_error("Ожидается 'if'")
            while self.current():
                self.advance()
                if self.current() and self.current().code == self.TOK_LPAREN:
                    break
                if self.current() and self.current().code in {self.TOK_LBRACE, self.TOK_SEMICOLON, self.TOK_IF}:
                    break

        # СЛУЧАЙ 4: идентификатор
        if tok.code == self.TOK_ID:
            self.add_error("Ожидается 'if'")
            while self.current():
                self.advance()
                if self.current() and self.current().code == self.TOK_LPAREN:
                    break
                if self.current() and self.current().code in {self.TOK_LBRACE, self.TOK_SEMICOLON, self.TOK_IF}:
                    break
            else:
                self.add_error("Ожидается 'if'")
                self.parsing_stopped = True
                return None

        # Корректный 'if'
        if self.current() and self.current().code == self.TOK_IF:
            self.advance()

        # Проверяем '('
        if self.current() and self.current().code != self.TOK_LPAREN:
            found_rparen = False
            for i in range(self.position, min(self.total_tokens, self.position + 5)):
                if i < self.total_tokens and self.tokens[i].code == self.TOK_RPAREN:
                    found_rparen = True
                    break
                if i < self.total_tokens and self.tokens[i].code in {self.TOK_LBRACE, self.TOK_SEMICOLON}:
                    break

            if found_rparen:
                self.add_error("Ожидается '('")
            else:
                if not self.expect(self.TOK_LPAREN, "Ожидается '('"):
                    self.skip_to({self.TOK_ID, self.TOK_NUM, self.TOK_NOT, self.TOK_RPAREN, self.TOK_LBRACE})
        else:
            self.match(self.TOK_LPAREN)

        # Парсим условие
        condition = self.parse_logical_exp()
        if not condition:
            condition = IdentifierNode(start_line, start_pos, "unknown")

        # Проверяем ')'
        if self.current() and self.current().code == self.TOK_RPAREN:
            self.advance()
            if self.current() and self.current().code == self.TOK_RPAREN:
                self.add_error("Лишняя ')'")
                self.advance()
        else:
            self.add_error("Ожидается ')'")
            self.skip_to({self.TOK_LBRACE, self.TOK_SEMICOLON})
            self.match(self.TOK_LBRACE)

        # Парсим then-блок
        then_block = self.parse_block()

        # Парсим else-часть
        else_block = None
        tok = self.current()
        has_else = False

        if tok and tok.code == self.TOK_ID:
            self.add_error("Ожидается 'else'")
            while self.current():
                self.advance()
                if self.current() and self.current().code == self.TOK_LBRACE:
                    break
                if self.current() and self.current().code in {self.TOK_SEMICOLON, self.TOK_RBRACE}:
                    break
            has_else = True
        elif tok and tok.code == self.TOK_ELSE:
            self.advance()
            has_else = True

        if has_else:
            else_block = self.parse_block()
        elif tok and tok.code not in {self.TOK_ID, self.TOK_ELSE}:
            self.add_error("Ожидается 'else'")

        # Проверяем завершающую ';'
        if self.current() and self.current().code == self.TOK_SEMICOLON:
            self.advance()
        elif self.current():
            self.add_error("Ожидается ';'")
        elif then_block:
            self.add_error("Ожидается ';'")

        return IfNode(start_line, start_pos, condition, then_block, else_block)

    # <LOGICAL_EXP> -> <COMPARE_EXP> <LOGICAL_EXP_TAIL>
    def parse_logical_exp(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        left = self.parse_compare_exp()
        if not left:
            return None

        # Обрабатываем хвост (логические операторы)
        while self.current() and self.current().code in self.LOGICAL_OPS:
            op_token = self.current()
            op_node = LogicalOpNode(op_token.line, op_token.start_pos, op_token.value)
            self.advance()

            right = self.parse_compare_exp()
            if right:
                left = LogicalExpNode(op_token.line, op_token.start_pos, left, op_node, right)
            else:
                self.add_error("Ожидается выражение после логического оператора")
                break

        return left

    # <LOGICAL_EXP_TAIL> -> <LOGICAL_OP> <COMPARE_EXP> <LOGICAL_EXP_TAIL> | eps
    def parse_logical_exp_tail(self):
        # Этот метод больше не нужен, логика перенесена в parse_logical_exp
        pass

    # <COMPARE_EXP> -> <NOT_OP> <COMPARE_EXP> | ( <LOGICAL_EXP> ) | <EXP>
    def parse_compare_exp(self) -> Optional[ASTNode]:
        if self.parsing_stopped:
            return None

        tok = self.current()
        if not tok:
            return None

        # Обработка отрицания
        if tok.code == self.TOK_NOT:
            not_line = tok.line
            not_pos = tok.start_pos
            self.advance()
            expr = self.parse_compare_exp()
            return NotOpNode(not_line, not_pos, expr)

        # Обработка скобок
        if tok.code == self.TOK_LPAREN:
            self.advance()
            expr = self.parse_logical_exp()
            if not self.expect(self.TOK_RPAREN, "Ожидается ')'"):
                self.skip_to({self.TOK_LBRACE, self.TOK_SEMICOLON, self.TOK_RPAREN})
            return ParenExpNode(tok.line, tok.start_pos, expr)

        # Обработка простого выражения сравнения
        return self.parse_exp()

    # <EXP> -> <id> <COMPARE> <id> | <id> <COMPARE> <num> | <num> <COMPARE> <id>
    def parse_exp(self) -> Optional[CompareExpNode]:
        if self.parsing_stopped:
            return None

        start_tok = self.current()
        if not start_tok:
            return None

        # Парсим левый операнд
        left = self._parse_primary()
        if not left:
            if start_tok.code == self.TOK_RPAREN:
                self.add_error("Ожидается выражение")
            else:
                self.add_error("Ожидается идентификатор или число")
            return None

        # Проверяем оператор сравнения
        if not self.current() or self.current().code not in self.COMPARE_OPS:
            if self.current() and self.current().code == self.TOK_RPAREN:
                self.add_error("Ожидается оператор сравнения")
                self.add_error("Ожидается идентификатор или число")
            else:
                self.add_error("Ожидается оператор сравнения")
                self.skip_to({self.TOK_RPAREN, self.TOK_LBRACE, self.TOK_SEMICOLON})
            return None

        op_token = self.current()
        op_node = CompareOpNode(op_token.line, op_token.start_pos, op_token.value)
        self.advance()

        # Парсим правый операнд
        right = self._parse_primary()
        if not right:
            self.add_error("Ожидается идентификатор или число")
            return None

        # Проверка: сравнение двух чисел недопустимо
        if isinstance(left, NumberNode) and isinstance(right, NumberNode):
            self.add_error("Сравнение двух чисел недопустимо")

        return CompareExpNode(start_tok.line, start_tok.start_pos, left, op_node, right)

    def _parse_primary(self) -> Optional[ASTNode]:
        """Парсит идентификатор или число"""
        tok = self.current()
        if not tok:
            return None

        if tok.code == self.TOK_ID:
            node = IdentifierNode(tok.line, tok.start_pos, tok.value)
            self.advance()
            return node

        if tok.code == self.TOK_NUM:
            node = NumberNode(tok.line, tok.start_pos, tok.value)
            self.advance()
            return node

        return None

    # <INSTR> -> <id> = <id> ; | <id> = <num> ;
    def parse_instr(self) -> Optional[AssignmentNode]:
        if self.parsing_stopped:
            return None

        start_tok = self.current()
        if not start_tok or start_tok.code == self.TOK_RBRACE:
            self.add_error("Ожидается инструкция присваивания")
            return None

        if start_tok.code != self.TOK_ID:
            self.add_error("Ожидается идентификатор")
            self.skip_to({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()
            return None

        left = IdentifierNode(start_tok.line, start_tok.start_pos, start_tok.value)
        self.advance()

        # Проверяем, не идёт ли сразу другой ID или NUM
        if self.current() and self.current().code in {self.TOK_ID, self.TOK_NUM}:
            self.add_error("Ожидается '='")
            self.skip_to({self.TOK_SEMICOLON, self.TOK_RBRACE})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()
            return None

        # Проверяем '='
        if not self.match(self.TOK_ASSIGN):
            self.add_error("Ожидается '='")
            return None

        # Парсим правую часть
        right = self._parse_primary()
        if not right:
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.add_error("Ожидается значение")
            elif self.current() and self.current().code == self.TOK_RBRACE:
                self.add_error("Ожидается значение")
                self.add_error("Ожидается ';'")
            else:
                self.add_error("Ожидается значение")
            return None

        # Проверяем ';'
        if not self.match(self.TOK_SEMICOLON):
            self.add_error("Ожидается ';'")
            self.skip_to({self.TOK_RBRACE, self.TOK_SEMICOLON})
            if self.current() and self.current().code == self.TOK_SEMICOLON:
                self.advance()

        return AssignmentNode(start_tok.line, start_tok.start_pos, left, right)

    # Парсит блок { <INSTR> }
    def parse_block(self) -> Optional[BlockNode]:
        start_tok = self.current()
        if not start_tok:
            return None

        # Проверяем '{'
        if not self.match(self.TOK_LBRACE):
            self.add_error("Ожидается '{'")
            self.skip_to({self.TOK_RBRACE, self.TOK_ELSE})
            if self.current() and self.current().code == self.TOK_RBRACE:
                self.advance()
            return None

        block = BlockNode(start_tok.line, start_tok.start_pos)

        # Парсим инструкции внутри блока (может быть несколько)
        while self.current() and self.current().code != self.TOK_RBRACE:
            instr = self.parse_instr()
            if instr:
                block.add_instruction(instr)

        # Проверяем '}'
        if not self.match(self.TOK_RBRACE):
            self.add_error("Ожидается '}'")
            self.skip_to({self.TOK_ELSE, self.TOK_SEMICOLON})

        return block

    def parse(self) -> Tuple[bool, List[ParseError], Optional[ProgramNode]]:
        if not self.tokens and not self.has_lexical_errors:
            return True, [], ProgramNode()

        ast = self.parse_start()
        success = len(self.errors) == 0 and not self.has_lexical_errors
        return success, self.errors, ast


def parse_tokens(tokens, has_lexical_errors=False):
    """Основная функция для запуска парсера"""
    parser = Parser(tokens, has_lexical_errors)
    return parser.parse()