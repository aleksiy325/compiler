from lark import Lark, Transformer, UnexpectedCharacters

CHECK_GRAMMAR = 'check_lang/check_grammar.lark'


class TestFail(Exception):
    pass


class Phase():
    def __init__(self, name, statements):
        self.name = name
        self.statements = statements

    def __str__(self):
        return "{} {}".format(self.name, self.statements)


class Error():
    def __init__(self, contains):
        self.contains = contains
        self.line = None
        self.char = None

    def __str__(self):
        return "Err contains:{} line:{} char:{}".format(self.contains, self.line, self.char)


class Output():
    def __init__(self, expected):
        self.expected = expected

    def __str__(self):
        return "Output expected: {}".format(self.expected)


class TestASTBuilder(Transformer):
    def __init__(self):
        super(TestASTBuilder, self).__init__()

    def phase(self, args):
        phase = Phase(args[0], args[1:])
        return phase

    def phase_name(self, args):
        return str(args[0])

    def statement(self, args):
        return args[0]

    def error_statement(self, args):
        err = Error(str(args[0]))
        for arg in args[1:]:
            if arg[0] == 'line':
                err.line = arg[1]
            if arg[0] == 'char':
                err.char = arg[1]
        return err

    def output_statement(self, args):
        return Output(*args)

    def line_n(self, args):
        return ('line', int(str(*args)))

    def char_n(self, args):
        return ('char', int(str(*args)))

    def string(self, args):
        return str(*args)[1:-1]


def parse_check(program):
    with open(CHECK_GRAMMAR) as f:
        grammar = f.read()
    parser = Lark(grammar, start='start')
    tree = parser.parse(program)
    new_tree = TestASTBuilder().transform(tree)
    phases = {}
    for phase in new_tree.children:
        phases[phase.name] = phase
    return phases
