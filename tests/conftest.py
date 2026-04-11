import os
import tempfile

_fd, _test_db = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = "sqlite:///" + _test_db.replace("\\", "/")

import pytest

from app import app, db


@pytest.fixture(autouse=True)
def _reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app.test_client()
