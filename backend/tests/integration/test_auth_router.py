from app.modules.auth.schemas import CurrentUserSchema, TokenResponseSchema

from ..test_conf import client


def test_login_sets_refresh_cookie(client, monkeypatch):  # noqa: ANN001
    def fake_login(*_args, **_kwargs):
        return (
            TokenResponseSchema(
                access_token="token",
                expires_in=900,
                user=CurrentUserSchema(id="u1", email="u@example.com", shop_id="s1"),
            ),
            "refresh-token",
        )

    monkeypatch.setattr("app.modules.auth.router.auth_service.login", fake_login)
    response = client.post("/api/v1/auth/login", json={"email": "u@example.com", "password": "secret123"})
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/" in set_cookie


def test_refresh_rotates_cookie(client, monkeypatch):  # noqa: ANN001
    def fake_refresh(*_args, **_kwargs):
        return (
            TokenResponseSchema(
                access_token="new-token",
                expires_in=900,
                user=CurrentUserSchema(id="u1", email="u@example.com", shop_id="s1"),
            ),
            "new-refresh-token",
        )

    monkeypatch.setattr("app.modules.auth.router.auth_service.refresh", fake_refresh)
    client.cookies.set("refresh_token", "old")
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/" in set_cookie
