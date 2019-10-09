# A Prototype for Generating a Python Mapping from a ITL File
# TODO: Implement Real Visitor Pattern
# TODO: A whole bunch of other stuff...

import sys
import json
from enum import Enum, auto

class Output:
  def __init__(self, name):
    self.name = name
    self.contents = []

  def write(self):
    with open(self.name, 'w') as f:
      f.write('\n'.join(self.contents))

class PythonOutput(Output):
  def __init__(self, name):
    super().__init__(name)
    self.imports = set()

  def add_import(self, name):
    if name not in self.imports:
      self.imports |= {name}
      self.contents.insert(0, 'import ' + name + ' as _' + name)

  def extend(self, lines):
    if self.contents:
      self.contents.append('')
    self.contents.extend(lines)

def itl_name_to_scope(itl_name):
  return itl_name.split(':')[1].split('/')

class Type:

  def set_name(self, itl_name):
    self.itl_name = itl_name
    self.scoped_name = itl_name_to_scope(itl_name)
    self.name = self.scoped_name[-1]

  def default_default_value(self):
    raise NotImplementedError

  def default_value(self):
    raise NotImplementedError

  class Kind(Enum):
    u8 = auto()
    i8 = auto()
    u16 = auto()
    i16 = auto()
    u32 = auto()
    i32 = auto()
    u64 = auto()
    i64 = auto()
    f32 = auto()
    f64 = auto()
    c8 = auto()
    s8 = auto()
    enum = auto()
    struct = auto()

  def kind(self):
    raise NotImplementedError

  def python_name(self):
    raise NotImplementedError

  def to_python(self, python_output):
    raise NotImplementedError

class PrimitiveType(Type):

  types = {
    Type.Kind.u8: ('int', '0'),
    Type.Kind.i8: ('int', '0'),
    Type.Kind.u16: ('int', '0'),
    Type.Kind.i16: ('int', '0'),
    Type.Kind.u32: ('int', '0'),
    Type.Kind.i32: ('int', '0'),
    Type.Kind.u64: ('int', '0'),
    Type.Kind.i64: ('int', '0'),
    Type.Kind.f32: ('float', '0.0'),
    Type.Kind.f64: ('float', '0.0'),
    Type.Kind.c8: ('str', "'\\x00'"),
    Type.Kind.s8: ('str', "''"),
  }

  def __init__(self, kind):
    if kind not in self.types:
      raise ValueError('Invalid Primitive: ' + repr(kind))
    self._kind = kind

  def python_name(self):
    return self.types[self._kind][0]

  def default_value(self):
    return self.types[self._kind][1]

class Struct(Type):
  
  def __init__(self, itl_name):
    self.set_name(itl_name)
    self.fields = []

  def add_field(self, name, kind):
    self.fields.append((name, kind))

  def to_python(self, python_output):
    python_output.add_import('dataclasses')
    result = [
      '@_dataclasses.dataclass',
      'class ' + self.name + ':']
    for field_name, field_type in self.fields:
      line = '    {}: {}'.format(field_name, field_type.python_name())
      default_value = field_type.default_value()
      if default_value:
        line += ' = ' + default_value
      result.append(line)
    python_output.extend(result)

  def python_name(self):
    return self.name

  def default_value(self):
    return self.name + '()'

class Enum(Type):
  
  def __init__(self, itl_name):
    self.set_name(itl_name)
    self.members = []

  def add_member(self, name, value):
    self.members.append((name, value))

  def to_python(self, python_output):
    python_output.add_import('enum')
    result = ['class ' + self.name + '(_enum.IntFlag):']
    for name, value in self.members:
      result.append('    {} = {}'.format(name, value))
    python_output.extend(result)

  def python_name(self):
    return self.name

  def default_value(self):
    return '{}.{}'.format(self.name, self.members[0][0])

class Context:
  def __init__(self):
    self.types = {}

def get_type(context, name, details):
  details_type = type(details)
  if details_type is str:
    return context.types[details]
  elif details_type is dict:
    kind = details['kind']
    if kind == 'int':
      unsigned = 'unsigned' in details and details['unsigned'] == True
      enum = 'values' in details and 'constrained' in details and details['constrained']
      char = False
      try:
        char = details['note']['presentation']['type'] == 'char'
      except:
        pass
      if 'bits' in details:
        kind = None
        if details['bits'] == 8:
          if unsigned:
            kind = Type.Kind.u8
          else:
            kind = Type.Kind.i8
        elif details['bits'] == 16:
          if unsigned:
            kind = Type.Kind.u16
          else:
            kind = Type.Kind.i16
        elif details['bits'] == 32:
          if unsigned:
            kind = Type.Kind.u32
          else:
            kind = Type.Kind.i32
        elif details['bits'] == 64:
          if unsigned:
            kind = Type.Kind.u64
          else:
            kind = Type.Kind.i64
        if char and kind == Type.Kind.u8:
          return PrimitiveType(Type.Kind.c8)
        elif enum:
          return visit_enum(context, name, details)
        else:
          return PrimitiveType(kind)
  raise ValueError(repr(details))

def visit_record(context, name, details):
  struct = Struct(name)
  for field in details['fields']:
    field_name = field['name']
    struct.add_field(field_name, get_type(context, field_name, field['type']))
  context.types[name] = struct
  struct.to_python(context.python_output)
  
def visit_enum(context, name, details):
  enum_type = Enum(name)
  for k, v in details['values'].items():
    enum_type.add_member(k, v)
  context.types[name] = enum_type
  enum_type.to_python(context.python_output)

def visit_int(context, name, details):
  return get_type(context, name, details)

def visit_type(context, name, details):
  if type(details) is str:
    print('  is', itl_name_to_scope(details))
  elif type(details) is dict:
    kind = details['kind']
    if kind == 'record':
      visit_record(context, name, details)
    elif kind == 'int':
      visit_int(context, name, details)
    elif kind == 'string':
      visit_string(details)
    else:
      print("Not Prepared For kind " + repr(kind))

if __name__ == "__main__":
  if len(sys.argv) != 2:
    sys.exit('Must pass ITL file')

  itl_file = sys.argv[1]

  if not itl_file.endswith('.itl'):
    sys.exit('ITL file must have itl file extension')

  context = Context()
  context.python_output = PythonOutput(itl_file[:-4] + '.py')

  with open(itl_file) as f:
    itl = json.load(f)

  for t in itl['types']:
    visit_type(context, t['name'], t['type'])

  print('\n'.join(context.python_output.contents))

  context.python_output.write()
