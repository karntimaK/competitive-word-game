import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "server")))

import pytest
from app import app, socketio

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Competitive Word Game" in res.data
