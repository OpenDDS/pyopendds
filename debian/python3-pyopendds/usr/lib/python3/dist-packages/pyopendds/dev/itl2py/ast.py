from enum import Enum, unique
from dataclasses import dataclass
from typing import Optional


class Name:
    def __init__(self, itl_name=None, parts=None):
        if itl_name is not None and parts is None:
            self.itl_name = itl_name
            self.parts = itl_name.split(":")[1].split("/")
        elif itl_name is None and parts is not None:
            self.itl_name = "IDL:{}:1.0".format("/".join(parts))
            self.parts = parts
        else:
            raise ValueError("Either parts or itl_name must be passed")
    
    def join(self, sep="."):
        return sep.join(self.parts)


class Node:
    def __init__(self):
        self.name = None
        self.is_topic_type = False
    
    def set_name(self, itl_name=None, parts=None):
        self.name = Name(itl_name=itl_name, parts=parts)
    
    def local_name(self):
        if self.name:
            return self.name.parts[-1]
        return None
    
    def parent_name(self):
        if self.name:
            return Name(parts=self.name.parts[:-1])
        return None
    
    def accept(self, visitor):
        raise NotImplementedError
    
    def repr_name(self):
        if self.name:
            return "::" + self.name.join("::")
    
    def repr_template(self, contents):
        info = ""
        name = self.repr_name()
        if name:
            info += " " + name
        if contents:
            info += ": " + contents
        return "<{}{}>".format(self.__class__.__name__, info)
    
    def __repr__(self):
        return self.repr_template(None)


class Module(Node):
    def __init__(self, parent, name):
        super().__init__()
        self.parent = parent
        name_parts = []
        if parent and name:
            name_parts.extend(parent.name.parts)
            name_parts.append(name)
        self.set_name(parts=name_parts)
        self.submodules = {}
        self.types = {}
    
    def accept(self, visitor):
        for type_node in self.types.values():
            type_node.accept(visitor)
        
        for submodule in self.submodules.values():
            visitor.visit_module(submodule)
    
    def repr_name(self):
        if self.name.parts:
            return super().__repr__()
        else:
            return ":: (Root Module)"


@dataclass(frozen=True)
class PrimitiveTypeTraits:
    element_size: Optional[int] = None
    is_unsigned_int: bool = False
    is_signed_int: bool = False
    is_float: bool = False
    is_text: bool = False
    is_scalar: bool = True
    is_bool: bool = False
    is_raw: bool = False


class PrimitiveType(Node):
    @unique
    class Kind(Enum):
        bool = PrimitiveTypeTraits(element_size=8, is_bool=True)
        byte = PrimitiveTypeTraits(element_size=8, is_raw=True)
        u8 = PrimitiveTypeTraits(element_size=8, is_unsigned_int=True)
        i8 = PrimitiveTypeTraits(element_size=8, is_signed_int=True)
        u16 = PrimitiveTypeTraits(element_size=16, is_unsigned_int=True)
        i16 = PrimitiveTypeTraits(element_size=16, is_signed_int=True)
        u32 = PrimitiveTypeTraits(element_size=32, is_unsigned_int=True)
        i32 = PrimitiveTypeTraits(element_size=32, is_signed_int=True)
        u64 = PrimitiveTypeTraits(element_size=64, is_unsigned_int=True)
        i64 = PrimitiveTypeTraits(element_size=64, is_signed_int=True)
        u128 = PrimitiveTypeTraits(element_size=128, is_unsigned_int=True)
        i128 = PrimitiveTypeTraits(element_size=128, is_signed_int=True)
        f32 = PrimitiveTypeTraits(element_size=32, is_float=True)
        f64 = PrimitiveTypeTraits(element_size=64, is_float=True)
        f128 = PrimitiveTypeTraits(element_size=128, is_float=True)
        c8 = PrimitiveTypeTraits(element_size=8, is_text=True)
        c16 = PrimitiveTypeTraits(element_size=16, is_text=True)
        s8 = PrimitiveTypeTraits(element_size=8, is_text=True, is_scalar=False)
        s16 = PrimitiveTypeTraits(element_size=16, is_text=True, is_scalar=False)
    
    def __init__(self, kind):
        super().__init__()
        self.kind = self.Kind(kind)
        self.element_count_limit = None
    
    def accept(self, visitor):
        pass
    
    def is_int(self):
        return self.kind.value.is_unsigned_int or self.kind.value.is_signed_int
    
    def is_string(self):
        return self.kind.value.is_text and not self.kind.value.is_scalar
    
    def __repr__(self):
        contents = self.kind.name
        if self.element_count_limit:
            contents += " max {}".format(self.element_count_limit)
        return self.repr_template(contents)


class FieldType(Node):
    def __init__(self, name, type_node, optional):
        super().__init__()
        self.set_name(parts=[name])
        self.type_node = type_node
        self.optional = optional
    
    def __repr__(self):
        return self.repr_template(repr(self.type_node))


class StructType(Node):
    def __init__(self):
        super().__init__()
        self.fields = {}
    
    def add_field(self, name, type_node, optional):
        self.fields[name] = FieldType(name, type_node, optional)
    
    def accept(self, visitor):
        visitor.visit_struct(self)


class EnumType(Node):
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.members = {}
        self.default_member = None
    
    def add_member(self, name, value):
        self.members[name] = value
        if self.default_member is None:
            self.default_member = name
    
    def accept(self, visitor):
        visitor.visit_enum(self)
    
    def __repr__(self):
        return self.repr_template("{} bits".format(self.size))


class ArrayType(Node):
    def __init__(self, base_type, dimensions):
        super().__init__()
        self.base_type = base_type
        self.dimensions = dimensions
    
    def accept(self, visitor):
        visitor.visit_array(self)
        pass
    
    def __repr__(self):
        return self.repr_template(
            repr(self.base_type) + "".join(["[{}]".format(i) for i in self.dimensions])
        )


class SequenceType(Node):
    def __init__(self, base_type, max_count):
        super().__init__()
        self.base_type = base_type
        self.max_count = max_count
    
    def accept(self, visitor):
        visitor.visit_sequence(self)
    
    def __repr__(self):
        return self.repr_template(
            repr(self.base_type)
            + ("max " + str(self.max_count) if self.max_count else "no max")
        )
    
    def repr_name(self):
        if self.name:
            return (
                    "::" + self.name.join("::") + "::_tao_seq_" + repr(self.base_type) + "_"
            )


class NodeVisitor:
    def visit_root_module(self, root_module):
        root_module.accept(self)
    
    def visit_module(self, module):
        module.accept(self)
    
    def visit_struct(self, struct_type):
        raise NotImplementedError
    
    def visit_enum(self, enum_type):
        raise NotImplementedError
    
    def visit_array(self, array_type):
        pass
        # array_type.accept(self)
    
    def visit_sequence(self, sequence_type):
        raise NotImplementedError
        # sequence_type.accept(self)


def get_ast(types: dict) -> Module:
    root_module = Module(None, "")
    for type_node in types.values():
        module = root_module
        for module_name in type_node.parent_name().parts:
            if module_name not in module.submodules:
                module.submodules[module_name] = Module(module, module_name)
            module = module.submodules[module_name]
        module.types[type_node.name.itl_name] = type_node
    return root_module
