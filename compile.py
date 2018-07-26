from lark import Lark
from lang.lex import ASTBuilder
from lang.generator import Generator

GRAMMAR = 'lang/grammar.lark'


def lex(grammar, program):
    parser = Lark(grammar, start='start')
    tree = parser.parse(program)
    print(tree.pretty())
    new_tree = ASTBuilder().transform(tree)
    return new_tree


def generate(tree):
    gen = Generator()
    for child in tree.children:
        child.visit(gen)
    return gen


if __name__ == '__main__':
    with open("test") as f:
        program = f.read()
    with open(GRAMMAR) as f:
        grammar = f.read()

    ast = lex(grammar, program)
    gen = generate(ast)
    gen.env.save_ir('test.ir')
