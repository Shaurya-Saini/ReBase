import os
import tempfile

import pytest

# Must be set before app.config is imported: isolated DB + fast WS ticks.
_tmp = tempfile.mkdtemp(prefix="rebase-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SIM_TICK_SECONDS"] = "0.01"
os.environ["ESTIMATOR_PATH"] = f"{_tmp}/estimator.json"  # never touch the dev model

from fastapi.testclient import TestClient  # noqa: E402

from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture
def client():
    seed(engine)  # fresh demo data per test, relative to the real clock
    with TestClient(app) as c:  # runs lifespan
        yield c
