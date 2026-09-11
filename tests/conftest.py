import pytest


def pytest_collection_modifyitems(config, items):
    # `slow` tests fit models; run them with `uv run pytest -m slow`
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.timeout(1800))
