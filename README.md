devlog
=====

No more logging in your code business logic with python decorators.

Logging is a very powerful tool for debugging and monitoring your code. But if you are often ommitting logging
statements, you will quickly find yourself overcrowded with logging statements.

Fortunately, you could avoid this by using the python decorator. This library provide easy logging for your code without
stealing readability and maintainability. Furthermore, it also provides stack trace to get full local variable on the
function.

How to use:
-----------
To use this library, you just need to add the decorator to your function. Depending on when you want to log, you can use
the decorator as below:

```python
import logging

from devlog import log_on_start, log_on_end, log_on_error

logging.basicConfig(level=logging.DEBUG)


@log_on_start
@log_on_end
def test_1(a, b):
    return a + b


@log_on_error
def test_2(a, b):
    return a / b

if __name__ == '__main__':
    test_1(1, b=2)
    # INFO:__main__:Start func test_1 with args (1,), kwargs {'b': 2}
    # INFO:__main__:Successfully run func test_1 with args (1,), kwargs {'b': 2}
    
    test_2("abc", "def")
    # ERROR:__main__:Error in func test_2 with args ('abc', 'def'), kwargs {}
    # 	unsupported operand type(s) for /: 'str' and 'str'.
```

What devlog can do for you
---------------------------

### Decorators

devlog provides three different decorators:

- LogOnStart: Log when the function is called.
- LogOnEnd: Log when the function is finished.
- LogOnError: Log when the function is finished with error.

Use variables in messages
=========================
The message given to decorators are treated as a format string which takes the function arguments as the format
arguments.

The following example shows how to use variables in messages:

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

#### format variables

The following variables are available in the format string:

| Default variable name | Description                                             | LogOnStart | LogOnEnd | LogOnError |
|-----------------------|---------------------------------------------------------|------------|----------|------------|
| callable              | The function object                                     | Yes        | Yes      | Yes        |
| *args/kwargs*         | The arguments, key arguments passed to the function     | Yes        | Yes      | Yes        |
| result                | The return value of the function                        | No         | Yes      | No         |
| error                 | The error object if the function is finished with error | No         | No       | Yes        |

#### base arguments

Available arguments in all decorators are:

| Arguments                | Description                                                                                                                                                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| logger                   | The logger object. If no logger is given, the devlog will create a logger object with the name of the module where the function is defined. Default is `logging.getLogger(callable.__name__)`                                   |
| handler                  | A custom log handler object. Only available if no logger object is given,                                                                                                                                                       |
| args_kwargs              | Set true if the message format using args, kwargs format or false to use function parameter name format. Default `True`                                                                                                         |
| callable_format_variable | The format variable to use for callable. Default is `callable`                                                                                                                                                                  |
| trace_stack              | Set to True if you want to get the full stack trace along with local variable. Default is `False`                                                                                                                               |
| trace_stack_message      | The message to use for the stack trace. Default is `{frame.filename}:{frame.lineno} at function {frame.name}@{frame.line}\n\t\t{frame.locals}`<br/>Note: only accept frame as format arguments, frame is a FrameSummary objects |                     

#### log_on_start

| Arguments | Description                                                                                                                                                                 |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level     | The level of the log message. Default is `logging.INFO`                                                                                                                     |
| message   | The message to log. Could using {args} {kwargs} or function parameter name but not both. <br/>Default is `Start func {callable.__name__} with args {args}, kwargs {kwargs}` |

#### log_on_end

| Arguments              | Description                                                                                                                                                                            |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level                  | The level of the log message. Default is `logging.INFO`                                                                                                                                |
| message                | The message to log. Could using {args} {kwargs} or function parameter name but not both. <br/>Default is `Successfully run func {callable.__name__} with args {args}, kwargs {kwargs}` |
| result_format_variable | The format variable to use for reference the return from callable. Default is `result`                                                                                                 |

#### log_on_error

| Arguments                 | Description                                                                                                                                                                            |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| level                     | The level of the log message. Default is `logging.ERROR`                                                                                                                               |
| message                   | The message to log. Could using {args} {kwargs} or function parameter name but not both. <br/>Default is `Successfully run func {callable.__name__} with args {args}, kwargs {kwargs}` |
| on_exceptions             | A tuple containing exception classes or a single exception, which should get caught and trigger the logging. Default is `tuple()` (All exception will get caught)                      |
| reraise                   | Control whether the exception should be reraised after logging. Default is `True`                                                                                                      | 
| exception_format_variable | The format variable to use for reference the exception raised in callable. Default is `error`                                                                                          |


### Extras
#### Stack trace
The stack trace configuration.

| method                   | Description                                                                                                                                        |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| set_stack_start_frames   | The number of frames to skip at the start (positive value). Default is `0`                                                                         |
| set_stack_removal_frames | The number of frames to remove from the back of the stack trace (positive value). Default is `6` (the last 6 frame usually from the devlog module) |

#### Custom exception hook
Override the default exception hook with a custom function.

```python
import devlog

devlog.system_excepthook_overwrite() # Overwrite the default exception hook
```
This will replace the sys.excepthook with the devlog.excepthook.

| Arguments | Description                                                   |
|-----------|---------------------------------------------------------------|
| out_file  | The path to the file to write the log. Default is `crash.log` |
