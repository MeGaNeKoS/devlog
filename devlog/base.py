import inspect
import logging
import sys
import traceback
from functools import wraps
from logging import Logger, Handler
from types import FunctionType
from typing import Callable, Any, Dict, Tuple, Optional, Union, Type
from warnings import warn


class WrapCallback:
    r"""A callback that wraps the function and executes it.

    This class is designed to be used as a mix-in for logging callables,
    such as functions or methods. These are not created manually, instead
    they are created from other log decorators in this package.
    """

    # default execute wrapped function
    def _devlog_executor(self, fn: FunctionType, *args: Tuple[Any], **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    def __call__(self, fn: FunctionType) -> Callable[..., Any]:
        @wraps(fn)
        def devlog_wrapper(*args: Tuple[Any], **kwargs: Any) -> Any:
            return self._devlog_executor(fn, *args, **kwargs)

        return devlog_wrapper


class LoggingDecorator(WrapCallback):
    r"""A class that implements the protocol for a logging callable.

    This class are responsible for create logging message for the function
    and log it.

    Attributes:
        log_level: The log level to use for logging.
        message: The message format for the log.
        logger: The logger to use for logging.
            If not set, the logger will be created using the module name of the function.
        handler: The handler to use for logging.
        callable_format_variable: The name of the variable to use for the callable.
        args_kwargs: If True, the message will accept {args} {kwargs} format.
        trace_stack: Whether to include the stack trace in the log.
        capture_locals: Capture the locals of the function.
        include_decorator: Whether to include the decorator in the trace log.
    """

    # Files to exclude from stack traces (populated by submodules)
    _internal_files: set = set()

    def __init__(self, log_level: int, message: str, *, logger: Optional[Logger] = None,
                 handler: Optional[Handler] = None, args_kwargs=True, callable_format_variable="callable",
                 trace_stack: bool = False, capture_locals: bool = False, include_decorator: bool = False):
        self.log_level = log_level
        self.message = message

        if logger is not None and handler is not None:
            warn("logger and handler are both set, the handler will be ignored")
            handler = None

        self._logger = logger
        self._handler = handler

        self.callable_format_variable = callable_format_variable
        self.include_decorator = include_decorator
        self.trace_stack = trace_stack or capture_locals
        self.capture_locals = capture_locals
        self.args_kwargs = args_kwargs

    @staticmethod
    def log(logger: Logger, log_level: int, msg: str) -> None:
        logger.log(log_level, msg)

    def get_logger(self, fn: FunctionType) -> Logger:
        """
        Returns the logger to use for logging.
        if the logger is not set, the logger will be created using the module name of the function.
        and the handler will be added to the logger if any.
        """
        if self._logger is None:
            self._logger = logging.getLogger(fn.__module__)

            if self._handler is not None:
                self._logger.addHandler(self._handler)

        return self._logger

    @classmethod
    def _is_internal_file(cls, filename: str) -> bool:
        return filename in cls._internal_files

    @classmethod
    def get_stack_summary(cls, include_decorator, *args, **kwargs):
        stack = traceback.StackSummary.extract(traceback.walk_stack(None), *args, **kwargs)
        stack.reverse()

        for frame in stack:
            if include_decorator or not cls._is_internal_file(frame.filename):
                yield frame

    @staticmethod
    def bind_param(fn: FunctionType, *args: Tuple[Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Returns a dictionary with all the `parameter`: `value` in the function.
        """
        callable_signature = inspect.signature(fn)
        bound_arguments = callable_signature.bind(*args, **kwargs)
        bounded_param = {param_name: bound_arguments.arguments.get(param_name, param_object.default) for
                         param_name, param_object in bound_arguments.signature.parameters.items()}

        return bounded_param

    def build_msg(self, fn: FunctionType, fn_args: Any, fn_kwargs: Any, **extra: Any) -> str:
        """
        Builds the message log using the message format and the function arguments.
        """
        format_kwargs = extra

        if self.args_kwargs:
            format_kwargs["args"] = fn_args
            format_kwargs["kwargs"] = fn_kwargs
        else:
            format_kwargs.update(self.bind_param(fn, *fn_args, **fn_kwargs))
        return self.message.format(**format_kwargs)


# Register this file as internal
LoggingDecorator._internal_files.add(__file__)
