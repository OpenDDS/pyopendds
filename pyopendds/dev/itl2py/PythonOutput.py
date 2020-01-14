from .ast import PrimitiveType, StructType, EnumType
from .Output import Output


class PythonOutput(Output):
    '''Manages Output of Python Bindings

    Using a self nesting structure, a PythonOutput is created for each IDL
    module.
    '''

    primitive_types = {  # (Python Type, Default Default Value)
        PrimitiveType.Kind.u8: ('int', '0'),
        PrimitiveType.Kind.i8: ('int', '0'),
        PrimitiveType.Kind.u16: ('int', '0'),
        PrimitiveType.Kind.i16: ('int', '0'),
        PrimitiveType.Kind.u32: ('int', '0'),
        PrimitiveType.Kind.i32: ('int', '0'),
        PrimitiveType.Kind.u64: ('int', '0'),
        PrimitiveType.Kind.i64: ('int', '0'),
        PrimitiveType.Kind.f32: ('float', '0.0'),
        PrimitiveType.Kind.f64: ('float', '0.0'),
        PrimitiveType.Kind.c8: ('str', "'\\x00'"),
        PrimitiveType.Kind.s8: ('str', "''"),
    }

    def __init__(self, context: dict, name: str):
        self.submodules = []
        self.module = None
        new_context = context.copy()
        new_context.update(dict(
            output=context['output'] / name,
            types=[]
        ))
        super().__init__(new_context, new_context['output'],
            {'__init__.py': 'user.py'})

    def write(self):
        super().write()
        for submodule in self.submodules:
            submodule.write()

    def visit_root_module(self, root_module):
        self.module = root_module
        super().visit_module(root_module)

    def visit_module(self, module):
        submodule = PythonOutput(self.context, module.local_name())
        self.submodules.append(submodule)
        submodule.visit_root_module(module)

    def get_python_type_string(self, field_type):
        if isinstance(field_type, PrimitiveType):
            return self.primitive_types[field_type.kind][0]
        elif field_type in self.module.types.values():
            return field_type.local_name()
        else:
            raise NotImplementedError

    def get_python_default_value_string(self, field_type):
        if isinstance(field_type, PrimitiveType):
            return self.primitive_types[field_type.kind][1]
        elif field_type in self.module.types.values():
            if isinstance(field_type, StructType):
                return field_type.local_name() + '()'
            elif isinstance(field_type, EnumType):
                return field_type.local_name() + '.' + field_type.default_member
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def visit_struct(self, struct_type):
        self.context['has_struct'] = True
        self.context['types'].append(dict(
            local_name=struct_type.local_name(),
            type_support=self.context['native_package_name'] if struct_type.is_topic_type else None,
            struct=dict(
                fields=[dict(
                    name=name,
                    type=self.get_python_type_string(node.type_node),
                    default_value=self.get_python_default_value_string(node.type_node),
                ) for name, node in struct_type.fields.items()],
            ),
        ))

    def visit_enum(self, enum_type):
        self.context['has_enum'] = True
        self.context['types'].append(dict(
            local_name=enum_type.local_name(),
            enum=dict(
                members=[
                    dict(name=name, value=value) for name, value in enum_type.members.items()
                ],
            ),
        ))
