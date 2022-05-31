import traceback

output_file = "crash.log"


def my_except_hook(exception_type, exception_value, traceback_message):
    # traceback.print_tb(traceback_message)
    with open(output_file, encoding="utf-8") as f:
        # save to file
        traceback.print_exception(exception_type, exception_value, traceback_message, file=f)
        print("Stack (most recent stack last):", file=f)
        # output to stdout
        traceback.print_exception(exception_type, exception_value, traceback_message)
        for frame in traceback.TracebackException.from_exception(exception_value, capture_locals=True).stack[1:]:
            # save to a file
            message = "\t{filename}:{lineno} on {line}\n\t\t{locals}".format(
                filename=frame.filename,
                lineno=frame.lineno,
                line=frame.line,
                locals=frame.locals
            )
            print(message, file=f)
            # output to stdout
            print(message)


def system_excepthook_overwrite(out_file=None):
    import sys
    global output_file

    if out_file is not None:
        output_file = out_file
    sys.excepthook = my_except_hook
