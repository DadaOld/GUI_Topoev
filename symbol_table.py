# symbol_table.py - с поддержкой всех типов

from typing import Dict, Optional, Any, List


class Symbol:
    def __init__(self, name: str, var_type: str, line: int, pos: int, value: Any = None):
        self.name = name
        self.var_type = var_type
        self.line = line
        self.pos = pos
        self.value = value
        self.initialized = value is not None


class SemanticError:
    def __init__(self, line: int, pos: int, fragment: str, message: str):
        self.line = line
        self.pos = pos
        self.fragment = fragment
        self.message = message


class SymbolTable:
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.errors: List[SemanticError] = []

    def clear(self):
        self.symbols.clear()
        self.errors.clear()

    def declare(self, name: str, var_type: str, line: int, pos: int, value: Any = None) -> bool:
        if name in self.symbols:
            existing = self.symbols[name]
            self.errors.append(SemanticError(
                line, pos, name,
                f"Ошибка: переменная '{name}' уже объявлена (строка {existing.line})"
            ))
            return False

        self.symbols[name] = Symbol(name, var_type, line, pos, value)
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def check_used_before_declaration(self, name: str, line: int, pos: int) -> bool:
        if name not in self.symbols:
            self.errors.append(SemanticError(
                line, pos, name,
                f"Ошибка: переменная '{name}' не объявлена"
            ))
            return False
        return True

    def check_type_compatible(self, expected_type: str, actual_node, line: int, pos: int) -> bool:
        from ast_nodes import Num, Bool, Var, Str

        actual_type = None

        if isinstance(actual_node, Num):
            if '.' in actual_node.value:
                actual_type = "double"
            else:
                actual_type = "int"
        elif isinstance(actual_node, Bool):
            actual_type = "boolean"
        elif isinstance(actual_node, Str):
            actual_type = "String"
        elif isinstance(actual_node, Var):
            sym = self.lookup(actual_node.name)
            if sym:
                actual_type = sym.var_type
            else:
                self.errors.append(SemanticError(
                    line, pos, actual_node.name,
                    f"Ошибка: переменная '{actual_node.name}' не объявлена"
                ))
                return False
        else:
            # Неизвестный тип узла
            self.errors.append(SemanticError(
                line, pos, str(actual_node),
                f"Ошибка: неожиданный тип узла"
            ))
            return False

        # Совместимость типов
        if expected_type == "double" and actual_type == "int":
            return True

        if expected_type != actual_type:
            self.errors.append(SemanticError(
                line, pos, str(actual_node.value) if hasattr(actual_node, 'value') else str(actual_node),
                f"Ошибка: несоответствие типов. Ожидается {expected_type}, получено {actual_type}"
            ))
            return False

        return True

    def check_value_range(self, node, var_type: str, line: int, pos: int) -> bool:
        from ast_nodes import Num

        if var_type == "int" and isinstance(node, Num):
            try:
                value = int(node.value)
                if value < -2147483648 or value > 2147483647:
                    self.errors.append(SemanticError(
                        line, pos, node.value,
                        f"Ошибка: число {value} вне диапазона int (-2147483648..2147483647)"
                    ))
                    return False
            except:
                pass

        return True