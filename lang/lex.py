from lark import Transformer, UnexpectedInput
from lark.lexer import Token
from lang.common import Function, FunctionCall, FunctionId
from lang.common import VariableAssignment, VariableDeclaration, VariableDerefrence, VariableId
from lang.common import ArgList, TypeList, ExpressionList, Block, Return
from lang.common import Integer, Float, Bool, String, Type
from lang.common import Struct, Field, StructInit, DotAccess, IfElse, Access
from lang.generator import Generator


class ASTBuilder(Transformer):
    def __init__(self):
        super(ASTBuilder, self).__init__()

    def access(self, args):
        return Access(*args)

    def if_block(self, args):
        return IfElse(*args)

    def ifelse_block(self, args):
        return IfElse(*args, has_else=True)

    def var_access(self, args):
        assert len(args) == 1
        return args[0]

    def dot_access(self, args):
        return DotAccess(args)

    def struct_init(self, args):
        return StructInit(*args)

    def struct(self, args):
        return Struct(*args)

    def structdef(self, args):
        return args

    def field(self, args):
        return Field(*args)

    def function(self, args):
        return Function(*args)

    def function_id(self, args):
        return FunctionId(*args)

    def variable_id(self, args):
        return VariableId(*args)

    def arglist(self, args):
        return ArgList(args)

    def argpair(self, args):
        return tuple(args)

    def typelist(self, args):
        return TypeList(args)

    def auto_variable_declaration(self, args):
        if len(args) > 2:
            return VariableDeclaration(args[1], args[2], is_ref=True)
        return VariableDeclaration(*args)

    def variable_assignment(self, args):
        return VariableAssignment(*args)

    def variable_deref(self, args):
        return VariableDerefrence(*args)

    def type(self, args):
        if len(args) > 1:
            return Type(args[0], is_ref=True)
        return Type(*args)

    def integer(self, args):
        return Integer(*args)

    def float(self, args):
        return Float(*args)

    def bool(self, args):
        return Bool(*args)

    def string(self, args):
        return String(*args)

    def block(self, args):
        return Block(args)

    def return_statement(self, args):
        if args:
            return Return(*args)
        return Return(ExpressionList([]))

    def statement(self, args):
        assert len(args) == 1
        return args[0]

    def bracket_expression(self, args):
        assert len(args) == 1
        return args[0]

    def expression(self, args):
        assert len(args) == 1
        return args[0]

    def atom(self, args):
        assert len(args) == 1
        return args[0]

    def constant(self, args):
        assert len(args) == 1
        return args[0]

    def expression_list(self, args):
        return ExpressionList(args)

    def unary_function_call(self, args):
        (func_id, expression,) = args
        return FunctionCall(func_id, ExpressionList([expression]))

    def binary_function_call(self, args):
        assert len(args) > 2
        param2 = args.pop()
        func_id = args.pop()
        param = args.pop()
        cur_func = FunctionCall(func_id, ExpressionList([param, param2]))
        while args:
            assert len(args) >= 2
            func_id = args.pop()
            param = args.pop()
            cur_func = FunctionCall(func_id, ExpressionList([param, cur_func]))
        return cur_func

    def function_call(self, args):
        return FunctionCall(*args)
