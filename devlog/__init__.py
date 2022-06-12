from .custom_excepthook import system_excepthook_overwrite
from .decorator import LogOnStart, LogOnError, LogOnEnd

__all__ = ["log_on_start", "log_on_end", "log_on_error", "system_excepthook_overwrite"]


def log_on_start(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return LogOnStart(**kwargs)(args[0])
    return LogOnStart(*args, **kwargs)


def log_on_end(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return LogOnEnd(**kwargs)(args[0])
    return LogOnEnd(*args, **kwargs)


def log_on_error(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return LogOnError(**kwargs)(args[0])
    return LogOnError(*args, **kwargs)
