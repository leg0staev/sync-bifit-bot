from dataclasses import dataclass


@dataclass
class TemplateField:
    name: str
    value: str
    type: str
    required: bool
    defaultValue: str
    minimumValue: str
    outType: str
    replace: bool
    prefix: str
    inputName: str
    regexp: str
    mask: str
    available: list[str]
    factor: int
    forPrint: bool
