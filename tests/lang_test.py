from check_lang.lang import parse_check
from compile import lex, generate, GRAMMAR
from lark import UnexpectedCharacters
import pytest


def test():
    with open('tests/test.lang') as f:
        program = f.read()
    with open(GRAMMAR) as f:
        grammar = f.read()

    phases = parse_check(program)

    # lex lang
    if 'lex' in phases:
        lex_phase = phases['lex']
        with pytest.raises(UnexpectedCharacters) as e:
            ast = lex(grammar, program)
        assert lex_phase.error.contains in str(e.value)
        if lex_phase.error.line is not None:
            assert lex_phase.error.line == e.value.line
        if lex_phase.error.col is not None:
            assert lex_phase.error.col == e.value.column

    elif 'execute' in phases:
        ast = lex(program)
