import codecs
from llvmlite import ir, binding
from lang.visitor import Visitor
from lang.ir_env import IREnvironment
from lang.mangler import FunctionMangler
from lang.intrinsics import Intrinsics
from lang.common import Type


class Generator(Visitor):
    def __init__(self):
        self.env = IREnvironment()
        intrinsics = Intrinsics()
        intrinsics.visit(self)

    def visit_field(self, field):
        raise NotImplementedError

    def visit_struct_init(self, struct_init):
        type_t = self.env.scope.get_type(struct_init.id)
        addr = self.env.builder.alloca(type_t)
        self.env.scope.add_variable(struct_init.id, addr)
        return addr

    def visit_struct(self, struct):
        types = [field.type.visit(self) for field in struct.fields]
        context = ir.global_context
        ir_struct = context.get_identified_type(str(struct.id))
        ir_struct.set_body(*types)
        self.env.scope.add_type(str(struct.id), ir_struct)
        return ir_struct

    def visit_expression_list(self, expr_list):
        raise NotImplementedError

    def visit_function_id(self, func_id):
        raise NotImplementedError

    def visit_arg_list(self, arg_list):
        ret = []
        for type_t, arg_id in arg_list.arglist:
            ret.append((type_t.visit(self), str(arg_id)))
        return ret

    def visit_type_list(self, type_list):
        types = [type_t.visit(self) for type_t in type_list.typelist]
        if not types:
            return [ir.VoidType()]
        return types

    def visit_block(self, block):
        for statement in block.statements:
            statement.visit(self)

    def visit_function(self, function, block_callback=None):
        args = function.arglist.visit(self)
        arg_types, arg_ids = zip(*args)
        ret_types = function.retlist.visit(self)

        name = FunctionMangler.encode(function.id, function.arglist.types())

        # TODO: make multiple returns
        func_type = ir.FunctionType(ret_types[0], arg_types)
        func = ir.Function(self.env.module, func_type, name)

        bb_entry = func.append_basic_block('entry')
        old_builder = self.env.builder
        self.env.builder = ir.IRBuilder(bb_entry)

        self.env.scope.enter_scope()
        for i, arg in enumerate(func.args):
            arg.name = arg_ids[i]
            self.env.scope.add_variable(arg.name, arg)

        if block_callback:
            block_callback(self.env)
        else:
            function.block.visit(self)

        self.env.builder = old_builder
        self.env.scope.exit_scope()
        self.env.scope.add_function(name, func)
        return func

    def visit_function_call(self, func_call):
        args = [expr.visit(self)
                for expr in func_call.expression_list.expressions]

        # TODO: check
        arg_types = []
        for arg in args:
            ir_type = arg.type
            if isinstance(ir_type, ir.PointerType):
                ir_type = ir_type.pointee
            arg_types.append(Type(self.env.scope.get_type_name(ir_type)))

        name = FunctionMangler.encode(func_call.id, arg_types)
        func = self.env.scope.get_function(name)

        # handle dereference references if necessary
        for i, (arg, func_arg) in enumerate(zip(args, func.args)):
            # if deref is of right type
            if isinstance(arg.type, ir.PointerType) and arg.type.pointee == func_arg.type:
                # deref
                deref = self.env.builder.load(arg)
                args[i] = deref

        return self.env.builder.call(func, args)

    def visit_variable_dereference(self, var_deref):
        var_id = str(var_deref.idtok)
        var = self.env.scope.get_variable(var_id)
        if isinstance(var, ir.Argument):
            # if arg dont need to load
            return var
        return self.env.builder.load(var, var_id)

    def visit_variable_declaration(self, var_decl):
        var_id = str(var_decl.var_id)
        init_val = var_decl.expression.visit(self)
        ir_type = init_val.type

        if var_decl.is_ref:
            ir_type = ir.PointerType(init_val.type)

        var_addr = self.env.builder.alloca(ir_type)

        if var_decl.is_ref:
            temp_var_addr = self.env.builder.alloca(init_val.type)
            self.env.builder.store(init_val, temp_var_addr)
            self.env.builder.store(temp_var_addr, var_addr)
        else:
            self.env.builder.store(init_val, var_addr)
        self.env.scope.add_variable(var_id, var_addr)

        # TODO: Redefinitions?
        # TODO: Return val?

    def visit_variable_assignment(self, var_assign):
        var_id = str(var_assign.var_id)
        init_val = var_assign.expression.visit(self)

        var_addr = self.env.scope.get_variable(var_id)

        if isinstance(var_addr, ir.values.Argument) and not isinstance(var_addr.type, ir.PointerType):
            # this is an argument but not reference
            # TODO: check make local copy?
            copy_var_addr = self.env.builder.alloca(var_addr.type)
            self.env.builder.store(init_val, copy_var_addr)
            self.env.scope.add_variable(var_id, copy_var_addr)

        elif isinstance(var_addr.type.pointee, ir.PointerType):
            # is ref
            temp_var_addr = self.env.builder.alloca(init_val.type)
            self.env.builder.store(init_val, temp_var_addr)
            self.env.builder.store(temp_var_addr, var_addr)
        else:
            self.env.builder.store(init_val, var_addr)

    def visit_type(self, type_t):
        ir_type = self.env.scope.get_type(str(type_t.typetok))
        if type_t.is_ref:
            ir_type = ir.PointerType(ir_type)
        return ir_type

    def visit_bool(self, bool_t):
        val = 0
        if bool_t.valtok.value is 'true':
            val = 1
        value = ir.Constant(self.env.scope.get_type('bool'), val)
        return value

    def visit_float(self, float_t):
        value = ir.Constant(
            ir.FloatType(), float(float_t.valtok.value[:-1]))
        return value

    def visit_integer(self, integer_t):
        value = ir.Constant(ir.IntType(64), int(integer_t.valtok.value))
        return value

    def visit_string(self, string_t):
        value = codecs.escape_decode(
            bytes(string_t.valtok.value[1:-1], "utf-8"))[0].decode("utf-8") + '\00'
        string = ir.Constant(ir.ArrayType(ir.IntType(8), len(value)),
                             bytearray(value.encode("utf8")))
        return string

    def visit_return(self, ret):
        # TODO: Multiple RETURNS
        if ret.expression_list.expressions:
            self.env.builder.ret(
                ret.expression_list.expressions[0].visit(self))
        else:
            self.env.builder.ret_void()
