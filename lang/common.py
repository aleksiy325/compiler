from lark.lexer import Token
from lang.visitor import Visitor, Visitable

INDENT = ' ' * 4


class Access(Visitable):
    def __init__(self, var_id, expr):
        self.var_id = var_id
        self.expr = expr

    def visit(self, visitor: Visitor):
        return visitor.visit_acess(self)

    def __str__(self):
        return '{}[{}]'.format(self.var_id, self.expr)


class IfElse(Visitable):
    def __init__(self, cond_expr, then_block, else_block=None, has_else=False):
        self.cond_expr = cond_expr
        self.then_block = then_block
        self.else_block = else_block
        self.has_else = has_else

    def visit(self, visitor: Visitor):
        return visitor.visit_if_else(self)

    def __str__(self):
        then_block_str = str(self.then_block)
        then_block_str = INDENT + then_block_str.replace('\n', '\n' + INDENT)
        if self.has_else:
            else_block_str = str(self.else_block)
            else_block_str = INDENT + \
                else_block_str.replace('\n', '\n' + INDENT)
            return 'if {} {{\n{} \n}} else {{\n{}\n}}\n'.format(self.cond_expr, then_block_str, else_block_str)
        else:
            return 'if {} {{\n{} \n}}\n'.format(self.cond_expr, then_block_str)


class DotAccess(Visitable):
    def __init__(self, varlist):
        self.varlist = varlist

    def visit(self, visitor: Visitor):
        return visitor.visit_dot_access(self)

    def __str__(self):
        return '.'.join([str(var) for var in self.varlist])


class StructInit(Visitable):
    def __init__(self, idtok, exprlist):
        self.id = idtok
        self.arglist = exprlist

    def visit(self, visitor: Visitor):
        return visitor.visit_struct_init(self)

    def __str__(self):
        return '{}{{ {} }}'.format(str(self.id), self.arglist)


class Field(Visitable):
    def __init__(self, type_t, idtok):
        self.type = type_t
        self.id = idtok

    def visit(self, visitor: Visitor):
        return visitor.visit_field(self)

    def __str__(self):
        return '{} {}'.format(self.type, self.id)


class Struct(Visitable):
    def __init__(self, idtok, fields):
        self.id = idtok
        self.fields = fields

    def visit(self, visitor: Visitor):
        return visitor.visit_struct(self)

    def __str__(self):
        fields = '\n'.join([INDENT + str(field) for field in self.fields])
        return 'struct {} {{\n{}\n}}\n'.format(self.id, fields)


class ExpressionList(Visitable):
    def __init__(self, expressions):
        self.expressions = expressions

    def visit(self, visitor: Visitor):
        return visitor.visit_expression_list(self)

    def __str__(self):
        return ', '.join([str(expression) for expression in self.expressions])


class FunctionId(Visitable):
    def __init__(self, idtok):
        self.idtok = idtok

    def visit(self, visitor: Visitor):
        return visitor.visit_function_id(self)

    def __str__(self):
        return str(self.idtok)


class ArgList(Visitable):
    def __init__(self, arglist):
        self.arglist = arglist

    def get(self, i):
        return self.arglist[i]

    def types(self):
        return [pair[0] for pair in self.arglist]

    def visit(self, visitor: Visitor):
        return visitor.visit_arg_list(self)

    def __str__(self):
        return ', '.join([str(stype) + ' ' + str(id) for stype, id in self.arglist])


class TypeList(Visitable):
    def __init__(self, typelist):
        self.typelist = typelist

    def types(self):
        return self.typelist

    def visit(self, visitor: Visitor):
        return visitor.visit_type_list(self)

    def __str__(self):
        return ', '.join([str(stype) for stype in self.typelist])


class Block(Visitable):
    def __init__(self, statements):
        self.statements = statements

    def visit(self, visitor: Visitor):
        return visitor.visit_block(self)

    def __str__(self):
        return '\n'.join([str(statement) for statement in self.statements])


