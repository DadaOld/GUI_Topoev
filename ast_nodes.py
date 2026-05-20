# ast_nodes.py - полная версия с Str

from typing import List, Optional


class ASTNode:
    def __init__(self, line: int, pos: int):
        self.line = line
        self.pos = pos


class Program(ASTNode):
    def __init__(self, line: int = 1, pos: int = 1):
        super().__init__(line, pos)
        self.nodes = []

    def add(self, node):
        self.nodes.append(node)


class Decl(ASTNode):
    def __init__(self, line: int, pos: int, var_type: str, name: str, value: Optional[ASTNode] = None):
        super().__init__(line, pos)
        self.var_type = var_type
        self.name = name
        self.value = value


class If(ASTNode):
    def __init__(self, line: int, pos: int, condition: ASTNode, then_block: 'Block',
                 else_block: Optional['Block'] = None):
        super().__init__(line, pos)
        self.cond = condition
        self.then = then_block
        self.else_ = else_block


class Block(ASTNode):
    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)
        self.stmts = []

    def add(self, stmt):
        self.stmts.append(stmt)


class Assign(ASTNode):
    def __init__(self, line: int, pos: int, left: 'Var', right: ASTNode):
        super().__init__(line, pos)
        self.left = left
        self.right = right


class Var(ASTNode):
    def __init__(self, line: int, pos: int, name: str):
        super().__init__(line, pos)
        self.name = name


class Num(ASTNode):
    def __init__(self, line: int, pos: int, value: str):
        super().__init__(line, pos)
        self.value = value


class Bool(ASTNode):
    def __init__(self, line: int, pos: int, value: bool):
        super().__init__(line, pos)
        self.value = value


class Str(ASTNode):
    def __init__(self, line: int, pos: int, value: str):
        super().__init__(line, pos)
        self.value = value


class Compare(ASTNode):
    def __init__(self, line: int, pos: int, left: ASTNode, op: 'Op', right: ASTNode):
        super().__init__(line, pos)
        self.left = left
        self.op = op
        self.right = right


class Logic(ASTNode):
    def __init__(self, line: int, pos: int, left: ASTNode, op: 'Op', right: ASTNode):
        super().__init__(line, pos)
        self.left = left
        self.op = op
        self.right = right


class Not(ASTNode):
    def __init__(self, line: int, pos: int, expr: ASTNode):
        super().__init__(line, pos)
        self.expr = expr


class Op(ASTNode):
    def __init__(self, line: int, pos: int, value: str):
        super().__init__(line, pos)
        self.value = value


class Paren(ASTNode):
    def __init__(self, line: int, pos: int, expr: ASTNode):
        super().__init__(line, pos)
        self.expr = expr


class ASTPrinter:
    @staticmethod
    def print(node: ASTNode, prefix: str = "", is_last: bool = True) -> str:
        lines = []
        node_name = ASTPrinter._name(node)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{node_name}")
        new_prefix = prefix + ("    " if is_last else "│   ")
        children = ASTPrinter._children(node)
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            lines.append(ASTPrinter.print(child, new_prefix, is_last_child))
        return "\n".join(lines)

    @staticmethod
    def _name(node: ASTNode) -> str:
        if isinstance(node, Program):
            return "Program"
        elif isinstance(node, Decl):
            return f"Decl: {node.var_type} {node.name}"
        elif isinstance(node, If):
            return "If"
        elif isinstance(node, Block):
            return "Block"
        elif isinstance(node, Assign):
            return "Assign"
        elif isinstance(node, Var):
            return f"Var: {node.name}"
        elif isinstance(node, Num):
            return f"Num: {node.value}"
        elif isinstance(node, Bool):
            return f"Bool: {node.value}"
        elif isinstance(node, Str):
            return f"String: {node.value}"
        elif isinstance(node, Compare):
            return f"Compare ({node.op.value})"
        elif isinstance(node, Logic):
            return f"Logic ({node.op.value})"
        elif isinstance(node, Not):
            return "Not"
        elif isinstance(node, Op):
            return f"Op: {node.value}"
        elif isinstance(node, Paren):
            return "Paren"
        return node.__class__.__name__

    @staticmethod
    def _children(node: ASTNode) -> List[ASTNode]:
        children = []
        if isinstance(node, Program):
            children.extend(node.nodes)
        elif isinstance(node, Decl) and node.value:
            children.append(node.value)
        elif isinstance(node, If):
            if node.cond:
                children.append(node.cond)
            if node.then:
                children.append(node.then)
            if node.else_:
                children.append(node.else_)
        elif isinstance(node, Block):
            children.extend(node.stmts)
        elif isinstance(node, Assign):
            if node.left:
                children.append(node.left)
            if node.right:
                children.append(node.right)
        elif isinstance(node, Compare):
            if node.left:
                children.append(node.left)
            if node.op:
                children.append(node.op)
            if node.right:
                children.append(node.right)
        elif isinstance(node, Logic):
            if node.left:
                children.append(node.left)
            if node.op:
                children.append(node.op)
            if node.right:
                children.append(node.right)
        elif isinstance(node, Not) and node.expr:
            children.append(node.expr)
        elif isinstance(node, Paren) and node.expr:
            children.append(node.expr)
        return children