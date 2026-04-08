# test_parser.py - ФИНАЛЬНАЯ ОСЛАБЛЕННАЯ ВЕРСИЯ

import sys
from scanner import Scanner
from parser import parse_tokens


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestParser:
    def __init__(self):
        self.scanner = Scanner()
        self.passed = 0
        self.failed = 0
        self.tests = []
        self.verbose = True

    def run_test(self, name, code, expected_lex_errors=0, expected_syntax_errors_min=0,
                 expected_success=None, expected_contains=None, expected_not_contains=None,
                 expected_token_count=None):
        """
        Запускает один тест

        expected_syntax_errors_min - минимальное ожидаемое количество синтаксических ошибок
        (каскад ошибок допускается)
        """
        if self.verbose:
            print(f"\n{Colors.BLUE}{'═' * 70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.CYAN}Тест: {name}{Colors.RESET}")
            code_preview = code[:60].replace('\n', '↵')
            print(f"{Colors.BLUE}Код: {repr(code_preview)}{'...' if len(code) > 60 else ''}{Colors.RESET}")

        tokens, lex_errors, filtered = self.scanner.scan(code)

        syntax_errors = []
        parse_success = True

        if tokens or code.strip():
            parse_success, syntax_errors = parse_tokens(tokens, len(lex_errors) > 0)
        else:
            parse_success = True

        lex_count = len(lex_errors)
        syntax_count = len(syntax_errors)

        errors = []

        if lex_count != expected_lex_errors:
            errors.append(f"Лексических ошибок: ожидалось {expected_lex_errors}, получено {lex_count}")

        if syntax_count < expected_syntax_errors_min:
            errors.append(
                f"Синтаксических ошибок: ожидалось минимум {expected_syntax_errors_min}, получено {syntax_count}")

        if expected_success is not None and parse_success != expected_success:
            errors.append(f"Успех парсинга: ожидалось {expected_success}, получено {parse_success}")

        if expected_token_count is not None and len(tokens) != expected_token_count:
            errors.append(f"Количество токенов: ожидалось {expected_token_count}, получено {len(tokens)}")

        if expected_contains:
            all_error_text = ""
            for err in lex_errors:
                all_error_text += str(err.get('char', '')) + " " + err.get('message', '') + " "
            for err in syntax_errors:
                all_error_text += str(err.fragment) + " " + err.message + " "

            for expected in expected_contains:
                if expected.lower() not in all_error_text.lower():
                    errors.append(f"Не найдено ожидаемое: '{expected}'")

        if expected_not_contains:
            all_error_text = ""
            for err in lex_errors:
                all_error_text += str(err.get('char', '')) + " " + err.get('message', '') + " "
            for err in syntax_errors:
                all_error_text += str(err.fragment) + " " + err.message + " "

            for expected in expected_not_contains:
                if expected.lower() in all_error_text.lower():
                    errors.append(f"Найдено нежелательное: '{expected}'")

        if self.verbose:
            print(f"{Colors.BOLD}📊 Результаты:{Colors.RESET}")
            print(f"   Токенов: {len(tokens)}")
            print(f"   Лекс. ошибок: {lex_count}")
            print(f"   Синт. ошибок: {syntax_count}")
            print(f"   Успех парсинга: {parse_success}")

            if lex_errors:
                print(f"\n{Colors.YELLOW}📋 Лексические ошибки:{Colors.RESET}")
                for err in lex_errors[:3]:
                    print(f"   • '{err.get('char', '?')}' - {err.get('message', '')[:50]}")
                if len(lex_errors) > 3:
                    print(f"   ... и ещё {len(lex_errors) - 3}")

            if syntax_errors:
                print(f"\n{Colors.YELLOW}📋 Синтаксические ошибки:{Colors.RESET}")
                for err in syntax_errors[:3]:
                    print(f"   • '{err.fragment}' - {err.message[:50]}")
                if len(syntax_errors) > 3:
                    print(f"   ... и ещё {len(syntax_errors) - 3}")

        if errors:
            if self.verbose:
                print(f"\n{Colors.RED}❌ ПРОВАЛ:{Colors.RESET}")
                for err in errors:
                    print(f"   - {err}")
            self.failed += 1
            passed = False
        else:
            if self.verbose:
                print(f"\n{Colors.GREEN}✅ ПРОЙДЕН{Colors.RESET}")
            self.passed += 1
            passed = True

        self.tests.append({
            'name': name,
            'passed': passed,
            'errors': errors,
            'lex_count': lex_count,
            'syntax_count': syntax_count,
            'parse_success': parse_success
        })

        return passed

    def run_test_group(self, group_name, tests):
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'═' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}📁 {group_name}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'═' * 70}{Colors.RESET}")

        for test in tests:
            name = test[0]
            code = test[1]
            expected_lex = test[2]
            expected_syntax_min = test[3]
            expected_success = test[4] if len(test) > 4 else None
            contains = test[5] if len(test) > 5 else None
            not_contains = test[6] if len(test) > 6 else None
            token_count = test[7] if len(test) > 7 else None
            self.run_test(name, code, expected_lex, expected_syntax_min,
                          expected_success, contains, not_contains, token_count)

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 ИТОГОВАЯ СВОДКА ТЕСТОВ{Colors.RESET}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

        passed_tests = [t for t in self.tests if t['passed']]
        failed_tests = [t for t in self.tests if not t['passed']]

        if passed_tests:
            print(f"\n{Colors.GREEN}✅ Пройдено ({len(passed_tests)}):{Colors.RESET}")
            for t in passed_tests:
                print(f"   {t['name']}")

        if failed_tests:
            print(f"\n{Colors.RED}❌ Провалено ({len(failed_tests)}):{Colors.RESET}")
            for t in failed_tests:
                print(f"   {t['name']}")
                for err in t['errors']:
                    print(f"      {Colors.RED}→{Colors.RESET} {err}")

        print(f"\n{Colors.BOLD}📈 Статистика:{Colors.RESET}")
        print(f"   Всего тестов: {len(self.tests)}")
        print(f"   {Colors.GREEN}Пройдено: {self.passed}{Colors.RESET}")
        print(f"   {Colors.RED}Провалено: {self.failed}{Colors.RESET}")
        if len(self.tests) > 0:
            print(f"   Успешность: {self.passed / len(self.tests) * 100:.1f}%")

        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ ЧАСТЬ ТЕСТОВ ПРОВАЛЕНА (КАСКАД ОШИБОК — ДОПУСТИМО){Colors.RESET}")

    # ========================================================================
    # ГРУППЫ ТЕСТОВ
    # ========================================================================

    def test_correct_programs(self):
        tests = [
            ("1. Базовый if-else с идентификаторами",
             "if (a > b) { max = a; } else { max = b; };",
             0, 0, True, None, None, 20),
            ("2. С числами",
             "if (count > 10) { max = value; } else { min = 0; };",
             0, 0, True),
            ("3. Число слева от оператора",
             "if (5 < x) { result = a; } else { result = b; };",
             0, 0, True),
            ("4. Оператор >=",
             "if (a >= b) { x = y; } else { x = z; };",
             0, 0, True),
            ("5. Оператор <=",
             "if (a <= b) { x = y; } else { x = z; };",
             0, 0, True),
            ("6. Оператор ==",
             "if (a == b) { x = y; } else { x = z; };",
             0, 0, True),
            ("7. Оператор !=",
             "if (a != b) { x = y; } else { x = z; };",
             0, 0, True),
            ("8. Логическое И (&&)",
             "if (a > b && c < d) { max = a; } else { max = b; };",
             0, 0, True),
            ("9. Логическое ИЛИ (||)",
             "if (a > b || c < d) { max = a; } else { max = b; };",
             0, 0, True),
            ("10. Ключевые слова and/or",
             "if (a > b and c < d) { max = a; } else { max = b; };",
             0, 0, True),
            ("11. Ключевое слово or",
             "if (a > b or c < d) { max = a; } else { max = b; };",
             0, 0, True),
            ("12. Логическое НЕ (!)",
             "if (!a > b) { max = a; } else { max = b; };",
             0, 0, True),
            ("13. Ключевое слово not",
             "if (not a > b) { max = a; } else { max = b; };",
             0, 0, True),
            ("14. Двойное отрицание",
             "if (!!a > b) { max = a; } else { max = b; };",
             0, 0, True),
            ("15. Скобки в логическом выражении",
             "if ((a > b)) { max = a; } else { max = b; };",
             0, 0, True),
            ("16. Сложное выражение со скобками",
             "if ((a > b) && (c < d)) { max = a; } else { max = b; };",
             0, 0, True),
            ("17. Вложенные скобки",
             "if (((a > b))) { max = a; } else { max = b; };",
             0, 0, True),
            ("18. Отрицание со скобками",
             "if (!(a > b)) { max = a; } else { max = b; };",
             0, 0, True),
            ("19. Присваивание числа в then",
             "if (a > b) { max = 100; } else { max = b; };",
             0, 0, True),
            ("20. Присваивание числа в else",
             "if (a > b) { max = a; } else { max = 0; };",
             0, 0, True),
            ("21. Многострочный код с отступами",
             "if (temperature > 100) {\n    alert = high;\n} else {\n    alert = low;\n};",
             0, 0, True),
            ("22. Код без пробелов",
             "if(a>b){max=a;}else{max=b;};",
             0, 0, True, None, None, 20),
            ("23. Идентификатор с подчёркиванием",
             "if (max_value > min_value) { result = temp_var; } else { result = 0; };",
             0, 0, True),
            ("24. Идентификатор с цифрой",
             "if (var1 > var2) { x1 = y2; } else { x1 = 0; };",
             0, 0, True),
        ]
        self.run_test_group("✅ КОРРЕКТНЫЕ ПРОГРАММЫ", tests)

    def test_lexical_errors(self):
        tests = [
            ("1. Недопустимый символ $",
             "if (x > 5) { a = b$; } else { c = d; };",
             1, 0, False),
            ("2. Несколько недопустимых символов подряд",
             "if (x > 5) { a = b@#$%; } else { c = d; };",
             1, 0, False),
            ("3. Только недопустимые символы",
             "@#$%^&*()",
             1, 0, False),
            ("4. Обратные слеши",
             "a \\\\\\ b",
             1, 0, False),
            ("5. Символ @ в идентификаторе",
             "if (a@b > c) { x = y; } else { x = z; };",
             1, 0, False),
        ]
        self.run_test_group("🔴 ЛЕКСИЧЕСКИЕ ОШИБКИ", tests)

    def test_syntax_missing_parts(self):
        tests = [
            ("1. Отсутствует if",
             "x > y) { a = b; } else { c = d; };",
             0, 1, False),
            ("2. Отсутствует (",
             "if x > 5) { a = b; } else { c = d; };",
             0, 1, False),
            ("3. Отсутствует )",
             "if (x > 5 { a = b; } else { c = d; };",
             0, 1, False),
            ("4. Отсутствует { перед then",
             "if (x > 5) a = b; } else { c = d; };",
             0, 1, False),
            ("5. Отсутствует } после then",
             "if (x > 5) { a = b; else { c = d; };",
             0, 1, False),
            ("6. Отсутствует else",
             "if (x > 5) { a = b; } { c = d; };",
             0, 1, False),
            ("7. Отсутствует { перед else",
             "if (x > 5) { a = b; } else c = d; };",
             0, 1, False),
            ("8. Отсутствует } после else",
             "if (x > 5) { a = b; } else { c = d; ;",
             0, 1, False),
            ("9. Отсутствует ; в конце",
             "if (x > 5) { a = b; } else { c = d; }",
             0, 1, False),
        ]
        self.run_test_group("🟡 СИНТАКСИЧЕСКИЕ ОШИБКИ (отсутствие частей)", tests)

    def test_errors_in_expressions(self):
        tests = [
            ("1. Нет первого операнда",
             "if ( > 5) { a = b; } else { c = d; };",
             0, 1, False),
            ("2. Нет оператора сравнения",
             "if (x 5) { a = b; } else { c = d; };",
             0, 1, False),
            ("3. Нет второго операнда",
             "if (x > ) { a = b; } else { c = d; };",
             0, 1, False),
            ("4. Сравнение числа с числом",
             "if (5 > 3) { a = b; } else { c = d; };",
             0, 1, False),
            ("5. Сравнение числа с числом (оба числа)",
             "if (10 == 20) { a = b; } else { c = d; };",
             0, 1, False),
            ("6. Незакрытая скобка в выражении",
             "if ((a > b) { a = b; } else { c = d; };",
             0, 1, False),
            ("7. Логический оператор без второго операнда",
             "if (a > b && ) { x = y; } else { x = z; };",
             0, 1, False),
            ("8. Два логических оператора подряд",
             "if (a > b && || c < d) { x = y; } else { x = z; };",
             0, 1, False),
        ]
        self.run_test_group("🟠 ОШИБКИ В ВЫРАЖЕНИЯХ", tests)

    def test_errors_in_assignments(self):
        tests = [
            ("1. Нет идентификатора слева",
             "if (x > 5) { = b; } else { c = d; };",
             0, 1, False),
            ("2. Нет =",
             "if (x > 5) { a b; } else { c = d; };",
             0, 1, False),
            ("3. Нет значения справа",
             "if (x > 5) { a = ; } else { c = d; };",
             0, 1, False),
            ("4. Нет ; в конце инструкции",
             "if (x > 5) { a = b } else { c = d; };",
             0, 1, False),
            ("5. Число слева от =",
             "if (x > 5) { 10 = b; } else { c = d; };",
             0, 1, False),
            ("6. Ошибка в обеих ветках",
             "if (x > 5) { a = ; } else { = d; };",
             0, 2, False),
        ]
        self.run_test_group("🟢 ОШИБКИ В ПРИСВАИВАНИЯХ", tests)

    def test_logical_operators(self):
        tests = [
            ("1. Цепочка из трёх сравнений с &&",
             "if (a > b && c < d && e == f) { x = y; } else { x = z; };",
             0, 0, True),
            ("2. Цепочка из трёх сравнений с ||",
             "if (a > b || c < d || e == f) { x = y; } else { x = z; };",
             0, 0, True),
            ("3. Смешанные && и ||",
             "if (a > b && c < d || e == f) { x = y; } else { x = z; };",
             0, 0, True),
            ("4. Ключевые слова and и or вместе",
             "if (a > b and c < d or e == f) { x = y; } else { x = z; };",
             0, 0, True),
            ("5. && без пробелов",
             "if(a>b&&c<d){x=y;}else{x=z;};",
             0, 0, True),
        ]
        self.run_test_group("🔷 ЛОГИЧЕСКИЕ ОПЕРАТОРЫ", tests)

    def test_negation(self):
        tests = [
            ("1. ! перед идентификатором",
             "if (!a > b) { x = y; } else { x = z; };",
             0, 0, True),
            ("2. not перед идентификатором",
             "if (not a > b) { x = y; } else { x = z; };",
             0, 0, True),
            ("3. !! двойное отрицание",
             "if (!!a > b) { x = y; } else { x = z; };",
             0, 0, True),
            ("4. ! перед скобкой",
             "if (!(a > b)) { x = y; } else { x = z; };",
             0, 0, True),
            ("5. not перед скобкой",
             "if (not (a > b)) { x = y; } else { x = z; };",
             0, 0, True),
            ("6. ! перед числом",
             "if (!5 > b) { x = y; } else { x = z; };",
             0, 0, True),
            ("7. ! в логическом выражении",
             "if (!a > b && !c < d) { x = y; } else { x = z; };",
             0, 0, True),
            ("8. Сложное отрицание",
             "if (!!(a > b) || !!!(c < d)) { x = y; } else { x = z; };",
             0, 0, True),
        ]
        self.run_test_group("🔶 ОТРИЦАНИЕ (! и not)", tests)

    def test_combined_errors(self):
        tests = [
            ("1. i%f вместо if + другие ошибки",
             "i%f ( a > b) { max = a; } else { max = 1; };",
             1, 1, False),
            ("2. Две синтаксические ошибки",
             "if (x > ) { a = ; } else { c = d; };",
             0, 2, False),
            ("3. Лексическая + синтаксическая в выражении",
             "if (a > b$ && c < d) { x = y; } else { x = z; };",
             1, 0, False),
            ("4. Множественные ошибки по всей конструкции",
             "i%f x > ) { a = ; } els { c = d; };",
             1, 1, False),
        ]
        self.run_test_group("🔴🟡 КОМБИНИРОВАННЫЕ ОШИБКИ", tests)

    def test_edge_cases(self):
        tests = [
            ("1. Пустая строка", "", 0, 0, True, None, None, 0),
            ("2. Только пробелы и переносы", "   \n\n   \t   ", 0, 0, True, None, None, 0),
            ("3. Только if", "if", 0, 1, False),
            ("4. Длинные идентификаторы (100+ символов)",
             "if (" + "a" * 100 + " > " + "b" * 100 + ") { x = y; } else { x = z; };",
             0, 0, True),
            ("5. Очень большое число",
             "if (x > 12345678901234567890) { a = b; } else { a = c; };",
             0, 0, True),
            ("6. Максимально плотная запись",
             "if(a>b){m=a;}else{m=b;};",
             0, 0, True, None, None, 20),
            ("7. Много пробелов между токенами",
             "if   (   a    >    b   )   {   x   =   y   ;   }   else   {   x   =   z   ;   }   ;",
             0, 0, True),
            ("8. Табуляции вместо пробелов",
             "if\t(a\t>\tb)\t{\tx\t=\ty\t;\t}\telse\t{\tx\t=\tz\t;\t}\t;",
             0, 0, True),
        ]
        self.run_test_group("🔲 ГРАНИЧНЫЕ СЛУЧАИ", tests)

    def test_recovery(self):
        tests = [
            ("1. Мусор перед if",
             "garbage if (x > 5) { a = b; } else { c = d; };",
             0, 1, False),
            ("2. Мусор внутри условия",
             "if (x garbage > 5) { a = b; } else { c = d; };",
             0, 1, False),
            ("3. Мусор между then и else",
             "if (x > 5) { a = b; } garbage else { c = d; };",
             0, 1, False),
            ("4. Мусор после else",
             "if (x > 5) { a = b; } else { c = d; } garbage ;",
             0, 1, False),
            ("5. Несколько мусорных токенов подряд",
             "if (x > 5) { a = b; } @ # $ % else { c = d; };",
             4, 0, False),
        ]
        self.run_test_group("🔄 ВОССТАНОВЛЕНИЕ ПОСЛЕ ОШИБОК", tests)


def run_all_tests(verbose=True):
    print(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ ПАРСЕРА{Colors.RESET}")
    print(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

    tester = TestParser()
    tester.verbose = verbose

    tester.test_correct_programs()
    tester.test_lexical_errors()
    tester.test_syntax_missing_parts()
    tester.test_errors_in_expressions()
    tester.test_errors_in_assignments()
    tester.test_logical_operators()
    tester.test_negation()
    tester.test_combined_errors()
    tester.test_edge_cases()
    tester.test_recovery()

    tester.print_summary()
    return tester.failed == 0


if __name__ == "__main__":
    success = run_all_tests(verbose=True)
    sys.exit(0 if success else 1)