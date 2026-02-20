[![GitHub latest version](https://img.shields.io/github/v/release/MeGaNeKoS/devlog?style=for-the-badge)](https://github.com/MeGaNeKoS/devlog/releases/latest)
[![Tests](https://img.shields.io/github/actions/workflow/status/MeGaNeKoS/devlog/python-test.yml?label=Tests&style=for-the-badge)](https://github.com/MeGaNeKoS/devlog/actions/workflows/python-test.yml)
[![Publish](https://img.shields.io/github/actions/workflow/status/MeGaNeKoS/devlog/python-publish.yml?label=Publish&style=for-the-badge)](https://github.com/MeGaNeKoS/devlog/actions/workflows/python-publish.yml)
![Size](https://img.shields.io/github/repo-size/MeGaNeKoS/devlog?style=for-the-badge)
![License](https://img.shields.io/github/license/MeGaNeKoS/devlog?style=for-the-badge)

devlog
=====

No more logging in your code business logic with python decorators.

Logging is a very powerful tool for debugging and monitoring your code. But if you are often adding logging
statements, you will quickly find your code overcrowded with them.

Fortunately, you can avoid this by using python decorators. This library provides easy logging for your code without
stealing readability and maintainability. It also provides stack traces with full local variables, value sanitization,
and async support.

**Requires Python 3.9+**

Installation
------------

```bash
pip install python-devlog
```

How to use
----------

Add the decorator to your function. Depending on when you want to log, you can use:

```python
import logging
from devlog import log_on_start, log_on_end, log_on_error

logging.basicConfig(level=logging.DEBUG)


@log_on_start
@log_on_end
def add(a, b):
    return a + b


@log_on_error
def divide(a, b):
    return a / b


if __name__ == '__main__':
    add(1, b=2)
    # INFO:__main__:Start func add with args (1,), kwargs {'b': 2}
    # INFO:__main__:Successfully run func add with args (1,), kwargs {'b': 2}

    divide("abc", "def")
    # ERROR:__main__:Error in func divide with args ('abc', 'def'), kwargs {}
    # 	unsupported operand type(s) for /: 'str' and 'str'.
```

### Async support

All decorators work with async functions automatically:

```python
@log_on_start
@log_on_end
@log_on_error
async def fetch_data(url):
    ...
```

### Value sanitization

Prevent sensitive values from appearing in logs using `Sensitive` or `sanitize_params`:

```python
from devlog import log_on_start, Sensitive


# Option 1: Wrap the value — function receives the real value, logs show "***"
@log_on_start
def login(username, password):
    ...

login("admin", Sensitive("hunter2"))
# INFO:__main__:Start func login with args ('admin', '***'), kwargs {}


# Option 2: Auto-redact by parameter name
@log_on_start(sanitize_params={"password", "token", "secret"})
def connect(host, token):
    ...

connect("example.com", "sk-abc123")
# INFO:__main__:Start func connect with args ('example.com', '***'), kwargs {}
```

`Sensitive` is a transparent proxy — the wrapped function receives the real value. Only devlog log output is redacted.

What devlog can do for you
---------------------------

### Decorators

devlog provides three decorators:

- **log_on_start**: Log when the function is called.
- **log_on_end**: Log when the function finishes successfully.
- **log_on_error**: Log when the function raises an exception.

Use variables in messages
=========================

The message given to decorators is treated as a format string which takes the function arguments as format
arguments.

```python
import logging
from devlog import log_on_start

logging.basicConfig(level=logging.DEBUG)


@log_on_start(logging.INFO, 'Start func {callable.__name__} with args {args}, kwargs {kwargs}')
def hello(name):
    print("Hello, {}".format(name))


if __name__ == "__main__":
    hello("World")
```

Which will print:
```INFO:__main__:Start func hello with args ('World',), kwargs {}```

### Documentation

#### Format variables

The following variables are available in the format string:

| Default variable name | Description                                             | LogOnStart | LogOnEnd | LogOnError |
|-----------------------|---------------------------------------------------------|------------|----------|------------|
| callable              | The function object                                     | Yes        | Yes      | Yes        |
| *args/kwargs*         | The arguments, key arguments passed to the function     | Yes        | Yes      | Yes        |
| result                | The return value of the function                        | No         | Yes      | No         |
| error                 | The error object if the function is finished with error | No         | No       | Yes        |

#### Base arguments

Available arguments in all decorators:

| Argument                 | Description                                                                                                                                                                                   |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| logger                   | The logger object. If no logger is given, devlog will create one with the module name where the function is defined. Default is `logging.getLogger(callable.__module__)`                       |
| handler                  | A custom log handler object. Only available if no logger object is given.                                                                                                                     |
| args_kwargs              | Set `True` to use `{args}`, `{kwargs}` format, or `False` to use function parameter names. Default `True`                                                                                    |
| callable_format_variable | The format variable name for the callable. Default is `callable`                                                                                                                              |
| trace_stack              | Set to `True` to get the full stack trace. Default is `False`                                                                                                                                 |
| capture_locals           | Set to `True` to capture local variables in stack frames. Default is `False` (or `trace_stack` on log_on_error)                                                                               |
| include_decorator        | Set to `True` to include devlog frames in the stack trace. Default is `False`                                                                                                                 |
| sanitize_params          | A set of parameter names to auto-redact in log messages. Default is `None`                                                                                                                    |

#### log_on_start

| Argument | Description                                                                                                                                                                 |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level    | The level of the log message. Default is `logging.INFO`                                                                                                                     |
| message  | The message to log. Can use `{args}` `{kwargs}` or function parameter names, but not both. Default is `Start func {callable.__name__} with args {args}, kwargs {kwargs}`    |

#### log_on_end

| Argument               | Description                                                                                                                                                                            |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level                  | The level of the log message. Default is `logging.INFO`                                                                                                                                |
| message                | The message to log. Can use `{args}` `{kwargs}` or function parameter names, but not both. Default is `Successfully run func {callable.__name__} with args {args}, kwargs {kwargs}`    |
| result_format_variable | The format variable name for the return value. Default is `result`                                                                                                                     |

#### log_on_error

| Argument                  | Description                                                                                                                                                                          |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level                     | The level of the log message. Default is `logging.ERROR`                                                                                                                             |
| message                   | The message to log. Can use `{args}` `{kwargs}` or function parameter names, but not both. Default is `Error in func {callable.__name__} with args {args}, kwargs {kwargs}\n{error}` |
| on_exceptions             | Exception classes to catch and log. Default catches all exceptions.                                                                                                                  |
| reraise                   | Whether to reraise the exception after logging. Default is `True`                                                                                                                    |
| exception_format_variable | The format variable name for the exception. Default is `error`                                                                                                                       |

### Extras

#### Custom exception hook

Override the default exception hook to write crash logs with local variable capture:

```python
import devlog

devlog.system_excepthook_overwrite()  # Overwrite the default exception hook
```

This replaces `sys.excepthook` with devlog's handler, which writes detailed crash information to a file.

| Argument | Description                                                   |
|----------|---------------------------------------------------------------|
| out_file | The path to the file to write the crash log. Default is `crash.log` |
