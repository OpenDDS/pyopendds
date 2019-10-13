#!/usr/bin/env python3

# A Prototype for Generating a Python Mapping from a ITL File

import sys
import json
from enum import Enum, auto

def itl_name_to_scope(itl_name):
  return itl_name.split(':')[1].split('/')

class Type:

  def __init__(self, note):
    self.note = note
    self.itl_name = None
    self.scoped_name = None
    self.name = None

  def set_name(self, itl_name):
    self.itl_name = itl_name
    self.scoped_name = itl_name_to_scope(itl_name)
    self.name = self.scoped_name[-1]

  def accept(self, visitor):
    raise NotImplementedError

class PrimitiveType(Type):

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

  def __init__(self, kind, note):
    super().__init__(note)
    if kind not in self.Kind:
      raise ValueError('Invalid Primitive Kind: ' + repr(kind))
    self.kind = kind

class StructType(Type):

  def __init__(self, note):
    super().__init__(note)
    self.fields = {}

  def add_field(self, name, type_node, optional):
    self.fields[name] = (type_node, optional)

  def accept(self, visitor):
    visitor.visit_struct(self)

class EnumType(Type):

  def __init__(self, note):
    super().__init__(note)
    self.members = {}
    self.default_member = None

  def add_member(self, name, value):
    self.members[name] = value
    if self.default_member is None:
      self.default_member = name

  def accept(self, visitor):
    visitor.visit_enum(self)

class TypeVisitor:

  def visit_struct(self, struct_type):
    raise NotImplementedError

  def visit_enum(self, enum_type):
    raise NotImplementedError

class Output(TypeVisitor):

  def __init__(self, name):
    self.name = name
    self.contents = []

  def write(self):
    with open(self.name, 'w') as f:
      f.write('\n'.join(self.contents))

  def extend(self, lines, insert_newline=True):
    if self.contents and insert_newline:
      self.contents.append('')
    self.contents.extend(lines)

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

  def __init__(self, name):
    super().__init__(name)
    self.imports = set()

  def add_import(self, name):
    if name not in self.imports:
      self.imports |= {name}
      self.contents.insert(0, 'import ' + name + ' as _' + name)

  def get_python_name(self, node):
    node_type = type(node)
    if node_type is PrimitiveType:
      return self.primitive_types[node.kind][0]
    elif node_type is StructType:
      return node.name
    elif node_type is EnumType:
      return node.name
    else:
      raise TypeError("Can't get Python Name for a " + repr(node_type))

  def get_python_default_value(self, node):
    node_type = type(node)
    if node_type is PrimitiveType:
      return self.primitive_types[node.kind][1]
    elif node_type is StructType:
      return node.name + '()'
    elif node_type is EnumType:
      return '{}.{}'.format(node.name, node.default_member)
    else:
      raise TypeError("Can't get Python Name for a " + repr(node_type))

  def visit_struct(self, struct_type):
    self.add_import('dataclasses')
    result = [
      '@_dataclasses.dataclass',
      'class ' + struct_type.name + ':']
    for field_name, field_properities in struct_type.fields.items():
      field_type = field_properities[0]
      result.append('    {}: {} = {}'.format(
        field_name,
        self.get_python_name(field_type),
        self.get_python_default_value(field_type)))
    self.extend(result)

  def visit_enum(self, enum_type):
    self.add_import('enum')
    result = ['class ' + enum_type.name + '(_enum.IntFlag):']
    for name, value in enum_type.members.items():
      result.append('    {} = {}'.format(name, value))
    self.extend(result)

def parse_int(details):
  note = details.get('note', {})
  unsigned = 'unsigned' in details and details['unsigned'] == True
  enum = 'values' in details and 'constrained' in details and details['constrained']
  char = False
  try:
    char = details['note']['presentation']['type'] == 'char'
  except KeyError:
    pass

  kind = None
  if 'bits' in details:
    bits = details['bits']
    if bits == 8:
      if unsigned:
        kind = PrimitiveType.Kind.u8
      else:
        kind = PrimitiveType.Kind.i8
    elif bits == 16:
      if unsigned:
        kind = PrimitiveType.Kind.u16
      else:
        kind = PrimitiveType.Kind.i16
    elif bits == 32:
      if unsigned:
        kind = PrimitiveType.Kind.u32
      else:
        kind = PrimitiveType.Kind.i32
    elif bits == 64:
      if unsigned:
        kind = PrimitiveType.Kind.u64
      else:
        kind = PrimitiveType.Kind.i64

  if char and kind == PrimitiveType.Kind.u8:
    kind = PrimitiveType.Kind.c8
  elif enum:
    enum_type = EnumType(note)
    for k, v in details['values'].items():
      enum_type.add_member(k, v)
    return enum_type

  if kind:
    return PrimitiveType(kind, note)
  else:
    raise ValueError('Can\'t decide what this int type is: ' + repr(details))

def parse_float(details):
  raise NotImplementedError

def parse_fixed(details):
  raise NotImplementedError

def parse_string(details):
  raise NotImplementedError

def parse_sequence(types, details):
  raise NotImplementedError

def parse_record(types, details):
  struct_type = StructType(details.get('note', {}))
  for field_dict in details['fields']:
    struct_type.add_field(
      field_dict['name'], parse_type(types, field_dict['type']),
      field_dict.get('optional', False))
  return struct_type

def parse_union(types, details):
  raise NotImplementedError

def parse_alias(types, details):
  the_type = parse_type(types, details['type'])
  the_type.set_name(details['name'])
  return the_type

def parse_typedef(types, details):
  kind = details['kind']
  if kind == 'int':
    return parse_int(details)
  elif kind == 'float':
    return parse_float(details)
  elif kind == 'fixed':
    return parse_fixed(details)
  elif kind == 'string':
    return parse_string(details)
  elif kind == 'sequence':
    return parse_sequence(types, details)
  elif kind == 'record':
    return parse_record(types, details)
  elif kind == 'union':
    return parse_union(types, details)
  elif kind == 'alias':
    return parse_alias(types, details)
  else:
    raise ValueError(
      'Kind "{}" is not a valid type for parse_typedef()'.format(kind))

def parse_type(types, details):
  details_type = type(details)
  if details_type is str:
    if details in types:
      return types[details]
    else:
      raise ValueError("Invalid Type: " + details)
  elif details_type is dict:
    return parse_typedef(types, details)
  else:
    raise TypeError(
      'Type {} is not a valid type for parse_type()'.format(details_type.__name__))

def parse_root(types, itl):
  for itl_type in itl['types']:
    parsed_type = parse_type(types, itl_type)
    types[parsed_type.itl_name] = parsed_type

if __name__ == "__main__":
  if len(sys.argv) != 2:
    sys.exit('Must pass ITL file')

  itl_file_path = sys.argv[1]

  if not itl_file_path.endswith('.itl'):
    sys.exit('ITL file must have itl file extension')

  # Parse ITL
  types = {}
  with open(itl_file_path) as itl_file:
    parse_root(types, json.load(itl_file))

  # Output Python
  pyout = PythonOutput(itl_file_path[:-4] + '.py')
  for type_name, type_node in types.items():
    type_node.accept(pyout)
  pyout.write()
