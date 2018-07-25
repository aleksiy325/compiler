from abc import ABCMeta, abstractmethod


class Visitor(metaclass=ABCMeta):

    @abstractmethod
    def visit_expression_list(self, expr_list):
        pass

    @abstractmethod
    def visit_function_id(self, func_id):
        pass

    @abstractmethod
    def visit_arg_list(self, arg_list):
        pass

    @abstractmethod
    def visit_type_list(self, type_list):
        pass

    @abstractmethod
    def visit_block(self, block):
        pass

    @abstractmethod
    def visit_function(self, func):
        pass

    @abstractmethod
    def visit_function_call(self, func_call):
        pass

    @abstractmethod
    def visit_variable_dereference(self, var_deref):
        pass

    @abstractmethod
    def visit_variable_declaration(self, var_decl):
        pass

    @abstractmethod
    def visit_variable_assigment(self, var_assign):
        pass

    @abstractmethod
    def visit_type(self, type_t):
        pass

    @abstractmethod
    def visit_bool(self, bool_t):
        pass

    @abstractmethod
    def visit_float(self, float_t):
        pass

    @abstractmethod
    def visit_integer(self, integer_t):
        pass

    @abstractmethod
    def visit_string(self, string_t):
        pass

    @abstractmethod
    def visit_return(self, ret):
        pass


class Visitable(metaclass=ABCMeta):

    @abstractmethod
    def visit(self, visitor: Visitor):
        pass
