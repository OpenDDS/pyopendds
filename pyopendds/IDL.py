class IDL:
    def __init__(self):
        self.definitions = {}
        self.types = {}
        self.root_contents = set()

    def add_definition(self, module, name, type, **kw):
        if module:
            full_name = module + '.' + name
            self.definitions[module]['contents'] |= {full_name}
        else:
            full_name = name
            self.root_contents |= {full_name}
        d = {
            'module': module,
            'name': name,
            'type': type,
        }
        d.update(kw)
        self.definitions[full_name] = d

    def add_struct(self, module, name, ts_package, members):
        self.add_definition(module, name, 'struct',
          ts_package=ts_package, members=members)

    def get_struct(self, full_name):
        if full_name not in self.types:
            d = self.definitions[full_name]
            from dataclasses import make_dataclass
            t = make_dataclass(d['name'], d['members'])
            t.__module__ = d['module']
            if d['ts_package']:
                t._pyopendds_typesupport_packge_name = d['ts_package']
            self.types[full_name] = t
        else:
            t = self.types[full_name]
        return t

    def add_enum(self, module, name, members):
        self.add_definition(module, name, 'enum', members=members)

    def get_enum(self, full_name):
        if full_name not in self.types:
            d = self.definitions[full_name]
            from enum import IntFlag
            t = IntFlag(d['name'], d['members'])
            t.__module__ = d['module']
            self.types[full_name] = t
        else:
            t = self.types[full_name]
        return t

    def add_module(self, module, name):
        self.add_definition(module, name, 'module', contents=set())

    def inject_i(self, python_module, contents):
        item_types = {
            'struct': self.get_struct,
            'enum': self.get_enum,
            'module': self.get_module,
        }
        for item_name in contents:
            item_def = self.definitions[item_name]
            setattr(python_module, item_def['name'],
              item_types[item_def['type']](item_name))

    def get_module(self, full_name):
        if full_name not in self.types:
            d = self.definitions[full_name]
            from types import ModuleType
            m = ModuleType(d['name'])
            m.__package__ = d['module']
            self.inject_i(m, d['contents'])
            self.types[full_name] = m
        else:
            m = self.types[full_name]
        return m

    def inject(self, python_name):
        from sys import modules
        self.inject_i(modules[python_name], self.root_contents)
