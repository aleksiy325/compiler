from lark import Lark
from lex import ASTBuilder
from generator import Generator

try:
    gen = Generator()
    with open("grammar") as f:
        grammar = f.read()
    with open("test") as f:
        program = f.read()
    parser = Lark(grammar, start='start')
    tree = parser.parse(program)
    print(tree.pretty())
    new_tree = ASTBuilder().transform(tree)
    for child in new_tree.children:
        print(child)
        child.visit(gen)
    gen.env.save_ir('test.ir')

except IOError as e:
    print(e)
