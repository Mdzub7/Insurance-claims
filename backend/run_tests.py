import os
os.environ["JWT_DEV_SECRET"] = "devsecret"
from fastapi.testclient import TestClient
from app.main import app


def main():
    c = TestClient(app)
    r = c.post("/api/v1/auth/register", json={"email": "x@y.com", "password": "Password1!", "role": "patient", "name": "X"})
    print("register status", r.status_code)
    r = c.post("/api/v1/auth/login", json={"email": "x@y.com", "password": "Password1!"})
    print("login status", r.status_code)
    token = r.json().get("token", "")
    r = c.get("/api/v1/claims/my")
    print("claims without auth", r.status_code)
    r = c.post("/api/v1/claims/", json={"amount": 10.0, "description": "d", "policy_number": "p"}, headers={"Authorization": f"Bearer {token}"})
    print("submit claim", r.status_code)


if __name__ == "__main__":
    main()
