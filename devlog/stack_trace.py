import traceback
from warnings import warn

DEFAULT_STACK_REMOVAL_FRAMES = 6
DEFAULT_STACK_START_FRAME = 0


def set_stack_removal_frames(frames: int):
    global DEFAULT_STACK_REMOVAL_FRAMES
    if frames < 0:
        warn("frames must be >= 0, setting to absolute value")
        frames = abs(frames)
    DEFAULT_STACK_REMOVAL_FRAMES = frames


def set_stack_start_frames(frames: int):
    global DEFAULT_STACK_START_FRAME
    if frames < 0:
        warn("frames must be >= 0, setting to absolute value")
        frames = abs(frames)
    DEFAULT_STACK_START_FRAME = frames


def get_stack_summary(*args, **kwargs):
    kwargs.setdefault("capture_locals", True)
    stack = traceback.StackSummary.extract(traceback.walk_stack(None), *args, **kwargs)
    stack.reverse()
    # remove stack frames from devlog module at the end of debug stack
    start_frame = -(len(stack) - DEFAULT_STACK_START_FRAME)
    for frame in stack[start_frame:-DEFAULT_STACK_REMOVAL_FRAMES]:
        yield frame
