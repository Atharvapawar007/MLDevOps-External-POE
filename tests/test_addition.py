"""
test_addition.py - Unit tests for core addition logic and CLI interface.
"""

import sys
import math
import unittest

try:
    import pytest
except ImportError:
    class _PytestApprox:
        def __init__(self, expected, rel=1e-5, abs=1e-5):
            self.expected = expected
            self.rel = rel
            self.abs = abs
        def __eq__(self, actual):
            return math.isclose(actual, self.expected, rel_tol=self.rel, abs_tol=self.abs)

    class _PytestShim:
        @staticmethod
        def approx(expected, rel=1e-5, abs=1e-5):
            return _PytestApprox(expected, rel=rel, abs=abs)
        @staticmethod
        def raises(expected_exc):
            import contextlib
            @contextlib.contextmanager
            def _cm():
                try:
                    yield
                except expected_exc:
                    pass
                else:
                    raise AssertionError(f"Expected exception {expected_exc.__name__} was not raised")
            return _cm()
    pytest = _PytestShim()

from src.addition import add_numbers, main


class TestAddNumbers(unittest.TestCase):
    """Test suite for the add_numbers core function."""

    def test_positive_integers(self):
        """Test addition of positive integers."""
        assert add_numbers(10, 20) == 30
        assert add_numbers(1, 1) == 2
        assert add_numbers(999, 1) == 1000

    def test_floating_point_numbers(self):
        """Test addition of floating-point numbers with precision."""
        assert add_numbers(10.5, 4.5) == 15.0
        assert add_numbers(0.1, 0.2) == pytest.approx(0.3)
        assert add_numbers(3.14159, 2.71828) == pytest.approx(5.85987)

    def test_negative_numbers(self):
        """Test addition involving negative numbers."""
        assert add_numbers(-10, 5) == -5
        assert add_numbers(-15, -25) == -40
        assert add_numbers(50, -50) == 0

    def test_zero_identity(self):
        """Test addition identity property with zero."""
        assert add_numbers(0, 0) == 0
        assert add_numbers(42, 0) == 42
        assert add_numbers(0, -100) == -100
        assert add_numbers(0.0, 7.5) == 7.5

    def test_large_numbers(self):
        """Test addition with very large numbers."""
        assert add_numbers(10**12, 10**12) == 2 * (10**12)
        assert add_numbers(1e9, 2e9) == 3e9

    def test_invalid_type_string_raises_type_error(self):
        """Test that invalid types raise a TypeError."""
        with pytest.raises(TypeError):
            add_numbers("10", 20)  # type: ignore

        with pytest.raises(TypeError):
            add_numbers(10, "20")  # type: ignore

        with pytest.raises(TypeError):
            add_numbers("abc", "def")  # type: ignore

    def test_invalid_type_none_raises_type_error(self):
        """Test that None values raise a TypeError."""
        with pytest.raises(TypeError):
            add_numbers(None, 5)  # type: ignore

        with pytest.raises(TypeError):
            add_numbers(10, None)  # type: ignore


class TestAdditionCLI(unittest.TestCase):
    """Test CLI and interactive execution."""

    def test_cli_interactive_flow(self):
        """Test interactive stdin prompt execution."""
        from unittest.mock import patch
        import io

        inputs = iter(["12", "8"])
        with patch("builtins.input", lambda _: next(inputs)), \
             patch("sys.argv", ["addition.py"]), \
             patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            assert "Addition (+)" in output
            assert "20" in output
            assert "12 + 8 = 20" in output

    def test_cli_argument_flow(self):
        """Test command line arguments flow."""
        from unittest.mock import patch
        import io

        with patch("sys.argv", ["addition.py", "--num1", "100.5", "--num2", "49.5"]), \
             patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            assert "100.5 + 49.5 = 150" in output
