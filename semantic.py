# semantic.py - с поддержкой всех типов

from ast_nodes import *
from symbol_table import SymbolTable, SemanticError


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()

    def analyze(self, ast: Program) -> List[SemanticError]:
        self.symbols.clear()
        self._visit(ast)
        return self.symbols.errors

    def _visit(self, node: ASTNode):
        if isinstance(node, Program):
            for child in node.nodes:
                self._visit(child)

        elif isinstance(node, Decl):
            self._check_decl(node)

        elif isinstance(node, Assign):
            self._check_assign(node)

        elif isinstance(node, If):
            self._visit(node.cond)
            self._visit(node.then)
            if node.else_:
                self._visit(node.else_)

        elif isinstance(node, Block):
            old_symbols = self.symbols.symbols.copy()
            for stmt in node.stmts:
                self._visit(stmt)
            self.symbols.symbols = old_symbols

        elif isinstance(node, Compare):
            self._visit(node.left)
            self._visit(node.right)

        elif isinstance(node, Logic):
            self._visit(node.left)
            self._visit(node.right)

        elif isinstance(node, Not):
            self._visit(node.expr)

        elif isinstance(node, Var):
            self._check_var_used(node)

    def _check_decl(self, node: Decl):
        # Уникальность имени
        if not self.symbols.declare(node.name, node.var_type, node.line, node.pos):
            return

        # Проверка значения
        if node.value:
            # Совместимость типов
            if not self.symbols.check_type_compatible(node.var_type, node.value, node.line, node.pos):
                return

            # Диапазон для int
            if node.var_type == "int":
                self.symbols.check_value_range(node.value, node.var_type, node.line, node.pos)

    def _check_assign(self, node: Assign):
        var_name = node.left.name
        symbol = self.symbols.lookup(var_name)

        if not symbol:
            self.symbols.errors.append(SemanticError(
                node.left.line, node.left.pos, var_name,
                f"Ошибка: переменная '{var_name}' не объявлена"
            ))
            return

        self.symbols.check_type_compatible(symbol.var_type, node.right, node.right.line, node.right.pos)

    def _check_var_used(self, node: Var):
        self.symbols.check_used_before_declaration(node.name, node.line, node.pos)