from jinja2 import Environment

from .ast import PrimitiveType, StructType, EnumType
from .Output import Output


def cpp_name(name_parts):
    return '::' + '::'.join(name_parts)


def cpp_type_name(type_node):
    if isinstance(type_node, PrimitiveType):
        return type_node.kind.name
    elif isinstance(type_node, (StructType, EnumType)):
        return cpp_name(type_node.name.parts)
    else:
        raise NotImplementedError


class CppOutput(Output):

    def __init__(self, context: dict):
        new_context = context.copy()
        jinja_start = '/*{'
        jinja_end = '}*/'
        new_context.update(dict(
            idl_names=[
                itl_file.name[:-len('.itl')] for itl_file in context['itl_files']],
            types=[],
            jinja=Environment(
                loader=context['jinja_loader'],
                block_start_string=jinja_start + '%',
                block_end_string='%' + jinja_end,
                variable_start_string=jinja_start + '{',
                variable_end_string='}' + jinja_end,
                comment_start_string=jinja_start + '#',
                comment_end_string='#' + jinja_end,
            )
        ))
        super().__init__(new_context, context['output'],
            {context['native_package_name'] + '.cpp': 'user.cpp'})

    def visit_struct(self, struct_type):
        struct_to_lines = [
            'Ref field_value;',
        ]
        struct_from_lines = [
            'Ref field_value;',
        ]
        for field_name, field_node in struct_type.fields.items():
            to_lines = []
            from_lines = []
            pyopendds_type = ''
            is_string = isinstance(field_node.type_node, PrimitiveType) and \
                field_node.type_node.is_string()

            to_lines = [
                'Type<{pyopendds_type}>::cpp_to_python(cpp.{field_name}',
                '#ifdef CPP11_IDL',
                '    ()',
                '#endif',
                '    , *field_value'
                    + (', "{default_encoding}"' if is_string else '') + ');',
            ]

            from_lines = [
                'if (PyObject_HasAttrString(py, "{field_name}")) {{',
                '    *field_value = PyObject_GetAttrString(py, "{field_name}");',
                '}}',
                'if (!field_value) {{',
                '  throw Exception();',
                '}}'
            ]

            pyopendds_type = cpp_type_name(field_node.type_node)

            if to_lines:
                to_lines.extend([
                    'if (!field_value || PyObject_SetAttrString(',
                    'py, "{field_name}", *field_value)) {{',
                    '  throw Exception();',
                    '}}'
                ])

            if from_lines:
                from_lines.extend([
                    'Type<{pyopendds_type}>::python_to_cpp(*field_value, cpp.{field_name}',
                    '#ifdef CPP11_IDL',
                    '    ()',
                    '#endif',
                    '    '
                    + (', "{default_encoding}"' if is_string else '') + ');'
                ])

            def line_process(lines):
                return [''] + [
                    s.format(
                        field_name=field_name,
                        default_encoding=self.context['default_encoding'],
                        pyopendds_type=pyopendds_type,
                    ) for s in (lines if lines else [
                        '// {field_name} was left unimplemented',
                    ])
                ]
            struct_to_lines.extend(line_process(to_lines))
            struct_from_lines.extend(line_process(from_lines))

        self.context['types'].append({
            'cpp_name': cpp_name(struct_type.name.parts),
            'name_parts': struct_type.parent_name().parts,
            'local_name': struct_type.local_name(),
            'to_lines': '\n'.join(struct_to_lines),
            'from_lines': '\n'.join(struct_from_lines),
            'new_lines': '\n'.join([
                'args = nullptr;'
            ]),
            'is_topic_type': struct_type.is_topic_type,
            'to_replace': False,
        })

    def visit_enum(self, enum_type):
        self.context['types'].append({
            'cpp_name': cpp_name(enum_type.name.parts),
            'name_parts': enum_type.parent_name().parts,
            'local_name': enum_type.local_name(),
            'to_replace': True,
            'new_lines': '\n'.join([
                'args = PyTuple_Pack(1, PyLong_FromLong(static_cast<long>(cpp)));',
            ]),
            'to_lines': '',
            'from_lines': '',
            'is_topic_type': False,
        })
