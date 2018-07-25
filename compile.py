from lark import Lark
from lang.lex import ASTBuilder
from lang.generator import Generator

GRAMMAR = 'lang/grammar.lark'


def lex(prog_file):
    try:
        with open(GRAMMAR) as f:
            grammar = f.read()
        with open(prog_file) as f:
            program = f.read()
        parser = Lark(grammar, start='start')
        tree = parser.parse(program)
        print(tree.pretty())
        new_tree = ASTBuilder().transform(tree)
        return new_tree
    except IOError as e:
        print(e)


def generate(tree):
    gen = Generator()
    for child in ast.children:
        child.visit(gen)
    return gen


ast = lex("test")
gen = generate(ast)
gen.env.save_ir('test.ir')
