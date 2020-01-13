from jinja2 import Environment

from .ast import PrimitiveType, EnumType
from .Output import Output


class CppOutput(Output):

    def __init__(self, context: dict):
        new_context = context.copy()
        jinja_start = '/*{'
        jinja_end = '}*/'
        new_context.update(dict(
            idl_names=[
                itl_file.name[:-len('.itl')] for itl_file in context['itl_files']],
            types=[],
            topic_types=[],
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
        cpp_name = '::' + struct_type.name.join('::')
        if struct_type.is_topic_type:
            self.context['topic_types'].append(cpp_name)

        struct_to_lines = []
        struct_from_lines = []
        nop = '// {field_name} was left unimplemented'
        for field_name, field_node in struct_type.fields.items():
            implemented = True
            to_lines = []
            from_lines = []
            if isinstance(field_node.type_node, PrimitiveType):
                if field_node.type_node.is_int():
                    to_lines.append(
                        'field_value = PyLong_FromLong(cpp.{field_name});')
                    from_lines.append(
                        'rv.{field_name} = get_python_long_attr(py, "{field_name}");')

                elif field_node.type_node.is_string():
                    to_lines.append('field_value = PyUnicode_Decode(cpp.{field_name}, '
                        'strlen(cpp.{field_name}), "{default_encoding}", "strict");')
                    from_lines.append(nop)

                else:
                    implemented = False

            elif isinstance(field_node.type_node, EnumType):
                implemented = False

            else:
                implemented = False

            if implemented:
                to_lines.extend([
                    'if (!field_value || PyObject_SetAttrString('
                    'py, "{field_name}", field_value)) {{',
                    '  py = nullptr;',
                    '}}'
                ])
            else:
                to_lines.append(nop)
                from_lines.append(nop)

            def line_process(lines):
                return [
                    s.format(
                        field_name=field_name,
                        default_encoding=self.context['default_encoding'],
                    ) for s in lines
                ]
            struct_to_lines.extend(line_process(to_lines))
            struct_from_lines.extend(line_process(from_lines))

        self.context['types'].append({
            'cpp_name': cpp_name,
            'name_parts': struct_type.parent_name().parts,
            'local_name': struct_type.local_name(),
            'to_lines': '\n'.join(struct_to_lines),
            'from_lines': '\n'.join(struct_from_lines),
        })

    def visit_enum(self, enum_type):
        pass
