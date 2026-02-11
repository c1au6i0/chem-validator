import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "fast: mark test as fast (unit tests)")
    config.addinivalue_line("markers", "slow: mark test as slow (integration tests)")
