def _token(client, username, password):
    return client.post("/api/login", json={"username": username, "password": password}).json()["token"]

def test_list_users(client):
    token = _token(client, "admin", "admin123")
    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) == 1
    assert users[0]["username"] == "client1"
    assert users[0]["credits"] == 10

def test_create_user(client):
    token = _token(client, "admin", "admin123")
    resp = client.post("/api/admin/users",
        json={"username": "newclient", "password": "pass", "credits": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "newclient"
    assert resp.json()["credits"] == 50

def test_create_user_duplicate_fails(client):
    token = _token(client, "admin", "admin123")
    resp = client.post("/api/admin/users",
        json={"username": "client1", "password": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400

def test_create_user_non_admin_forbidden(client):
    token = _token(client, "client1", "pass123")
    resp = client.post("/api/admin/users",
        json={"username": "x", "password": "y"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

def test_update_credits(client):
    token = _token(client, "admin", "admin123")
    users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"}).json()
    user_id = users[0]["id"]
    resp = client.put(f"/api/admin/users/{user_id}/credits",
        json={"credits": 200},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["credits"] == 200

def test_update_credits_unknown_user(client):
    token = _token(client, "admin", "admin123")
    resp = client.put("/api/admin/users/9999/credits",
        json={"credits": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
