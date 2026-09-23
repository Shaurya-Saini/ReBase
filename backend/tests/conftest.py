import os
import tempfile

import pytest

# Must be set before app.config is imported: isolated DB + fast WS ticks.
_tmp = tempfile.mkdtemp(prefix="rebase-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SIM_TICK_SECONDS"] = "0.01"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:  # runs lifespan (creates tables)
        yield c
