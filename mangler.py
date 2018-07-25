from common import Type


class FunctionMangler():
    end_symbol = '_'

    @staticmethod
    def digits(num_chars):
        return str(num_chars) + FunctionMangler.end_symbol

    @staticmethod
    def encode(id, arg_types):
        id_str = str(id)
        mangle = [FunctionMangler.digits(len(id_str)), id_str,
                  FunctionMangler.digits(len(arg_types))]

        for type_t in arg_types:
            type_str = str(type_t.typetok)
            mangle.append(FunctionMangler.digits(len(type_str)))
            mangle.append(type_str)

        return ''.join(mangle)

    @staticmethod
    def decode(mangled):
        # TODO: Doesnt work with ref also needed?
        i = 0
        end = mangled.find(FunctionMangler.end_symbol, i)
        i = end + 1 + int(mangled[i: end])
        id = mangled[end + 1: i]
        end = mangled.find(FunctionMangler.end_symbol, i)
        arg_types = []
        num_args = int(mangled[i: end])
        i = end + 1
        for _ in range(num_args):
            end = mangled.find(FunctionMangler.end_symbol, i)
            i = end + 1 + int(mangled[i: end])
            arg = mangled[end + 1: i]
            arg_types.append(Type(arg))

        end = mangled.find(FunctionMangler.end_symbol, i)
        return id, arg_types
