from unittest.mock import patch, AsyncMock

MOCK_URLS = ["https://cdn.runware.ai/img1.webp"]

def _token(client, username="client1", password="pass123"):
    return client.post("/api/login", json={"username": username, "password": password}).json()["token"]

def _generate(client, token, prompt="a cat"):
    with patch("main.generate_images", new_callable=AsyncMock, return_value=MOCK_URLS):
        client.post("/api/generate",
            json={"prompt": prompt, "count": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

def test_history_empty(client):
    token = _token(client)
    resp = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []

def test_history_after_generate(client):
    token = _token(client)
    _generate(client, token, "a dog")
    resp = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["prompt"] == "a dog"
    assert resp.json()[0]["image_urls"] == MOCK_URLS

def test_gallery_returns_flat_urls(client):
    token = _token(client)
    _generate(client, token)
    _generate(client, token)
    resp = client.get("/api/gallery", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()["images"]) == 2

def test_history_isolated_per_user(client):
    token1 = _token(client, "client1", "pass123")
    _generate(client, token1)
    token2 = _token(client, "admin", "admin123")
    resp = client.get("/api/history", headers={"Authorization": f"Bearer {token2}"})
    assert resp.json() == []
