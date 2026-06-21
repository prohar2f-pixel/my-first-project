def test_login_success(client):
    resp = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["username"] == "admin"
    assert data["is_admin"] is True
    assert "credits" in data

def test_login_wrong_password(client):
    resp = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401

def test_login_unknown_user(client):
    resp = client.post("/api/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401

def test_protected_route_no_token(client):
    resp = client.get("/api/history")
    assert resp.status_code in (401, 422)
