"""Item-by-item validation of loaded JSON data."""
from typing import Any, TypeVar
import sys
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def validate_l(data: Any, model_class: type[T]) -> list[T]:
    """Validate each item of a JSON array, skipping invalid ones."""
    if not isinstance(data, list):
        raise ValueError("expected a JSON array at the top level")
    validated: list[T] = []
    for i, item in enumerate(data):
        try:
            validated.append(model_class(**item))
        except (ValidationError, TypeError, BaseException) as e:
            print(f"Skipping item {i}: {e}")
            sys.exit(1)
    return validated
