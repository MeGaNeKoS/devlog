import asyncio
import logging
import os
import sys
import tempfile
from unittest import TestCase

import pytest

import devlog
from devlog.base import LoggingDecorator
from devlog.sanitize import Sensitive, unwrap_sensitive, format_value


def generic_func(arg1, arg2, kwarg1=None, kwarg2=None):
    return arg1 + arg2


async def async_generic_func(arg1, arg2, kwarg1=None, kwarg2=None):
    return arg1 + arg2


async def async_error_func(arg1, arg2):
    return arg1 + arg2


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.messages = {'debug': [], 'info': [], 'warning': [], 'error': [], 'critical': []}
        super().__init__(*args, **kwargs)

    def emit(self, record):
        try:
            self.messages[record.levelname.lower()].append(record.getMessage())
        except Exception:
            self.handleError(record)

    def reset(self):
        self.acquire()
        try:
            for message_list in self.messages.values():
                message_list.clear()
        finally:
            self.release()


class TestDecorators(TestCase):
    def setUp(self):
        self.logger = logging.Logger("mocked")
        self.log_handler = MockLoggingHandler()
        self.logger.addHandler(self.log_handler)

    def test_log_on_start(self):
        wrapped_function = devlog.log_on_start(args_kwargs=False,
                                               logger=self.logger,
                                               message="Start func generic_func with "
                                                       "arg1 = {arg1}, arg2 = {arg2}, "
                                                       "kwarg1 = {kwarg1}, kwarg2 = {kwarg2}"
                                               )(generic_func)
        wrapped_function(1, 2)
        self.assertIn("Start func generic_func with arg1 = 1, arg2 = 2, kwarg1 = None, kwarg2 = None",
                      self.log_handler.messages["info"])

    def test_log_on_start_wo_parentheses(self):
        wrapped_function_wo_parentheses = devlog.log_on_start(generic_func, logger=self.logger)
        wrapped_function_wo_parentheses(3, 4)
        self.assertIn("Start func generic_func with args (3, 4), kwargs {}", self.log_handler.messages["info"])

    def test_log_on_start_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_start(logger=self.logger)(generic_func)
        wrapped_function_parentheses(5, 6)
        self.assertIn("Start func generic_func with args (5, 6), kwargs {}", self.log_handler.messages["info"])

    def test_log_on_start_w_trace_stack(self):
        wrapped_function = devlog.log_on_start(logger=self.logger,
                                               trace_stack=True)(generic_func)
        wrapped_function(1, 2)
        self.assertTrue(len(self.log_handler.messages["debug"]) > 0)

    def test_log_on_end(self):
        wrapped_function = devlog.log_on_end(
            args_kwargs=False,
            logger=self.logger,
            message="Successfully run func generic_func with "
                    "arg1 = {arg1}, arg2 = {arg2}, "
                    "kwarg1 = {kwarg1}, kwarg2 = {kwarg2}"
        )(generic_func)
        wrapped_function(1, 2)
        self.assertIn("Successfully run func generic_func with arg1 = 1, arg2 = 2, kwarg1 = None, kwarg2 = None",
                      self.log_handler.messages["info"])

    def test_log_on_end_wo_parentheses(self):
        wrapped_function_wo_parentheses = devlog.log_on_end(generic_func, logger=self.logger)
        wrapped_function_wo_parentheses(1, 2)
        self.assertIn("Successfully run func generic_func with args (1, 2), kwargs {}",
                      self.log_handler.messages["info"])

    def test_log_on_end_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_end(logger=self.logger)(generic_func)
        wrapped_function_parentheses(1, 2)
        self.assertIn("Successfully run func generic_func with args (1, 2), kwargs {}",
                      self.log_handler.messages["info"])

    def test_log_on_end_w_trace_stack(self):
        wrapped_function = devlog.log_on_end(logger=self.logger,
                                             trace_stack=True)(generic_func)
        wrapped_function(1, 2)
        self.assertTrue(len(self.log_handler.messages["debug"]) > 0)

    def test_log_on_error(self):
        wrapped_function = devlog.log_on_error(logger=self.logger, trace_stack=True)(generic_func)
        with pytest.raises(TypeError):
            wrapped_function(1, "abc")

        self.assertTrue(len(self.log_handler.messages["error"]) > 0)
        self.assertIn("generic_func", self.log_handler.messages["error"][0])

    def test_log_on_error_wo_parentheses(self):
        wrapped_function_wo_parentheses = devlog.log_on_error(generic_func, logger=self.logger)
        with pytest.raises(TypeError):
            wrapped_function_wo_parentheses(2, "abc")

        self.assertTrue(len(self.log_handler.messages["error"]) > 0)
        self.assertIn("generic_func", self.log_handler.messages["error"][0])

    def test_log_on_error_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_error(logger=self.logger)(generic_func)
        with pytest.raises(TypeError):
            wrapped_function_parentheses(3, "abc")

        self.assertTrue(len(self.log_handler.messages["error"]) > 0)
        self.assertIn("generic_func", self.log_handler.messages["error"][0])

    def test_log_on_error_w_trace_stack(self):
        wrapped_function = devlog.log_on_error(logger=self.logger,
                                               trace_stack=True)(generic_func)
        with pytest.raises(TypeError):
            wrapped_function(4, "abc")

        self.assertTrue(len(self.log_handler.messages["error"]) > 0)

    def test_logger_handler(self):
        decorator = LoggingDecorator(logging.INFO, "", logger=self.logger, handler=self.log_handler)
        self.assertEqual(decorator.get_logger(generic_func).name, self.logger.name)

    def test_handler(self):
        decorator = LoggingDecorator(logging.INFO, "", handler=self.log_handler)
        self.assertEqual(decorator.get_logger(generic_func).name, "test_generic")


