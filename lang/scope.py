
class MetaVariable():
    def __init__(self, value, type_name, is_ref=False):
        self.ir_value = value
        self.is_ref = is_ref
        self.type_name = type_name


class MetaFunction():
    def __init__(self, func, meta_args, meta_rets):
        self.ir_func = func
        self.meta_args = meta_args
        self.meta_rets = meta_rets


class MetaType():
    def __init__(self, name, type_t, is_ref=False, field_names=None, fields=None):
        self.name = name
        self.ir_type = type_t
        self.fields = fields
        self.is_ref = is_ref
        if not self.fields:
            self.fields = []
        self.field_names = field_names
        if not self.field_names:
            self.field_names = []

    def get_field_offset(self, field_name):
        assert field_name in self.field_names
        return self.field_names.index(field_name)


class Scope():
    def __init__(self):
        self.type_dicts = [{}]
        self.func_dicts = [{}]
        self.ir_type_dicts = [{}]
        self.var_dicts = [{}]

    def add_variable(self, name, var, type_name, is_ref=False):
        self.var_dicts[-1][name] = MetaVariable(var, type_name, is_ref=is_ref)

    def add_function(self, name, func, meta_args, meta_rets):
        self.func_dicts[-1][name] = MetaFunction(func, meta_args, meta_rets)

    def add_type(self, name, ir_type, field_names=None, fields=None, is_ref=False):
        self.type_dicts[-1][name] = MetaType(name, ir_type,
                                             field_names=field_names, fields=fields)
        self.ir_type_dicts[-1][ir_type] = name

    def get_variable(self, name):
        name = str(name)
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
