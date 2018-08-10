import codecs
from lang.scope import MetaVariable, MetaType
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

    def visit_dot_access(self, dot_access):
        first = dot_access.varlist[0]
        meta_var = self.env.scope.get_variable(first)
        type_t = self.env.scope.get_type(meta_var.type_name)

        struct_index = ir.Constant(ir.IntType(32), 0)
        vec = [struct_index]

        for field_name in dot_access.varlist[1:]:
            i = type_t.get_field_offset(str(field_name))
            type_t = type_t.fields[i]
            vec.append(ir.Constant(ir.IntType(32), i))

        # deref if needed
        ir_var = meta_var.ir_value
        if meta_var.is_ref:
            ir_var = self.env.builder.load(meta_var.ir_value)

        ele_addr = self.env.builder.gep(ir_var, vec)
        return MetaVariable(ele_addr, type_t.name)

    def visit_field(self, field):
        raise NotImplementedError

    def visit_struct_init(self, struct_init):
        type_t = self.env.scope.get_type(struct_init.id)
        struct_addr = self.env.builder.alloca(type_t.ir_type)
        variables = struct_init.arglist.visit(self)

        for i, (field_type, var) in enumerate(zip(type_t.fields, variables)):
            struct_index = ir.Constant(ir.IntType(32), 0)
            index = ir.Constant(ir.IntType(32), i)
            ele_addr = self.env.builder.gep(struct_addr, [struct_index, index])

            if field_type.is_ref and var.is_ref:
                val_addr = self.env.builder.load(var.ir_value)
                self.env.builder.store(val_addr, ele_addr)

            elif field_type.is_ref and not var.is_ref:
                temp = self.env.builder.load(var.ir_value)
                temp_var_addr = self.env.builder.alloca(temp.type)
                self.env.builder.store(temp, temp_var_addr)
                self.env.builder.store(temp_var_addr, ele_addr)

            elif not field_type.is_ref and var.is_ref:
                val_addr = self.env.builder.load(var.ir_value)
                val = self.env.builder.load(val_addr)
                self.env.builder.store(val, ele_addr)
            else:
                temp = self.env.builder.load(var.ir_value)
                self.env.builder.store(temp, ele_addr)

        return MetaVariable(struct_addr, str(struct_init.id))

    def visit_struct(self, struct):
        types = [field.type.visit(self) for field in struct.fields]
        field_names = [str(field.id) for field in struct.fields]
        ir_types = [type_t.ir_type for type_t in types]
        context = ir.global_context
        ir_struct = context.get_identified_type(str(struct.id))
        ir_struct.set_body(*ir_types)
        self.env.scope.add_type(str(struct.id), ir_struct,
                                field_names=field_names, fields=types)

    def visit_expression_list(self, expr_list):
        return [expr.visit(self) for expr in expr_list.expressions]

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
            type_t = ir.VoidType()
            type_name = self.env.scope.get_type_name(type_t)
            return [MetaType(type_name, type_t)]
        return types

    def visit_block(self, block):
        for statement in block.statements:
            statement.visit(self)

    def visit_function(self, function, block_callback=None):
        arg_types, arg_ids = zip(*function.arglist.visit(self))
        ret_types = function.retlist.visit(self)

        ret_ir_types = [ret_type.ir_type for ret_type in ret_types]
        arg_ir_types = [arg_type.ir_type for arg_type in arg_types]

        name = FunctionMangler.encode(function.id, function.arglist.types())

        func_type = ir.FunctionType(ret_ir_types[0], arg_ir_types)
        func = ir.Function(self.env.module, func_type, name)

        bb_entry = func.append_basic_block('entry')
        old_builder = self.env.builder
        self.env.builder = ir.IRBuilder(bb_entry)

        self.env.scope.enter_scope()
        for arg, meta_arg, arg_name in zip(func.args, arg_types, arg_ids):
            arg.name = arg_name
            arg_addr = self.env.builder.alloca(arg.type, name=arg_name)
            self.env.builder.store(arg, arg_addr)
            self.env.scope.add_variable(
                arg.name, arg_addr, meta_arg.name, is_ref=meta_arg.is_ref)

        if block_callback:
            block_callback(self.env)
        else:
            function.block.visit(self)

        self.env.builder = old_builder
        self.env.scope.exit_scope()
        self.env.scope.add_function(name, func, arg_types, ret_types)

    def visit_function_call(self, func_call):
        args = [expr.visit(self)
                for expr in func_call.expression_list.expressions]
        arg_types = []
        for var_arg in args:
            ir_type = var_arg.ir_value.type.pointee
            if var_arg.is_ref:
                ir_type = ir_type.pointee
            stype = self.env.scope.get_type_name(ir_type)
            arg_types.append(Type(stype))

        name = FunctionMangler.encode(func_call.id, arg_types)
        function = self.env.scope.get_function(name)
        func = function.ir_func
        func_args = []

        for arg, arg_type in zip(args, function.meta_args):
            func_arg = self.env.builder.load(arg.ir_value)
            if arg.is_ref and not arg_type.is_ref:
                func_arg = self.env.builder.load(func_arg)
            func_args.append(func_arg)

        ret = self.env.builder.call(func, func_args)
        if not isinstance(func.ftype.return_type, ir.VoidType):
            ret_addr = self.env.builder.alloca(ret.type)
            self.env.builder.store(ret, ret_addr)
            ret_type_name = function.meta_rets[0].name
            return MetaVariable(ret_addr, ret_type_name, is_ref=function.meta_rets[0].is_ref)

    def visit_variable_dereference(self, var_deref):
        var_id = str(var_deref.idtok)
        return self.env.scope.get_variable(var_id)

    def visit_variable_declaration(self, var_decl):
        var_id = str(var_decl.var_id)
        var = var_decl.expression.visit(self)
        ir_type = var.ir_value.type.pointee
        init_val = var.ir_value

        # TODO: CLEAN
        if var_decl.is_ref and var.is_ref:
            var_addr = self.env.builder.alloca(ir_type, name=var_id)
            addr = self.env.builder.load(var.ir_value)
            self.env.builder.store(addr, var_addr)
            self.env.scope.add_variable(
                var_id, var_addr, var.type_name, is_ref=True)

        elif var_decl.is_ref and not var.is_ref:
            var_addr = self.env.builder.alloca(
                ir.PointerType(ir_type), name=var_id)
            temp = self.env.builder.load(init_val)
            temp_var_addr = self.env.builder.alloca(ir_type)
            self.env.builder.store(temp, temp_var_addr)
            self.env.builder.store(temp_var_addr, var_addr)
            self.env.scope.add_variable(
                var_id, var_addr, var.type_name, is_ref=True)

        elif not var_decl.is_ref and var.is_ref:
            temp = self.env.builder.load(init_val)
            val = self.env.builder.load(temp)
            var_addr = self.env.builder.alloca(val.type, name=var_id)
            self.env.builder.store(val, var_addr)
            self.env.scope.add_variable(var_id, var_addr, var.type_name)

        else:
            var_addr = self.env.builder.alloca(ir_type, name=var_id)
            temp = self.env.builder.load(init_val)
            self.env.builder.store(temp, var_addr)
            self.env.scope.add_variable(var_id, var_addr, var.type_name)

    def visit_variable_assignment(self, var_assign):
        var = var_assign.var.visit(self)
        init_var = var_assign.expression.visit(self)
        init_val = init_var.ir_value

        if var.is_ref:
            temp = self.env.builder.load(init_val)
            addr = self.env.builder.load(var.ir_value)
            self.env.builder.store(temp, addr)
        else:
            temp = self.env.builder.load(init_val)
            self.env.builder.store(temp, var.ir_value)

    def visit_type(self, type_t):
        meta_type = self.env.scope.get_type(str(type_t.typetok))
        if type_t.is_ref:
            ir_type = ir.PointerType(meta_type.ir_type)
            return MetaType(str(type_t.typetok), ir_type, is_ref=True)
        return meta_type

    def visit_bool(self, bool_t):
        val = 0
        if bool_t.valtok.value is 'true':
            val = 1
        value = ir.Constant(self.env.scope.get_type('bool'), val)
        var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, var_addr)
        return MetaVariable(var_addr, 'bool')

    def visit_float(self, float_t):
        value = ir.Constant(
            ir.FloatType(), float(float_t.valtok.value[:-1]))
        var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, var_addr)
        type_name = self.env.scope.get_type_name(ir.FloatType())
        return MetaVariable(var_addr, type_name)

    def visit_integer(self, integer_t):
        value = ir.Constant(ir.IntType(64), int(integer_t.valtok.value))
        var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(value, var_addr)
        type_name = self.env.scope.get_type_name(value.type)
        return MetaVariable(var_addr, type_name)

    def visit_string(self, string_t):
        value = codecs.escape_decode(
            bytes(string_t.valtok.value[1:-1], "utf-8"))[0].decode("utf-8") + '\00'
        string = ir.Constant(ir.ArrayType(ir.IntType(8), len(value)),
                             bytearray(value.encode("utf8")))
        var_addr = self.env.builder.alloca(value.type)
        self.env.builder.store(string, var_addr)
        type_name = self.env.scope.get_type_name(value.type)
        return MetaVariable(var_addr, type_name)

    def visit_return(self, ret):
        # TODO: Multiple RETURNS
        if ret.expression_list.expressions:
            ret_addr = ret.expression_list.expressions[0].visit(self)
            ret_val = self.env.builder.load(ret_addr.ir_value)
            return self.env.builder.ret(ret_val)
        else:
            self.env.builder.ret_void()
