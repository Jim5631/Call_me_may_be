"""Pydantic models and JSON loading helpers."""
import json
from typing import Any

from pydantic import BaseModel


def load(filepath: str) -> Any:
    """Load and parse a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class Parameter(BaseModel):
    """Type description of a function parameter or return value."""

    type: str


class Function(BaseModel):
    """A function definition from functions_definition.json."""

    name: str
    description: str
    parameters: dict[str, Parameter]
    returns: Parameter


class InputModel(BaseModel):
    """A single test prompt."""

    prompt: str


class OutputModel(BaseModel):
    """A single function call result."""

    prompt: str
    name: str
    parameters: dict[str, Any]
