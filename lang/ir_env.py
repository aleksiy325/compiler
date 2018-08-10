from llvmlite import ir, binding
from lang.scope import Scope
from collections import defaultdict


class IREnvironment():
    def __init__(self):
        self.functions = {}
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        self.scope = Scope()
        self._config_llvm()
        self._create_execution_engine()
        self._declare_print()
        self._add_basic_types()

    def _config_llvm(self):
        self.module = ir.Module(name='main_module', context=ir.Context())
        self.module.triple = self.binding.get_default_triple()
        func_type = ir.FunctionType(ir.IntType(64), [], False)
        main_func = ir.Function(self.module, func_type, name='main')
        block = main_func.append_basic_block(name='entry')
        self.builder = ir.IRBuilder(block)

    def _create_execution_engine(self):
        target = self.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = self.binding.parse_assembly('')
        self.engine = self.binding.create_mcjit_compiler(
            backing_mod, target_machine)

    def _declare_print(self):
        voidptr_type = ir.IntType(8).as_pointer()
        printf_type = ir.FunctionType(
            ir.IntType(32), [voidptr_type], var_arg=True)
        ir.Function(self.module, printf_type, name='printf')

    def _add_basic_types(self):
        self.scope.add_type("int", ir.IntType(64))
        self.scope.add_type("float", ir.FloatType())
        self.scope.add_type("void", ir.VoidType())
        self.scope.add_type("bool", ir.IntType(8))

    def _compile_ir(self):
        self.builder.ret(ir.Constant(ir.IntType(64), 0))
        mod = self.binding.parse_assembly(str(self.module))
        mod.verify()
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod

    def save_ir(self, filename):
        with open(filename, 'w+') as f:
            self._compile_ir()
            f.write(str(self.module))
