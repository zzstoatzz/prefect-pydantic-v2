import logging
from functools import lru_cache
from typing import Dict, Optional


class PrefectLogAdapter(logging.LoggerAdapter):
    """
    Adapter that ensures extra kwargs are passed through correctly; without this
    the `extra` fields set on the adapter would overshadow any provided on a
    log-by-log basis.

    See https://bugs.python.org/issue32732 — the Python team has declared that this is
    not a bug in the LoggingAdapter and subclassing is the intended workaround.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = {**(self.extra or {}), **(kwargs.get("extra") or {})}


        return (msg, kwargs)

    def getChild(
        self, suffix: str, extra: Optional[Dict[str, str]] = None
    ) -> "PrefectLogAdapter":
        if extra is None:
            extra = {}

        return PrefectLogAdapter(
            self.logger.getChild(suffix),
            extra={
                **self.extra,
                **extra,
            },
        )


@lru_cache()
def get_logger(name: str = None) -> logging.Logger:
    """
    Get a `prefect` logger. These loggers are intended for internal use within the
    `prefect` package.

    See `get_run_logger` for retrieving loggers for use within task or flow runs.
    By default, only run-related loggers are connected to the `APILogHandler`.
    """
    parent_logger = logging.getLogger("prefect")

    if name:
        # Append the name if given but allow explicit full names e.g. "prefect.test"
        # should not become "prefect.prefect.test"
        if not name.startswith(parent_logger.name + "."):
            logger = parent_logger.getChild(name)
        else:
            logger = logging.getLogger(name)
    else:
        logger = parent_logger

    return logger
