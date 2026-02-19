"""
YAIF code generators.
"""

from .python import PythonGenerator
from .typescript import TypeScriptGenerator
from .jsonschema import JSONSchemaGenerator
from .html import HTMLGenerator
from .discord import DiscordGenerator

GENERATORS = {
    'python':     PythonGenerator(),
    'typescript': TypeScriptGenerator(),
    'jsonschema': JSONSchemaGenerator(),
    'html':       HTMLGenerator(),
    'discord':    DiscordGenerator(),
}

FILE_EXTENSIONS = {
    'python':     '.py',
    'typescript': '.ts',
    'jsonschema': '.json',
    'html':       '.html',
    'discord':    '.txt',
}