class Function(Visitable):
    def __init__(self, id, arglist, retlist, block, block_callback=None):
        assert type(id) is FunctionId
        assert type(arglist) is ArgList
        assert type(retlist) is TypeList
        assert type(block) is Block
        self.id = id
        self.arglist = arglist
        self.retlist = retlist
        self.block = block
        self.block_callback = block_callback

    def visit(self, visitor: Visitor):
        if self.block_callback:
            return visitor.visit_function(self, block_callback=self.block_callback)
        return visitor.visit_function(self)

    def __str__(self):
        block_str = str(self.block)
        block_str = INDENT + block_str.replace('\n', '\n' + INDENT)
        return 'def {}({}) ({}) {{\n{}\n}} \n'.format(self.id, self.arglist, self.retlist, block_str)


class FunctionCall(Visitable):
    def __init__(self, id: FunctionId, expression_list: ExpressionList):
        self.id = id
        self.expression_list = expression_list

    def visit(self, visitor: Visitor):
        return visitor.visit_function_call(self)

    def __str__(self):
        return '{}({})'.format(self.id, self.expression_list)


class VariableId():
    def __init__(self, idtok):
        assert type(idtok) is Token
        self.idtok = idtok

    def __str__(self):
        return str(self.idtok)


class VariableDerefrence(Visitable):
    def __init__(self, idtok):
        assert type(idtok) is VariableId
        self.idtok = idtok

    def visit(self, visitor: Visitor):
        return visitor.visit_variable_dereference(self)

    def __str__(self):
        return str(self.idtok)


class VariableDeclaration(Visitable):
    def __init__(self, var_id, expression, is_ref=False):
        assert type(var_id) is VariableId
        self.var_id = var_id
        self.expression = expression
        self.is_ref = is_ref

    def visit(self, visitor: Visitor):
        return visitor.visit_variable_declaration(self)

    def __str__(self):
        s = ''
        if self.is_ref:
            s = 'ref '
        s += '{} := {}'.format(self.var_id, self.expression)
        return s


class VariableAssignment(Visitable):
    def __init__(self, var, expression):
        self.var = var
        self.expression = expression

    def visit(self, visitor: Visitor):
        return visitor.visit_variable_assignment(self)

    def __str__(self):
        return '{} = {}'.format(self.var, self.expression)


class Type(Visitable):
    def __init__(self, typetok, is_ref=False):
        assert type(typetok) is Token or type(typetok) is str
        self.typetok = typetok
        self.is_ref = is_ref

    def visit(self, visitor: Visitor):
        return visitor.visit_type(self)

    def __str__(self):
        s = str(self.typetok)
        if self.is_ref:
            s += ' ref'
        return s


class Bool(Visitable):
    def __init__(self, valtok):
        assert type(valtok) is Token
        self.valtok = valtok

    def visit(self, visitor: Visitor):
        return visitor.visit_bool(self)

    def __str__(self):
        return str(self.valtok)


class Float(Visitable):
    def __init__(self, valtok):
        assert type(valtok) is Token
        self.valtok = valtok

    def visit(self, visitor: Visitor):
        return visitor.visit_float(self)

    def __str__(self):
        return str(self.valtok)


class Integer(Visitable):
    def __init__(self, valtok):
        assert type(valtok) is Token
        self.valtok = valtok

    def visit(self, visitor: Visitor):
        return visitor.visit_integer(self)

    def __str__(self):
        return str(self.valtok)


class String(Visitable):
    def __init__(self, valtok):
        assert type(valtok) is Token
        self.valtok = valtok

    def visit(self, visitor: Visitor):
        return visitor.visit_string(self)

    def __str__(self):
        return str(self.valtok)


class Return(Visitable):
    def __init__(self, expression_list):
        self.expression_list = expression_list

    def visit(self, visitor: Visitor):
        return visitor.visit_return(self)

    def __str__(self):
        return 'return ' + str(self.expression_list)
