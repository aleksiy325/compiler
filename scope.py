class Scope():
    def __init__(self):
        self.type_dicts = [{}]
        self.func_dicts = [{}]
        self.ir_type_dicts = [{}]
        self.var_dicts = [{}]

    def add_variable(self, name, var_type):
        self.var_dicts[-1][name] = var_type

    def add_function(self, name, func):
        self.func_dicts[-1][name] = func

    def add_type(self, name, ir_type):
        self.type_dicts[-1][name] = ir_type
        self.ir_type_dicts[-1][ir_type] = name

    def get_variable(self, name):
        for var_dict in self.var_dicts[::-1]:
            if name in var_dict:
                return var_dict[name]
        assert False

    def get_type(self, name):
        for type_dict in self.type_dicts[::-1]:
            if name in type_dict:
                return type_dict[name]
        assert False

    def get_type_name(self, ir_type):
        for type_dict in self.ir_type_dicts[::-1]:
            if ir_type in type_dict:
                return type_dict[ir_type]
        assert False

    def get_function(self, name):
        for func_dict in self.func_dicts[::-1]:
            if name in func_dict:
                return func_dict[name]
        assert False

    def enter_scope(self):
        self.type_dicts.append(dict())
        self.ir_type_dicts.append(dict())
        self.var_dicts.append(dict())

    def exit_scope(self):
        self.type_dicts.pop()
        self.var_dicts.pop()

    def __str__(self):
        str_list = []
        for types, variables, ir_types, functions in zip(self.type_dicts, self.var_dicts, self.ir_type_dicts, self.func_dicts):
            for key, val in types.items():
                str_list.append("{}: {}\n".format(key, val))
            for key, val in ir_types.items():
                str_list.append("{}: {}\n".format(key, val))
            for key, val in variables.items():
                str_list.append("{}: {}\n".format(key, val))
            for key, val in functions.items():
                str_list.append("{}: {}\n".format(key, val))
        return "".join(str_list)
