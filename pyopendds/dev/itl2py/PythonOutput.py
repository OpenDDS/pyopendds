from pathlib import Path

from .ast import Output, PrimitiveType

class PythonOutput(Output):

  primitive_types = { # (Python Type, Default Default Value)
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

  def __init__(self,
      output_path: Path,
      python_package_name: str,
      native_package_name: str):
    self.python_package_name = python_package_name
    self.native_package_name = native_package_name
    path = output_path / python_package_name
    path.mkdir(parents=True, exist_ok=True)
    super().__init__(path / '__init__.py')
    self.append('''\
def _pyopendds_inject_idl(module_name):
    from pyopendds.IDL import IDL
    from dataclasses import field
    idl = IDL()
''')

  def write(self):
    self.append('''
    idl.inject(module_name)
_pyopendds_inject_idl(__name__)
del _pyopendds_inject_idl''')
    super().write()

  def visit_module(self, module):
    if module.name.parts:
      self.append("    idl.add_module('{}', '{}')".format(
        module.parent_name().join(),
        module.local_name())
      )
    super().visit_module(module)

  def visit_struct(self, struct_type):
    self.append("    idl.add_struct('{}', '{}', '{}', [".format(
      struct_type.parent_name().join(),
      struct_type.local_name(),
      self.native_package_name if struct_type.is_topic_type else None))
    for name in struct_type.fields:
      self.append("        ('{}', 'typing.Any', field(default=None)),".format(name))
    self.append("    ])")

  def visit_enum(self, enum_type):
    self.append("    idl.add_enum('{}', '{}', [".format(
      enum_type.parent_name().join(),
      enum_type.local_name()))
    for name in enum_type.members:
      self.append("        '{}',".format(name))
    self.append("    ])")
