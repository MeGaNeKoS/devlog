import operator
from typing import Any


class Sensitive:
    """Transparent proxy that marks a value for redaction in devlog logs only.

    The wrapped value passes through to functions unchanged — all attribute access,
    operators, iteration, etc. are delegated to the real value. Redaction only
    happens when devlog formats log messages.

    Usage:
        password = Sensitive("hunter2")
        login(password)  # function receives "hunter2" normally
        # but devlog logs show: login(password='***')
    """

    __slots__ = ('_devlog_value', '_devlog_mask')

    def __init__(self, value: Any, mask: str = "***"):
        object.__setattr__(self, '_devlog_value', value)
        object.__setattr__(self, '_devlog_mask', mask)

    @property
    def real_value(self) -> Any:
        return object.__getattribute__(self, '_devlog_value')

    @property
    def mask(self) -> str:
        return object.__getattribute__(self, '_devlog_mask')

    # --- transparent proxy ---
    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, '_devlog_value'), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, '_devlog_value'), name, value)

    def __delattr__(self, name: str) -> None:
        delattr(object.__getattribute__(self, '_devlog_value'), name)

    def __str__(self) -> str:
        return str(object.__getattribute__(self, '_devlog_value'))

    def __repr__(self) -> str:
        return repr(object.__getattribute__(self, '_devlog_value'))

    def __bool__(self) -> bool:
        return bool(object.__getattribute__(self, '_devlog_value'))

    def __len__(self) -> int:
        return len(object.__getattribute__(self, '_devlog_value'))

    def __iter__(self):
        return iter(object.__getattribute__(self, '_devlog_value'))

    def __contains__(self, item: Any) -> bool:
        return item in object.__getattribute__(self, '_devlog_value')

    def __getitem__(self, key: Any) -> Any:
        return object.__getattribute__(self, '_devlog_value')[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        object.__getattribute__(self, '_devlog_value')[key] = value

    def __delitem__(self, key: Any) -> None:
        del object.__getattribute__(self, '_devlog_value')[key]

    def __eq__(self, other: Any) -> bool:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val == other_val

    def __hash__(self) -> int:
        return hash(object.__getattribute__(self, '_devlog_value'))

    def __lt__(self, other: Any) -> bool:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val < other_val

    def __le__(self, other: Any) -> bool:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val <= other_val

    def __gt__(self, other: Any) -> bool:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val > other_val

    def __ge__(self, other: Any) -> bool:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val >= other_val

    def __add__(self, other: Any) -> Any:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val + other_val

    def __radd__(self, other: Any) -> Any:
        val = object.__getattribute__(self, '_devlog_value')
        return other + val

    def __mul__(self, other: Any) -> Any:
        val = object.__getattribute__(self, '_devlog_value')
        other_val = other.real_value if isinstance(other, Sensitive) else other
        return val * other_val

    def __rmul__(self, other: Any) -> Any:
        val = object.__getattribute__(self, '_devlog_value')
        return other * val

    def __int__(self) -> int:
        return int(object.__getattribute__(self, '_devlog_value'))

    def __float__(self) -> float:
        return float(object.__getattribute__(self, '_devlog_value'))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return object.__getattribute__(self, '_devlog_value')(*args, **kwargs)


def unwrap_sensitive(value: Any) -> Any:
    """Unwrap a Sensitive value to its real value, or return as-is."""
    if isinstance(value, Sensitive):
        return value.real_value
    return value


def format_value(value: Any, param_name: str = "",
                 sanitize_params: set = None) -> str:
    """Format a value for log display, applying redaction as needed."""
    if isinstance(value, Sensitive):
        return object.__getattribute__(value, '_devlog_mask')
    if sanitize_params and param_name in sanitize_params:
        return "***"
    return repr(value)
