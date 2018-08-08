import codecs
from lang.scope import Variable
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
            ret.append((type_t.visit(self), str(arg_id), type_t.is_ref))
        return ret

    def visit_type_list(self, type_list):
        types = [(type_t.visit(self), type_t.is_ref)
                 for type_t in type_list.typelist]
        if not types:
            return [(ir.VoidType(), False)]
        return types

    def visit_block(self, block):
        for statement in block.statements:
            statement.visit(self)

    def visit_function(self, function, block_callback=None):
        args = function.arglist.visit(self)
        arg_types, arg_ids, arg_refs = zip(*args)
        ret_types, ret_refs = zip(*function.retlist.visit(self))

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
            arg_addr = self.env.builder.alloca(arg.type, name=arg.name)
            self.env.builder.store(arg, arg_addr)
            self.env.scope.add_variable(arg.name, arg_addr, is_ref=arg_refs[i])

        if block_callback:
            block_callback(self.env)
        else:
            function.block.visit(self)

        self.env.builder = old_builder
        self.env.scope.exit_scope()
        self.env.scope.add_function(name, func, arg_refs, ret_refs)
        return func

    def visit_function_call(self, func_call):
        args = [expr.visit(self)
                for expr in func_call.expression_list.expressions]

        arg_types = []
        for var_arg in args:
            ir_type = var_arg.value.type.pointee
            if var_arg.is_ref:
                ir_type = ir_type.pointee

            arg_types.append(Type(self.env.scope.get_type_name(ir_type)))

        name = FunctionMangler.encode(func_call.id, arg_types)

        function = self.env.scope.get_function(name)
        func = function.func

        for i, (arg, is_ref) in enumerate(zip(args, function.arg_refs)):
            args[i] = self.env.builder.load(arg.value)
            if arg.is_ref and not is_ref:
                args[i] = self.env.builder.load(args[i])

        ret = self.env.builder.call(func, args)
        if not isinstance(func.ftype.return_type, ir.VoidType):
            ret_addr = self.env.builder.alloca(ret.type)
            self.env.builder.store(ret, ret_addr)
            return Variable(ret_addr, is_ref=function.ret_refs[0])

    def visit_variable_dereference(self, var_deref):
        var_id = str(var_deref.idtok)
        return self.env.scope.get_variable(var_id)

    def visit_variable_declaration(self, var_decl):
        var_id = str(var_decl.var_id)
        var = var_decl.expression.visit(self)
        ir_type = var.value.type.pointee
        init_val = var.value

        if var_decl.is_ref and var.is_ref:
            var_addr = self.env.builder.alloca(ir_type, name=var_id)
            addr = self.env.builder.load(var.value)
            self.env.builder.store(addr, var_addr)
            self.env.scope.add_variable(var_id, var_addr, is_ref=True)

        elif var_decl.is_ref:
            var_addr = self.env.builder.alloca(
                ir.PointerType(ir_type), name=var_id)
            temp = self.env.builder.load(init_val)
            temp_var_addr = self.env.builder.alloca(ir_type)
            self.env.builder.store(temp, temp_var_addr)
            self.env.builder.store(temp_var_addr, var_addr)
            self.env.scope.add_variable(var_id, var_addr, is_ref=True)

        else:
            var_addr = self.env.builder.alloca(ir_type, name=var_id)
            temp = self.env.builder.load(init_val)
            self.env.builder.store(temp, var_addr)
            self.env.scope.add_variable(var_id, var_addr)

    def visit_variable_assignment(self, var_assign):
        var_id = str(var_assign.var_id)
        var = self.env.scope.get_variable(var_id)

        init_var = var_assign.expression.visit(self)
        init_val = init_var.value

        if var.is_ref:
            temp = self.env.builder.load(init_val)
            addr = self.env.builder.load(var.value)
            self.env.builder.store(temp, addr)
        else:
            temp = self.env.builder.load(init_val)
            self.env.builder.store(temp, var.value)
            self.env.scope.add_variable(var_id, var.value)

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
        temp_var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, temp_var_addr)
        return Variable(temp_var_addr)

    def visit_float(self, float_t):
        value = ir.Constant(
            ir.FloatType(), float(float_t.valtok.value[:-1]))
        temp_var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, temp_var_addr)
        return Variable(temp_var_addr)

    def visit_integer(self, integer_t):
        value = ir.Constant(ir.IntType(64), int(integer_t.valtok.value))
        temp_var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, temp_var_addr)
        return Variable(temp_var_addr)

    def visit_string(self, string_t):
        value = codecs.escape_decode(
            bytes(string_t.valtok.value[1:-1], "utf-8"))[0].decode("utf-8") + '\00'
        string = ir.Constant(ir.ArrayType(ir.IntType(8), len(value)),
                             bytearray(value.encode("utf8")))
        temp_var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, temp_var_addr)
        return Variable(temp_var_addr)

    def visit_return(self, ret):
        # TODO: Multiple RETURNS
        if ret.expression_list.expressions:
            ret_addr = ret.expression_list.expressions[0].visit(self)
            ret_val = self.env.builder.load(ret_addr.value)
            return self.env.builder.ret(ret_val)
        else:
            self.env.builder.ret_void()