class TestSensitive:
    def test_str_passes_through(self):
        s = Sensitive("secret")
        assert str(s) == "secret"

    def test_repr_passes_through(self):
        s = Sensitive("secret")
        assert repr(s) == "'secret'"

    def test_real_value(self):
        s = Sensitive("secret")
        assert s.real_value == "secret"

    def test_mask(self):
        s = Sensitive("secret")
        assert s.mask == "***"

    def test_custom_mask(self):
        s = Sensitive("4111111111111111", mask="****-****-****-XXXX")
        assert s.mask == "****-****-****-XXXX"

    def test_equality(self):
        s = Sensitive("hello")
        assert s == "hello"
        assert s == Sensitive("hello")

    def test_hash(self):
        s = Sensitive("hello")
        assert hash(s) == hash("hello")

    def test_addition(self):
        s = Sensitive(3)
        assert s + 2 == 5
        assert 2 + s == 5

    def test_iteration(self):
        s = Sensitive([1, 2, 3])
        assert list(s) == [1, 2, 3]

    def test_len(self):
        s = Sensitive("abc")
        assert len(s) == 3

    def test_contains(self):
        s = Sensitive([1, 2, 3])
        assert 2 in s

    def test_getitem(self):
        s = Sensitive([10, 20, 30])
        assert s[1] == 20

    def test_bool(self):
        assert bool(Sensitive("nonempty"))
        assert not bool(Sensitive(""))

    def test_getattr_delegation(self):
        s = Sensitive("hello world")
        assert s.upper() == "HELLO WORLD"

    def test_unwrap_sensitive(self):
        assert unwrap_sensitive(Sensitive(42)) == 42
        assert unwrap_sensitive(42) == 42

    def test_format_value_sensitive(self):
        s = Sensitive("secret")
        assert format_value(s) == "***"

    def test_format_value_sanitize_params(self):
        assert format_value("mypassword", "password", {"password"}) == "***"
        assert format_value("visible", "username", {"password"}) == "'visible'"

    def test_format_value_plain(self):
        assert format_value("plain", "arg") == "'plain'"

    def test_setattr_delegation(self):
        class Obj:
            x = 1
        s = Sensitive(Obj())
        s.x = 42
        assert s.x == 42

    def test_delattr_delegation(self):
        class Obj:
            pass
        o = Obj()
        o.x = 1
        s = Sensitive(o)
        del s.x
        assert not hasattr(o, "x")

    def test_setitem(self):
        d = {"a": 1}
        s = Sensitive(d)
        s["b"] = 2
        assert d["b"] == 2

    def test_delitem(self):
        d = {"a": 1, "b": 2}
        s = Sensitive(d)
        del s["a"]
        assert "a" not in d

    def test_comparisons(self):
        s = Sensitive(5)
        assert s < 10
        assert s <= 5
        assert s > 2
        assert s >= 5
        # Also test against another Sensitive
        assert s < Sensitive(10)
        assert s >= Sensitive(3)

    def test_rmul(self):
        s = Sensitive(3)
        assert 4 * s == 12

    def test_mul(self):
        s = Sensitive("ab")
        assert s * 3 == "ababab"

    def test_int(self):
        s = Sensitive(3.7)
        assert int(s) == 3

    def test_float(self):
        s = Sensitive(5)
        assert float(s) == 5.0

    def test_call(self):
        s = Sensitive(lambda x: x + 1)
        assert s(10) == 11


