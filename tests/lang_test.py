from check_lang.lang import parse_check
from compile import lex, generate, GRAMMAR
from lark import UnexpectedCharacters
from subprocess import call, check_output
import os
from os.path import basename, splitext, join
import pytest
import glob

CC = 'clang'
LLC = 'llc'
TMP_DIR = 'tmp'
TEST_DIR = 'tests'
EXT = 'lang'

if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)


def list_test_files():
    return glob.glob(join(TEST_DIR, '*.' + EXT))


@pytest.mark.parametrize('test_file', list_test_files())
def test(test_file):
    print(test_file)
    base = basename(test_file)
    name, ext = splitext(base)
    with open(test_file) as f:
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
        ast = lex(grammar, program)
        gen = generate(ast)
        ir_path = join(TMP_DIR, name + '.ir')
        gen.env.save_ir(ir_path)
        call([LLC, '-filetype=obj', ir_path])
        obj_path = ir_path + '.o'
        out_path = join(TMP_DIR, name)
        call([CC, obj_path, '-o', out_path])
        ret = check_output([out_path])
        ret = ret.decode()
        exec_phase = phases['execute']
        assert exec_phase.output.expected == ret
