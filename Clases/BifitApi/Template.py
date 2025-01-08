from dataclasses import dataclass
from Clases.BifitApi.TemplateField import TemplateField

@dataclass
class Template:
    fields: list[TemplateField]
