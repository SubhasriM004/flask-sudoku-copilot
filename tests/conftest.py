import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "starter"

if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))

import app as app_module


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_game_state():
    app_module.CURRENT["puzzle"] = None
    app_module.CURRENT["solution"] = None
    yield
    app_module.CURRENT["puzzle"] = None
    app_module.CURRENT["solution"] = None
