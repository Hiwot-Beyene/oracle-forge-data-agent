"""
Test suite for shared utility library.

Run all tests:
    python -m pytest utils/tests/ -v

Run specific test file:
    python -m pytest utils/tests/test_join_key_resolver.py -v

Run with coverage:
    python -m pytest utils/tests/ --cov=utils --cov-report=html
"""

import pytest

if __name__ == "__main__":
    pytest.main([__file__.replace("__init__.py", ""), "-v"])