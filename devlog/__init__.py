from .custom_excepthook import system_excepthook_overwrite
from .decorator import LogOnStart, LogOnError, LogOnEnd
from .stack_trace import set_stack_removal_frames, set_stack_start_frames

__all__ = ["log_on_start", "log_on_end", "log_on_error", "system_excepthook_overwrite", "set_stack_removal_frames",
           "set_stack_start_frames"]

log_on_start = LogOnStart
log_on_end = LogOnEnd
log_on_error = LogOnError
