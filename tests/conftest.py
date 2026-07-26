import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = PROJECT_ROOT / "starter"

if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))

from app_factory import create_app
from utils import CURRENT


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_game_state():
    CURRENT["puzzle"] = None
    CURRENT["solution"] = None
    CURRENT["locked_cells"] = []
    CURRENT["timer_running"] = False
    CURRENT["elapsed_seconds"] = 0
    CURRENT["leaderboard"] = []
    CURRENT["hints_used"] = 0
    yield
    CURRENT["puzzle"] = None
    CURRENT["solution"] = None
    CURRENT["locked_cells"] = []
    CURRENT["timer_running"] = False
    CURRENT["elapsed_seconds"] = 0
    CURRENT["leaderboard"] = []
    CURRENT["hints_used"] = 0
