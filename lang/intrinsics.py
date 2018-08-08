from llvmlite import ir
from lang.common import Function, Type, TypeList, ArgList, FunctionId, Block

INTEGER = 'int'


class Intrinsics():
    def __init__(self):
        self.functions = []
        self.declare_integer_add()
        # self.declare_integer_add_overflow()
        # self.declare_integer_sub()
        # # self.declare_integer_sub_overflow()
        # self.declare_integer_shl()
        # self.declare_integer_lshr()
        # self.declare_integer_ashr()
        self.declare_print_integer()
        # self.declare_integer_mul()
        # # self.declare_integer_mul_overflow()
        # self.declare_integer_signed_div()
        # self.declare_integer_unsigned_div()
        # self.declare_integer_signed_mod()
        # self.declare_integer_unsigned_mod()

        # self.declare_integer_and()
        # self.declare_integer_or()
        # self.declare_integer_xor()
        # self.declare_integer_not()
        # self.declare_integer_neg()

    def visit(self, visitor):
        for func in self.functions:
            func.visit(visitor)

    def declare_print_integer(self):
        retlist = TypeList([])
        arglist = ArgList([(Type(INTEGER), '_int')])
        function = Function(FunctionId('print'), arglist, retlist, Block([]))

        def print_integer_block(env):
            voidptr_ty = ir.IntType(8).as_pointer()
            fmt = "%i\n\0"
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(
                env.module, c_fmt.type, name="fstr")
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
            fmt_arg = env.builder.bitcast(global_fmt, voidptr_ty)

            var_addr = env.scope.get_variable('_int').ir_value
            _int_ptr = env.builder.load(var_addr)
            printf = env.module.get_global('printf')
            env.builder.call(printf, [fmt_arg, _int_ptr])
            env.builder.ret_void()

        function.block_callback = print_integer_block
        self.functions.append(function)

    def declare_integer_add(self):
        retlist = TypeList([Type(INTEGER)])
        arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
        function = Function(FunctionId('+'), arglist, retlist, Block([]))

        def integer_add_block(env):
            aa = env.scope.get_variable('_a').ir_value
            ba = env.scope.get_variable('_b').ir_value
            a = env.builder.load(aa)
            b = env.builder.load(ba)
            add = env.builder.add(a, b)
            env.builder.ret(add)

        function.block_callback = integer_add_block
        self.functions.append(function)

    # def declare_integer_sub(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('-'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.sub(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_sub_overflow(self):
    #     # TODO: Fix
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('-^'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.ssub_with_overflow(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_add_overflow(self):
    #     # TODO: Fix
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('+^'), arglist, retlist, Block([]))

    #     def integer_add_block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.sadd_with_overflow(a, b)
    #         env.builder.ret(add)

    # def declare_integer_shl(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('<<'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.shl(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_lshr(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('>>'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.lshr(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_ashr(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('>>>'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.ashr(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_mul(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('*'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.mul(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_mul_overflow(self):
    #     # TODO: Fix
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('*^'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.smul_with_overflow(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_signed_div(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('/'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.sdiv(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_unsigned_div(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('//'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.udiv(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_signed_mod(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('%'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.srem(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_unsigned_mod(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('%%'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.urem(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_and(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('&'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.and_(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_or(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('|'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.or_(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_xor(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a'), (Type(INTEGER), '_b')])
    #     function = Function(FunctionId('^'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         b = env.scope.get_variable('_b')
    #         add = env.builder.xor(a, b)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_not(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a')])
    #     function = Function(FunctionId('!'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         add = env.builder.not_(a)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)

    # def declare_integer_neg(self):
    #     retlist = TypeList([Type(INTEGER)])
    #     arglist = ArgList([(Type(INTEGER), '_a')])
    #     function = Function(FunctionId('-'), arglist, retlist, Block([]))

    #     def block(env):
    #         a = env.scope.get_variable('_a')
    #         add = env.builder.neg(a)
    #         env.builder.ret(add)

    #     function.block_callback = block
    #     self.functions.append(function)
