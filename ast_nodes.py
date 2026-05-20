# ast_nodes.py - классы для абстрактного синтаксического дерева

from typing import List, Optional


class ASTNode:
    """Базовый класс для всех узлов AST"""

    def __init__(self, line: int, pos: int):
        self.line = line
        self.pos = pos

    def __repr__(self):
        return f"{self.__class__.__name__}(line={self.line}, pos={self.pos})"


class ProgramNode(ASTNode):
    """Корневой узел программы"""

    def __init__(self, line: int = 1, pos: int = 1):
        super().__init__(line, pos)
        self.children = []

    def add_child(self, node: ASTNode):
        self.children.append(node)

    def __repr__(self):
        return f"ProgramNode(children={len(self.children)})"


class IfNode(ASTNode):
    """Узел условного оператора if-else"""

    def __init__(self, line: int, pos: int, condition: ASTNode, then_block: 'BlockNode',
                 else_block: Optional['BlockNode'] = None):
        super().__init__(line, pos)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def __repr__(self):
        return f"IfNode(has_else={self.else_block is not None})"


class BlockNode(ASTNode):
    """Узел блока { ... }"""

    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)
        self.instructions = []

    def add_instruction(self, instr: ASTNode):
        self.instructions.append(instr)

    def __repr__(self):
        return f"BlockNode(instructions={len(self.instructions)})"


class AssignmentNode(ASTNode):
    """Узел присваивания id = id; или id = num;"""

    def __init__(self, line: int, pos: int, left: 'IdentifierNode', right: ASTNode):
        super().__init__(line, pos)
        self.left = left
        self.right = right

    def __repr__(self):
        return f"AssignmentNode(left={self.left.name})"


class IdentifierNode(ASTNode):
    """Узел идентификатора"""

    def __init__(self, line: int, pos: int, name: str):
        super().__init__(line, pos)
        self.name = name

    def __repr__(self):
        return f"IdentifierNode({self.name})"


class NumberNode(ASTNode):
    """Узел числового литерала"""

    def __init__(self, line: int, pos: int, value: str):
        super().__init__(line, pos)
        self.value = value

    def __repr__(self):
        return f"NumberNode({self.value})"


class LogicalExpNode(ASTNode):
    """Узел логического выражения"""

    def __init__(self, line: int, pos: int, left: ASTNode, operator: Optional['LogicalOpNode'] = None,
                 right: Optional[ASTNode] = None):
        super().__init__(line, pos)
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        if self.operator:
            return f"LogicalExpNode(op={self.operator.operator})"
        return "LogicalExpNode"


class CompareExpNode(ASTNode):
    """Узел выражения сравнения"""

    def __init__(self, line: int, pos: int, left: ASTNode, operator: 'CompareOpNode', right: ASTNode):
        super().__init__(line, pos)
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"CompareExpNode(op={self.operator.operator})"


class NotOpNode(ASTNode):
    """Узел отрицания (! или not)"""

    def __init__(self, line: int, pos: int, expr: ASTNode):
        super().__init__(line, pos)
        self.expr = expr

    def __repr__(self):
        return "NotOpNode"


class CompareOpNode(ASTNode):
    """Узел оператора сравнения"""

    def __init__(self, line: int, pos: int, operator: str):
        super().__init__(line, pos)
        self.operator = operator

    def __repr__(self):
        return f"CompareOpNode({self.operator})"


class LogicalOpNode(ASTNode):
    """Узел логического оператора"""

    def __init__(self, line: int, pos: int, operator: str):
        super().__init__(line, pos)
        self.operator = operator

    def __repr__(self):
        return f"LogicalOpNode({self.operator})"


class ParenExpNode(ASTNode):
    """Узел выражения в скобках ( ( ... ) )"""

    def __init__(self, line: int, pos: int, expr: ASTNode):
        super().__init__(line, pos)
        self.expr = expr

    def __repr__(self):
        return "ParenExpNode"


class ASTPrinter:
    """Класс для визуализации AST в текстовом виде"""

    @staticmethod
    def print_ast(node: ASTNode, prefix: str = "", is_last: bool = True) -> str:
        """Рекурсивный вывод AST с красивыми отступами"""
        lines = []

        # Определяем имя узла с дополнительной информацией
        node_name = ASTPrinter._get_node_name(node)

        # Добавляем текущий узел
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{node_name}")

        # Обновляем префикс для детей
        new_prefix = prefix + ("    " if is_last else "│   ")

        # Получаем детей узла
        children = ASTPrinter._get_children(node)

        # Рекурсивно выводим детей
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            lines.append(ASTPrinter.print_ast(child, new_prefix, is_last_child))

        return "\n".join(lines)

    @staticmethod
    def _get_node_name(node: ASTNode) -> str:
        """Возвращает имя узла с атрибутами"""
        if isinstance(node, ProgramNode):
            return "Program"

        elif isinstance(node, IfNode):
            return "IfStatement"

        elif isinstance(node, BlockNode):
            return "Block"

        elif isinstance(node, AssignmentNode):
            return "Assignment"

        elif isinstance(node, IdentifierNode):
            return f"Identifier: {node.name}"

        elif isinstance(node, NumberNode):
            return f"Number: {node.value}"

        elif isinstance(node, LogicalExpNode):
            if node.operator:
                return f"LogicalExp ({node.operator.operator})"
            return "LogicalExp"

        elif isinstance(node, CompareExpNode):
            return f"Compare: {node.operator.operator}"

        elif isinstance(node, NotOpNode):
            return "Not"

        elif isinstance(node, CompareOpNode):
            return f"Op: {node.operator}"

        elif isinstance(node, LogicalOpNode):
            return f"Op: {node.operator}"

        elif isinstance(node, ParenExpNode):
            return "Paren"

        return node.__class__.__name__

    @staticmethod
    def _get_children(node: ASTNode) -> List[ASTNode]:
        """Возвращает список дочерних узлов"""
        children = []

        if isinstance(node, ProgramNode):
            children.extend(node.children)

        elif isinstance(node, IfNode):
            if node.condition:
                children.append(node.condition)
            if node.then_block:
                children.append(node.then_block)
            if node.else_block:
                children.append(node.else_block)

        elif isinstance(node, BlockNode):
            children.extend(node.instructions)

        elif isinstance(node, AssignmentNode):
            if node.left:
                children.append(node.left)
            if node.right:
                children.append(node.right)

        elif isinstance(node, LogicalExpNode):
            if node.left:
                children.append(node.left)
            if node.operator:
                children.append(node.operator)
            if node.right:
                children.append(node.right)

        elif isinstance(node, CompareExpNode):
            if node.left:
                children.append(node.left)
            if node.operator:
                children.append(node.operator)
            if node.right:
                children.append(node.right)

        elif isinstance(node, NotOpNode):
            if node.expr:
                children.append(node.expr)

        elif isinstance(node, ParenExpNode):
            if node.expr:
                children.append(node.expr)

        return children