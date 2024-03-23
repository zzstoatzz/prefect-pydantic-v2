import enum
import os
import re
from typing import Any, Dict, NamedTuple, Set, Type, TypeVar, Union

from prefect.utilities.annotations import NotSet
from prefect.utilities.collections import get_from_dict

T = TypeVar("T", str, int, float, bool, dict, list, None)

PLACEHOLDER_CAPTURE_REGEX = re.compile(r"({{\s*([\w\.\-\[\]$]+)\s*}})")
BLOCK_DOCUMENT_PLACEHOLDER_PREFIX = "prefect.blocks."
VARIABLE_PLACEHOLDER_PREFIX = "prefect.variables."
ENV_VAR_PLACEHOLDER_PREFIX = "$"


class PlaceholderType(enum.Enum):
    STANDARD = "standard"
    BLOCK_DOCUMENT = "block_document"
    VARIABLE = "variable"
    ENV_VAR = "env_var"


class Placeholder(NamedTuple):
    full_match: str
    name: str
    type: PlaceholderType


def determine_placeholder_type(name: str) -> PlaceholderType:
    """
    Determines the type of a placeholder based on its name.

    Args:
        name: The name of the placeholder

    Returns:
        The type of the placeholder
    """
    if name.startswith(BLOCK_DOCUMENT_PLACEHOLDER_PREFIX):
        return PlaceholderType.BLOCK_DOCUMENT
    elif name.startswith(VARIABLE_PLACEHOLDER_PREFIX):
        return PlaceholderType.VARIABLE
    elif name.startswith(ENV_VAR_PLACEHOLDER_PREFIX):
        return PlaceholderType.ENV_VAR
    else:
        return PlaceholderType.STANDARD


def find_placeholders(template: T) -> Set[Placeholder]:
    """
    Finds all placeholders in a template.

    Args:
        template: template to discover placeholders in

    Returns:
        A set of all placeholders in the template
    """
    if isinstance(template, (int, float, bool)):
        return set()
    if isinstance(template, str):
        result = PLACEHOLDER_CAPTURE_REGEX.findall(template)
        return {
            Placeholder(full_match, name, determine_placeholder_type(name))
            for full_match, name in result
        }
    elif isinstance(template, dict):
        return set().union(
            *[find_placeholders(value) for key, value in template.items()]
        )
    elif isinstance(template, list):
        return set().union(*[find_placeholders(item) for item in template])
    else:
        raise ValueError(f"Unexpected type: {type(template)}")


def apply_values(
    template: T, values: Dict[str, Any], remove_notset: bool = True
) -> Union[T, Type[NotSet]]:
    """
    Replaces placeholders in a template with values from a supplied dictionary.

    Will recursively replace placeholders in dictionaries and lists.

    If a value has no placeholders, it will be returned unchanged.

    If a template contains only a single placeholder, the placeholder will be
    fully replaced with the value.

    If a template contains text before or after a placeholder or there are
    multiple placeholders, the placeholders will be replaced with the
    corresponding variable values.

    If a template contains a placeholder that is not in `values`, NotSet will
    be returned to signify that no placeholder replacement occurred. If
    `template` is a dictionary that contains a key with a value of NotSet,
    the key will be removed in the return value unless `remove_notset` is set to False.

    Args:
        template: template to discover and replace values in
        values: The values to apply to placeholders in the template
        remove_notset: If True, remove keys with an unset value

    Returns:
        The template with the values applied
    """
    if isinstance(template, (int, float, bool, type(NotSet), type(None))):
        return template
    if isinstance(template, str):
        placeholders = find_placeholders(template)
        if not placeholders:
            # If there are no values, we can just use the template
            return template
        elif (
            len(placeholders) == 1
            and list(placeholders)[0].full_match == template
            and list(placeholders)[0].type is PlaceholderType.STANDARD
        ):
            # If there is only one variable with no surrounding text,
            # we can replace it. If there is no variable value, we
            # return NotSet to indicate that the value should not be included.
            return get_from_dict(values, list(placeholders)[0].name, NotSet)
        else:
            for full_match, name, placeholder_type in placeholders:
                if placeholder_type is PlaceholderType.STANDARD:
                    value = get_from_dict(values, name, NotSet)
                elif placeholder_type is PlaceholderType.ENV_VAR:
                    name = name.lstrip(ENV_VAR_PLACEHOLDER_PREFIX)
                    value = os.environ.get(name, NotSet)
                else:
                    continue

                if value is NotSet and not remove_notset:
                    continue
                elif value is NotSet:
                    template = template.replace(full_match, "")
                else:
                    template = template.replace(full_match, str(value))

            return template
    elif isinstance(template, dict):
        updated_template = {}
        for key, value in template.items():
            updated_value = apply_values(value, values, remove_notset=remove_notset)
            if updated_value is not NotSet:
                updated_template[key] = updated_value
            elif not remove_notset:
                updated_template[key] = value

        return updated_template
    elif isinstance(template, list):
        updated_list = []
        for value in template:
            updated_value = apply_values(value, values, remove_notset=remove_notset)
            if updated_value is not NotSet:
                updated_list.append(updated_value)
        return updated_list
    else:
        raise ValueError(f"Unexpected template type {type(template).__name__!r}")
