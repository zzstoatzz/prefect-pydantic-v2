"""
Internal utilities for tests.
"""

import sys
import warnings
from contextlib import contextmanager
from pprint import pprint
from typing import Dict, List, Union


def exceptions_equal(a, b):
    """
    Exceptions cannot be compared by `==`. They can be compared using `is` but this
    will fail if the exception is serialized/deserialized so this utility does its
    best to assert equality using the type and args used to initialize the exception
    """
    if a == b:
        return True
    return type(a) == type(b) and getattr(a, "args", None) == getattr(b, "args", None)


# AsyncMock has a new import path in Python 3.8+

if sys.version_info < (3, 8):
    # https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock
    from mock import AsyncMock  # noqa
else:
    from unittest.mock import AsyncMock  # noqa

# MagicMock supports async magic methods in Python 3.8+

if sys.version_info < (3, 8):
    from unittest.mock import MagicMock as _MagicMock
    from unittest.mock import MagicProxy as _MagicProxy

    class MagicMock(_MagicMock):
        def _mock_set_magics(self):
            """Patch to include proxies for async methods"""
            super()._mock_set_magics()

            for attr in {"__aenter__", "__aexit__", "__anext__"}:
                if not hasattr(MagicMock, attr):
                    setattr(MagicMock, attr, _MagicProxy(attr, self))

        def _get_child_mock(self, **kw):
            """Patch to return async mocks for async methods"""
            # This implementation copied from unittest in Python 3.8
            _new_name = kw.get("_new_name")
            if _new_name in self.__dict__.get("_spec_asyncs", {}):
                return AsyncMock(**kw)

            _type = type(self)
            if issubclass(_type, MagicMock) and _new_name in {
                "__aenter__",
                "__aexit__",
                "__anext__",
            }:
                if self._mock_sealed:
                    attribute = "." + kw["name"] if "name" in kw else "()"
                    mock_name = self._extract_mock_name() + attribute
                    raise AttributeError(mock_name)

                return AsyncMock(**kw)

            return super()._get_child_mock(**kw)

else:
    from unittest.mock import MagicMock


def kubernetes_environments_equal(
    actual: List[Dict[str, str]],
    expected: Union[List[Dict[str, str]], Dict[str, str]],
):
    # Convert to a required format and sort by name
    if isinstance(expected, dict):
        expected = [{"name": key, "value": value} for key, value in expected.items()]

    expected = list(sorted(expected, key=lambda item: item["name"]))

    # Just sort the actual so the format can be tested
    if isinstance(actual, dict):
        raise TypeError(
            "Unexpected type 'dict' for 'actual' kubernetes environment. "
            "Expected 'List[dict]'. Did you pass your arguments in the wrong order?"
        )

    actual = list(sorted(actual, key=lambda item: item["name"]))

    print("---- Actual Kubernetes environment ----")
    pprint(actual, width=180)
    print()
    print("---- Expected Kubernetes environment ----")
    pprint(expected, width=180)
    print()

    for actual_item, expected_item in zip(actual, expected):
        if actual_item != expected_item:
            print("----- First difference in Kubernetes environments -----")
            print(f"Actual: {actual_item}")
            print(f"Expected: {expected_item}")
            break

    return actual == expected


@contextmanager
def assert_does_not_warn(ignore_warnings=[]):
    """
    Converts warnings to errors within this context to assert warnings are not raised,
    except for those specified in ignore_warnings.

    Parameters:
    - ignore_warnings: List of warning types to ignore. Example: [DeprecationWarning, UserWarning]
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for warning_type in ignore_warnings:
            warnings.filterwarnings("ignore", category=warning_type)

        try:
            yield
        except Warning as warning:
            raise AssertionError(f"Warning was raised. {warning!r}") from warning



def assert_blocks_equal(
    found, expected, exclude_private: bool = True, **kwargs
) -> bool:
    assert isinstance(
        found, type(expected)
    ), f"Unexpected type {type(found).__name__}, expected {type(expected).__name__}"

    if exclude_private:
        exclude = set(kwargs.pop("exclude", set()))
        for attr, _ in found._iter():
            if attr.startswith("_"):
                exclude.add(attr)

    assert found.dict(exclude=exclude, **kwargs) == expected.dict(
        exclude=exclude, **kwargs
    )


def a_test_step(**kwargs):
    kwargs.update({"output1": 1, "output2": ["b", 2, 3]})
    return kwargs


def b_test_step(**kwargs):
    kwargs.update({"output1": 1, "output2": ["b", 2, 3]})
    return kwargs
