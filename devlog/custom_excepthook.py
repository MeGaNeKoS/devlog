import sys
import traceback
from typing import Optional, Type
from types import TracebackType


_output_file: str = "crash.log"


def my_except_hook(exception_type: Type[BaseException],
                   exception_value: BaseException,
                   traceback_message: Optional[TracebackType]) -> None:
    """Custom exception hook that writes crash info to a file and stdout."""
    tb_exception = traceback.TracebackException(
        exception_type, exception_value, traceback_message,
        capture_locals=True
    )

    formatted = "".join(tb_exception.format())

    # Print to stdout
    print(formatted, end="")

    # Write to file
    try:
        with open(_output_file, encoding="utf-8", mode="w") as f:
            f.write(formatted)
            f.write("\nStack (most recent stack last):\n")
            for frame in tb_exception.stack:
                message = "\t{filename}:{lineno} on {line}\n\t\t{locals}".format(
                    filename=frame.filename,
                    lineno=frame.lineno,
                    line=frame.line,
                    locals=frame.locals
                )
                f.write(message + "\n")
    except OSError as e:
        print(f"devlog: Failed to write crash log to {_output_file}: {e}", file=sys.stderr)


def system_excepthook_overwrite(out_file: Optional[str] = None) -> None:
    """Override sys.excepthook to write crash logs with local variable capture."""
    global _output_file

    if out_file is not None:
        _output_file = out_file
    sys.excepthook = my_except_hook
