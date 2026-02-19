"""
JSON Schema generator — outputs draft-07 JSON Schema.
Config description/title are included as schema metadata.
Field annotations are ignored.
"""

import re
import json

from .base import BaseGenerator
from ..models import YAIFInterface, YAIFEnum, YAIFConfig


class JSONSchemaGenerator(BaseGenerator):

    TYPE_MAP = {
        'string': {'type': 'string'},
        'int':    {'type': 'integer'},
        'float':  {'type': 'number'},
        'bool':   {'type': 'boolean'},
    }

    def generate(
        self,
        interfaces: list[YAIFInterface],
        enums: list[YAIFEnum],
        config: YAIFConfig,
    ) -> str:
        schema: dict = {
            '$schema': 'http://json-schema.org/draft-07/schema#',
        }
        if config.title:
            schema['title'] = config.title
        if config.description:
            schema['description'] = config.description

        schema['definitions'] = {}

        for enum in enums:
            schema['definitions'][enum.name] = {
                'type': 'string',
                'enum': enum.values,
            }

        for iface in interfaces:
            props    = {}
            required = []

            for f in iface.fields:
                props[f.name] = self._convert_type(f.type_str)
                if f.default is not None:
                    props[f.name]['default'] = self._convert_default(f.default)
                elif not f.type_str.lower().startswith('optional['):
                    required.append(f.name)

            definition = {'type': 'object', 'properties': props}
            if required:
                definition['required'] = required

            if iface.parent:
                definition = {
                    'allOf': [
                        {'$ref': f'#/definitions/{iface.parent}'},
                        definition,
                    ]
                }

            schema['definitions'][iface.name] = definition

        return json.dumps(schema, indent=2)

    def _convert_type(self, type_str: str) -> dict:
        low = type_str.lower()
        if low in self.TYPE_MAP:
            return dict(self.TYPE_MAP[low])

        generic = re.match(r'^(list|optional|dict)\[(.+)\]$', type_str, re.IGNORECASE)
        if generic:
            kind  = generic.group(1).lower()
            inner = generic.group(2)
            if kind == 'list':
                return {'type': 'array', 'items': self._convert_type(inner)}
            elif kind == 'optional':
                return {'oneOf': [self._convert_type(inner), {'type': 'null'}]}
            elif kind == 'dict':
                parts = [p.strip() for p in inner.split(',')]
                return {'type': 'object', 'additionalProperties': self._convert_type(parts[1])}

        return {'$ref': f'#/definitions/{type_str}'}

    def _convert_default(self, default: str):
        low = default.lower()
        if low == 'true':  return True
        if low == 'false': return False
        if low in ('none', 'null'): return None
        if low == '[]': return []
        if low == '{}': return {}
        try:
            return int(default)
        except ValueError:
            try:
                return float(default)
            except ValueError:
                return default