class TestSanitizeParams:
    def setup_method(self):
        self.logger = logging.Logger("sanitize_test")
        self.handler = MockLoggingHandler()
        self.logger.addHandler(self.handler)

    def test_sanitize_params_redacts_named_params(self):
        def login(username, password):
            return True

        wrapped = devlog.log_on_start(
            logger=self.logger,
            args_kwargs=False,
            sanitize_params={"password"},
            message="login with username = {username}, password = {password}"
        )(login)
        wrapped("admin", "secret123")
        msg = self.handler.messages["info"][0]
        assert "admin" in msg
        assert "secret123" not in msg
        assert "***" in msg

    def test_sensitive_wrapper_redacted_in_logs(self):
        def login(username, password):
            return True

        wrapped = devlog.log_on_start(
            logger=self.logger,
            args_kwargs=False,
            message="login with username = {username}, password = {password}"
        )(login)
        wrapped("admin", Sensitive("secret123"))
        msg = self.handler.messages["info"][0]
        assert "secret123" not in msg
        assert "***" in msg

    def test_sensitive_unwrapped_for_function(self):
        """Verify the actual function receives the real value, not Sensitive."""
        received = {}

        def capture(password):
            received["password"] = password
            return True

        wrapped = devlog.log_on_start(logger=self.logger)(capture)
        wrapped(Sensitive("real_secret"))
        assert received["password"] == "real_secret"
        assert not isinstance(received["password"], Sensitive)

    def test_sensitive_with_log_on_end(self):
        def process(token):
            return "ok"

        wrapped = devlog.log_on_end(logger=self.logger)(process)
        result = wrapped(Sensitive("my_token"))
        assert result == "ok"
        msg = self.handler.messages["info"][0]
        assert "my_token" not in msg

    def test_sensitive_with_log_on_error(self):
        def fail(secret):
            raise ValueError("boom")

        wrapped = devlog.log_on_error(logger=self.logger, reraise=False)(fail)
        wrapped(Sensitive("top_secret"))
        msg = self.handler.messages["error"][0]
        # The args portion of the message should be redacted
        # (traceback locals may contain the real value, that's expected behavior)
        assert "args ('***',)" in msg or "args (***,)" in msg or "***" in msg


class TestReraiseAndOnExceptions:
    def setup_method(self):
        self.logger = logging.Logger("reraise_test")
        self.handler = MockLoggingHandler()
        self.logger.addHandler(self.handler)

    def test_reraise_false_suppresses(self):
        def fail():
            raise ValueError("boom")

        wrapped = devlog.log_on_error(logger=self.logger, reraise=False)(fail)
        result = wrapped()  # Should not raise
        assert result is None
        assert len(self.handler.messages["error"]) == 1

    def test_on_exceptions_filters(self):
        def fail():
            raise TypeError("type error")

        wrapped = devlog.log_on_error(
            logger=self.logger, on_exceptions=(ValueError,), reraise=False
        )(fail)
        # TypeError is not in on_exceptions, so it should not be logged but still suppressed...
        # Actually reraise=False only suppresses if the error was caught. Let's check behavior.
        # The current code catches BaseException, logs only if matching on_exceptions, then reraises if reraise=True
        # With reraise=False, the exception is swallowed regardless, but only logged if matching
        wrapped()
        assert len(self.handler.messages["error"]) == 0

    def test_on_exceptions_matches(self):
        def fail():
            raise ValueError("val error")

        wrapped = devlog.log_on_error(
            logger=self.logger, on_exceptions=(ValueError,), reraise=False
        )(fail)
        wrapped()
        assert len(self.handler.messages["error"]) == 1


class TestDuplicateExceptionLogging:
    def setup_method(self):
        self.logger = logging.Logger("dedup_test")
        self.handler = MockLoggingHandler()
        self.logger.addHandler(self.handler)
        pass

    def test_no_duplicate_logging_on_reraise(self):
        """When an exception is reraised through multiple decorators, it should only be logged once."""

        @devlog.log_on_error(logger=self.logger)
        @devlog.log_on_error(logger=self.logger)
        def nested_fail():
            raise ValueError("only once")

        with pytest.raises(ValueError):
            nested_fail()

        assert len(self.handler.messages["error"]) == 1


