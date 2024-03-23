import logging


class SafeLogger(logging.Logger):
    """
    A logger with extensions for safe emission of logs in our concurrency tooling.
    """
    def getChild(self, suffix: str):
        logger = super().getChild(suffix)
        logger.__class__ = SafeLogger
        return logger


# Use `getLogger` to retain `logger.Manager` behavior
logger = logging.getLogger("prefect._internal")

# Update the class to inject patched behavior
logger.__class__ = SafeLogger
