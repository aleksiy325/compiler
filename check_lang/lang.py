from lark import Lark, Transformer, UnexpectedCharacters
import codecs

CHECK_GRAMMAR = 'check_lang/check_grammar.lark'


class Lex():
    def __init__(self, error):
        self.error = error
        self.name = 'lex'

    def __str__(self):
        return "{} {}".format('lex', self.error)


class Execute():
    def __init__(self, output):
        self.output = output
        self.name = 'execute'


class Error():
    def __init__(self, contains):
        self.contains = contains
        self.line = None
        self.col = None

    def __str__(self):
        return "Err contains:{} line:{} col:{}".format(self.contains, self.line, self.col)


class Output():
    def __init__(self, expected):
        self.expected = expected

    def __str__(self):
        return "Output expected: {}".format(self.expected)


class TestASTBuilder(Transformer):
    def __init__(self):
        super(TestASTBuilder, self).__init__()

    def execute_phase(self, args):
        return Execute(*args)

    def lex_phase(self, args):
        return Lex(*args)

    def error(self, args):
        err = Error(str(args[0]))
        for arg in args[1:]:
            if arg[0] == 'line':
                err.line = arg[1]
            if arg[0] == 'col':
                err.col = arg[1]
        return err

    def output(self, args):
        return Output(*args)

    def line_n(self, args):
        return ('line', int(str(*args)))

    def col_n(self, args):
        return ('col', int(str(*args)))

    def string(self, args):
        return codecs.escape_decode(
            bytes(args[0][1:-1], "utf-8"))[0].decode("utf-8")


def parse_check(program):
    with open(CHECK_GRAMMAR) as f:
        grammar = f.read()
    parser = Lark(grammar, start='start')
    tree = parser.parse(program)
    print(tree.pretty())
    new_tree = TestASTBuilder().transform(tree)
    phases = {}

    for phase in new_tree.children:
        phases[phase.name] = phase
    return phases


if __name__ == '__main__':
    with open('tests/test.lang') as f:
        print(parse_check(f.read()))
