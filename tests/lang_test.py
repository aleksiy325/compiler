from check_lang.lang import parse_check
from compile import lex, generate


def test():
    with open('tests/test.lang') as f:
        program = f.read()
        print(program)
        phases = parse_check(program)

        # lex lang
        ast = lex(program)
