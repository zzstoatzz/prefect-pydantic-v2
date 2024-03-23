"""
Utilities for Python version compatibility
""" # noqa

import asyncio
import sys
from shutil import copytree  # noqa
from signal import raise_signal  # noqa

if sys.version_info < (3, 10):
    import importlib_metadata # noqa
    from importlib_metadata import EntryPoint, EntryPoints, entry_points # noqa
else:
    import importlib.metadata as importlib_metadata # noqa
    from importlib.metadata import EntryPoint, EntryPoints, entry_points # noqa

if sys.version_info < (3, 9):
    # https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread

    import functools # noqa

    async def asyncio_to_thread(fn, *args, **kwargs): # noqa
        loop = asyncio.get_running_loop() # noqa
        return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs)) # noqa

else:
    from asyncio import to_thread as asyncio_to_thread # noqa

if sys.platform != "win32": # noqa
    from asyncio import ThreadedChildWatcher # noqa
