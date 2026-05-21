from scanner import TokenType


class RpnConverter:
    @staticmethod
    def get_precedence(op: str) -> int:
        if op in ('*', '/', '%'):
            return 2
        if op in ('+', '-'):
            return 1
        return 0

    @staticmethod
    def infix_to_rpn(tokens):
        output = []
        stack = []
        errors = []

        for token in tokens:
            if token.type in (TokenType.NUMBER, TokenType.IDENTIFIER):
                output.append(token.value)
            elif token.type in (
                TokenType.PLUS, TokenType.MINUS,
                TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD
            ):
                op = token.value
                while (stack and stack[-1] != '(' and
                       RpnConverter.get_precedence(stack[-1]) >= RpnConverter.get_precedence(op)):
                    output.append(stack.pop())
                stack.append(op)
            elif token.type == TokenType.LPAREN:
                stack.append('(')
            elif token.type == TokenType.RPAREN:
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()
                else:
                    errors.append("несогласованная скобка")
            elif token.type == TokenType.ERROR:
                errors.append(f"неизвестный символ '{token.value}'")

        while stack:
            op = stack.pop()
            if op in ('(', ')'):
                errors.append("несогласованные скобки в выражении")
            else:
                output.append(op)

        return output, errors

    @staticmethod
    def infix_to_rpn_with_steps(tokens):
        output = []
        stack = []
        steps = []
        step_num = 1

        for token in tokens:
            if token.type == TokenType.NUMBER:
                output.append(token.value)
                steps.append(f"{step_num}: число '{token.value}' -> выход: {output}, стек: {stack}")
            elif token.type == TokenType.IDENTIFIER:
                output.append(token.value)
                steps.append(f"{step_num}: идентификатор '{token.value}' -> выход: {output}, стек: {stack}")
            elif token.type in (
                TokenType.PLUS, TokenType.MINUS,
                TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD
            ):
                op = token.value
                steps.append(f"{step_num}: оператор '{op}'")
                while (stack and stack[-1] != '(' and
                       RpnConverter.get_precedence(stack[-1]) >= RpnConverter.get_precedence(op)):
                    popped = stack.pop()
                    output.append(popped)
                    steps.append(f"    выталкиваем '{popped}' -> выход: {output}, стек: {stack}")
                stack.append(op)
                steps.append(f"    помещаем '{op}' в стек: {stack}")
            elif token.type == TokenType.LPAREN:
                stack.append('(')
                steps.append(f"{step_num}: '(' -> стек: {stack}")
            elif token.type == TokenType.RPAREN:
                steps.append(f"{step_num}: ')'")
                while stack and stack[-1] != '(':
                    popped = stack.pop()
                    output.append(popped)
                    steps.append(f"    выталкиваем '{popped}' -> выход: {output}, стек: {stack}")
                if stack and stack[-1] == '(':
                    stack.pop()
                    steps.append(f"    удаляем '(' из стека: {stack}")
            step_num += 1

        while stack:
            popped = stack.pop()
            if popped not in ('(', ')'):
                output.append(popped)
                steps.append(f"{step_num}: выталкиваем '{popped}' -> выход: {output}, стек: {stack}")
            step_num += 1

        return steps

    @staticmethod
    def evaluate_rpn(rpn):
        stack = []
        errors = []

        for token in rpn:
            try:
                stack.append(int(token))
                continue
            except ValueError:
                pass

            if token in ('+', '-', '*', '/', '%'):
                if len(stack) < 2:
                    errors.append(f"недостаточно операндов для '{token}'")
                    return None, errors
                b = stack.pop()
                a = stack.pop()
                try:
                    if token == '+':
                        stack.append(a + b)
                    elif token == '-':
                        stack.append(a - b)
                    elif token == '*':
                        stack.append(a * b)
                    elif token == '/':
                        if b == 0:
                            errors.append("деление на ноль")
                            return None, errors
                        stack.append(a // b)
                    elif token == '%':
                        if b == 0:
                            errors.append("деление на ноль в операции %")
                            return None, errors
                        stack.append(a % b)
                except Exception as e:
                    errors.append(f"ошибка вычисления: {e}")
                    return None, errors
            else:
                errors.append(f"неизвестная операция: '{token}'")
                return None, errors

        if len(stack) != 1:
            errors.append("неверное выражение")
            return None, errors

        return stack[0], errors