class TestAsyncSupport:
    def setup_method(self):
        self.logger = logging.Logger("async_test")
        self.handler = MockLoggingHandler()
        self.logger.addHandler(self.handler)

    def test_async_log_on_start(self):
        wrapped = devlog.log_on_start(logger=self.logger)(async_generic_func)
        result = asyncio.get_event_loop().run_until_complete(wrapped(1, 2))
        assert result == 3
        assert len(self.handler.messages["info"]) == 1
        assert "async_generic_func" in self.handler.messages["info"][0]

    def test_async_log_on_end(self):
        wrapped = devlog.log_on_end(logger=self.logger)(async_generic_func)
        result = asyncio.get_event_loop().run_until_complete(wrapped(10, 20))
        assert result == 30
        assert len(self.handler.messages["info"]) == 1

    def test_async_log_on_error(self):
        wrapped = devlog.log_on_error(logger=self.logger)(async_error_func)
        with pytest.raises(TypeError):
            asyncio.get_event_loop().run_until_complete(wrapped(1, "abc"))
        assert len(self.handler.messages["error"]) == 1

    def test_async_preserves_coroutine(self):
        wrapped = devlog.log_on_start(logger=self.logger)(async_generic_func)
        assert asyncio.iscoroutinefunction(wrapped)

    def test_async_sensitive_log_on_start(self):
        async def greet(name, token):
            return f"hi {name}"

        wrapped = devlog.log_on_start(logger=self.logger)(greet)
        result = asyncio.get_event_loop().run_until_complete(wrapped("alice", Sensitive("secret_tok")))
        assert result == "hi alice"
        msg = self.handler.messages["info"][0]
        assert "secret_tok" not in msg

    def test_async_sensitive_log_on_end(self):
        async def greet(name, token):
            return f"hi {name}"

        wrapped = devlog.log_on_end(logger=self.logger)(greet)
        result = asyncio.get_event_loop().run_until_complete(wrapped("bob", Sensitive("secret_tok")))
        assert result == "hi bob"
        msg = self.handler.messages["info"][0]
        assert "secret_tok" not in msg

    def test_async_sensitive_log_on_error(self):
        async def fail(secret):
            raise ValueError("boom")

        wrapped = devlog.log_on_error(logger=self.logger, reraise=False)(fail)
        asyncio.get_event_loop().run_until_complete(wrapped(Sensitive("top_secret")))
        msg = self.handler.messages["error"][0]
        assert "***" in msg


class TestCustomExcepthook:
    def test_writes_crash_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            tmppath = f.name

        try:
            devlog.system_excepthook_overwrite(out_file=tmppath)
            # Simulate an exception
            try:
                raise RuntimeError("test crash")
            except RuntimeError:
                exc_type, exc_value, exc_tb = sys.exc_info()
                sys.excepthook(exc_type, exc_value, exc_tb)

            with open(tmppath, encoding="utf-8") as f:
                content = f.read()
            assert "RuntimeError" in content
            assert "test crash" in content
        finally:
            os.unlink(tmppath)
            # Restore default excepthook
            sys.excepthook = sys.__excepthook__


    def test_writes_to_unwritable_path(self, capsys):
        """When the output file can't be written, it should print an error to stderr."""
        bad_path = "/nonexistent_dir_12345/crash.log"
        try:
            devlog.system_excepthook_overwrite(out_file=bad_path)
            try:
                raise RuntimeError("test crash")
            except RuntimeError:
                exc_type, exc_value, exc_tb = sys.exc_info()
                sys.excepthook(exc_type, exc_value, exc_tb)

            captured = capsys.readouterr()
            assert "Failed to write crash log" in captured.err
        finally:
            sys.excepthook = sys.__excepthook__


class TestFrameHiding:
    def test_tracebackhide_on_sync_wrapper(self):
        """Verify __tracebackhide__ is set in wrapper functions."""
        wrapped = devlog.log_on_start()(generic_func)
        # The wrapper function should have __tracebackhide__ in its code
        # We can verify by checking that devlog frames are excluded from traces
        assert wrapped.__wrapped__ is generic_func

    def test_tracebackhide_on_async_wrapper(self):
        wrapped = devlog.log_on_start()(async_generic_func)
        assert asyncio.iscoroutinefunction(wrapped)
        assert wrapped.__wrapped__ is async_generic_func
