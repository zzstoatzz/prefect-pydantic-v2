# isort: skip_file

# Setup version and path constants

from . import _version
import pathlib
import warnings
import sys

__version__ = _version.__version__

# The absolute path to this module
__module_path__ = pathlib.Path(__file__).parent
# The absolute path to the root of the repository, only valid for use during development
__development_base_path__ = __module_path__.parents[1]

# The absolute path to the built UI within the Python module, used by
# `prefect server start` to serve a dynamic build of the UI
__ui_static_subpath__ = __module_path__ / "server" / "ui_build"

# The absolute path to the built UI within the Python module
__ui_static_path__ = __module_path__ / "server" / "ui"

del _version, pathlib

if sys.version_info < (3, 8):
    warnings.warn(
        (
            "Prefect dropped support for Python 3.7 when it reached end-of-life"
            " . To use new versions of Prefect, you will need"
            " to upgrade to Python 3.8+. See https://devguide.python.org/versions/ for "
            " more details."
        ),
        FutureWarning,
        stacklevel=2,
    )


# Import user-facing API
from prefect.utilities.annotations import unmapped, allow_failure


# Declare API for type-checkers
__all__ = [
    "allow_failure",
    "unmapped",
]