from .ast import PrimitiveType, StructType, EnumType


def parse_int(details):
    note = details.get('note', {})
    unsigned = 'unsigned' in details and details['unsigned']
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
    return PrimitiveType(PrimitiveType.Kind.s8, details.get('note', {}))


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
    the_type.is_topic_type = \
        details['note'].get("is_dcps_data_type", False) if 'note' in details else False
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
            'Type "{}" is not a valid type for parse_type()'.format(details_type.__name__))


def parse_itl(types, itl):
    for itl_type in itl['types']:
        parsed_type = parse_type(types, itl_type)
        # opendds_idl produces ITL that includes types from included IDL files, so
        # just use the first definition we found.
        if parsed_type.name.itl_name not in types:
            types[parsed_type.name.itl_name] = parsed_type
