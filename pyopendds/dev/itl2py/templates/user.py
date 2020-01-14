{% if has_struct -%}
from dataclasses import dataclass as _pyopendds_struct
{%- endif %}
{% if has_enum -%}
from enum import IntFlag as _pyopendds_enum
{%- endif %}
{% for type in types -%}
{%- if type.struct %}

@_pyopendds_struct
class {{ type.local_name }}:
{%- if type.type_support %}
    _pyopendds_typesupport_packge_name = '{{ type.type_support }}'
{% endif -%}
{%- for field in type.struct.fields %}
    {{ field.name }}: {{ field.type }} = {{ field.default_value }}
{%- endfor %}
{%- elif type.enum %}
class {{ type.local_name }}(_pyopendds_enum):
{%- for member in type.enum.members %}
    {{ member.name }} = {{ member.value }}
{%- endfor %}
{%- else %}
# {{ type.local_name }} was left unimplmented
{% endif -%}
{%- endfor -%}
