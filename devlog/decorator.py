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

    @staticmethod
    def get_stack_summary(include_decorator, *args, **kwargs):
        stack = traceback.StackSummary.extract(traceback.walk_stack(None), *args, **kwargs)
        stack.reverse()

        for frame in stack:
            if include_decorator or frame.filename != __file__:  # exclude this file
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


class LogOnStart(LoggingDecorator):
    r"""A logging decorator that logs the start of the function.

    This decorator will log the start of the function using the logger and the handler
    provided in the constructor.

    Attributes:
        log_level: The log level to use for logging.
        message: The message format for the log.
        logger: The logger to use for logging.
            If not set, the logger will be created using the module name of the function.
        handler: The handler to use for logging.
        callable_format_variable: The name of the variable to use for the callable.
        args_kwargs: If True, the message will accept {args} {kwargs} format.
        trace_stack: Whether to include the stack trace in the log.
        trace_stack_message:The message format for the stack trace log.
    """

    def __init__(self, log_level: int = logging.INFO,
                 message: str = None,
                 **kwargs: Any):
        super().__init__(log_level, message, **kwargs)
        if message is None:
            self.message = "Start func {{{cal_var}.__name__}} " \
                           "with args {{args}}, kwargs {{kwargs}}".format(cal_var=self.callable_format_variable)

    def _devlog_executor(self, fn: FunctionType, *args: Tuple[Any], **kwargs: Any) -> Any:
        self._do_logging(fn, *args, **kwargs)
        return super()._devlog_executor(fn, *args, **kwargs)

    def _do_logging(self, fn: FunctionType, *args: Any, **kwargs: Any) -> None:
        logger = self.get_logger(fn)
        extra = {self.callable_format_variable: fn}
        msg = self.build_msg(fn, fn_args=args, fn_kwargs=kwargs, **extra)

        self.log(logger, self.log_level, msg)
        if self.trace_stack:
            stack = traceback.StackSummary(
                LoggingDecorator.get_stack_summary(self.include_decorator, capture_locals=self.capture_locals)
            )
            self.log(logger, logging.DEBUG, "".join(stack.format()).strip())


class LogOnEnd(LoggingDecorator):
    r"""A logging decorator that logs the end of the function.

    This decorator will log the end of the function using the logger and the handler
    provided in the constructor.

    Attributes:
        log_level: The log level to use for logging.
        message: The message format for the log.
        logger: The logger to use for logging.
            If not set, the logger will be created using the module name of the function.
        handler: The handler to use for logging.
        callable_format_variable: The name of the variable to use for the callable.
        args_kwargs: If True, the message will accept {args} {kwargs} format.
        trace_stack: Whether to include the stack trace in the log.
        trace_stack_message:The message format for the stack trace log.
        result_format_variable: The variable to use for the result.
    """

    def __init__(self, log_level: int = logging.INFO,
                 message: str = None, result_format_variable: str = "result",
                 **kwargs: Any):
        super().__init__(log_level, message, **kwargs)
        if message is None:
            self.message = "Successfully run func {{{cal_var}.__name__}} " \
                           "with args {{args}}, kwargs {{kwargs}}".format(cal_var=self.callable_format_variable)
        self.result_format_variable = result_format_variable

    def _devlog_executor(self, fn: FunctionType, *args: Any, **kwargs: Any) -> Any:
        result = super()._devlog_executor(fn, *args, **kwargs)
        self._do_logging(fn, result, *args, **kwargs)

        return result

    def _do_logging(self, fn: FunctionType, result: Any, *args: Tuple[Any], **kwargs: Any) -> None:
        logger = self.get_logger(fn)

        extra = {self.result_format_variable: result, self.callable_format_variable: fn}
        msg = self.build_msg(fn, fn_args=args, fn_kwargs=kwargs, **extra)

        self.log(logger, self.log_level, msg)
        if self.trace_stack:
            stack = traceback.StackSummary(
                LoggingDecorator.get_stack_summary(self.include_decorator, capture_locals=self.capture_locals)
            )
            self.log(logger, logging.DEBUG, "".join(stack.format()).strip())


class LogOnError(LoggingDecorator):
    r"""A logging decorator that logs the error of the function.

    This decorator will log the error of the function using the logger and the handler
    provided in the constructor.

    Attributes:
        log_level: The log level to use for logging.
        message: The message format for the log.
        logger: The logger to use for logging.
            If not set, the logger will be created using the module name of the function.
        handler: The handler to use for logging.
        args_kwargs: If True, the message will accept {args} {kwargs} format.
        trace_stack: Whether to include the stack trace in the log.
        trace_stack_message:The message format for the stack trace log.
        on_exception: The exception that will catch. Empty mean everything.
        reraise: Whether to reraise the exception or supress it.
        exception_format_variable: The variable to use for the error.
    """

    def __init__(self, log_level: int = logging.ERROR,
                 message: str = None,
                 on_exceptions: Optional[Union[Type[BaseException], Tuple[Type[BaseException]], Tuple[()]]] = None,
                 reraise: bool = True, exception_format_variable: str = "error", **kwargs):
        super().__init__(log_level, message, **kwargs)
        if message is None:
            self.message = "Error in func {{{cal_var}.__name__}} " \
                           "with args {{args}}, kwargs {{kwargs}}\n{{{except_var}}}.".format(
                cal_var=self.callable_format_variable,
                except_var=exception_format_variable
            )
        self.on_exceptions: Union[Type[BaseException], Tuple[Type[BaseException]], Tuple[()]] = on_exceptions if \
            on_exceptions is not None else BaseException
        self.reraise = reraise
        self.exception_format_variable = exception_format_variable
        self.capture_locals = self.trace_stack or self.capture_locals

    def _devlog_executor(self, fn: FunctionType, *args: Any, **kwargs: Any) -> Any:
        try:
            return super()._devlog_executor(fn, *args, **kwargs)
        except BaseException as e:
            self._on_error(fn, e, *args, **kwargs)

    def _do_logging(self, fn: FunctionType, *args: Any, **kwargs: Any) -> None:
        logger = self.get_logger(fn)
        full_traceback = traceback.TracebackException(*sys.exc_info(), capture_locals=self.capture_locals)
        custom_traceback = list(LoggingDecorator.get_stack_summary(
            self.include_decorator, capture_locals=self.capture_locals)
        )

        # exclude all the stack trace that are in this module
        for frame in full_traceback.stack:
            if frame.filename != __file__ or self.include_decorator:
                custom_traceback.append(frame)

        full_traceback.stack = traceback.StackSummary(custom_traceback)

        extra = {self.callable_format_variable: fn,
                 self.exception_format_variable: "".join(list(full_traceback.format(chain=True))).strip()}

        msg = self.build_msg(fn, fn_args=args, fn_kwargs=kwargs, **extra)

        self.log(logger, self.log_level, msg)

    def _on_error(self, fn: FunctionType, exception: BaseException, *args: Any, **kwargs: Any) -> None:

        if issubclass(exception.__class__, self.on_exceptions) and not hasattr(exception, "reraised"):
            self._do_logging(fn, *args, **kwargs)
            exception.reraised = True  # Mark the exception as reraised, so no more logging is done.
        if self.reraise:
            raise
