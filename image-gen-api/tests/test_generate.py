from unittest.mock import patch, AsyncMock

MOCK_URLS = ["https://cdn.runware.ai/img1.webp"]

def _token(client, username, password):
    return client.post("/api/login", json={"username": username, "password": password}).json()["token"]

def test_generate_success(client):
    token = _token(client, "client1", "pass123")
    with patch("main.generate_images", new_callable=AsyncMock, return_value=MOCK_URLS):
        resp = client.post("/api/generate",
            json={"prompt": "a cat", "count": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["image_urls"] == MOCK_URLS
    assert resp.json()["credits"] == 9  # started with 10, used 1

def test_generate_deducts_credits_for_multiple(client):
    token = _token(client, "client1", "pass123")
    with patch("main.generate_images", new_callable=AsyncMock, return_value=MOCK_URLS * 2):
        resp = client.post("/api/generate",
            json={"prompt": "a cat", "count": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["credits"] == 8  # 10 - 2

def test_generate_no_credits(client):
    from models import User
    from tests.conftest import TestingSession
    db = TestingSession()
    db.query(User).filter(User.username == "client1").update({"credits": 0})
    db.commit()
    db.close()

    token = _token(client, "client1", "pass123")
    resp = client.post("/api/generate",
        json={"prompt": "a cat", "count": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 402

def test_generate_admin_bypasses_credits(client):
    token = _token(client, "admin", "admin123")
    with patch("main.generate_images", new_callable=AsyncMock, return_value=MOCK_URLS):
        resp = client.post("/api/generate",
            json={"prompt": "a cat", "count": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200

def test_generate_no_auth(client):
    resp = client.post("/api/generate", json={"prompt": "a cat"})
    assert resp.status_code in (401, 422)
