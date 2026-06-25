"""Notification dispatcher must render templates + route to channels."""

from app.clients import notifications
from app.clients.notifications import Channel


def test_render_template():
    out = notifications.render_template("Hello {name}, your loss was ${loss}.", {"name": "Ravi", "loss": 1800})
    assert out == "Hello Ravi, your loss was $1800."


def test_send_welcome_in_app(monkeypatch):
    monkeypatch.setattr(notifications, "_INBOX", [])
    results = notifications.send(
        kind="welcome",
        user_id="usr_x",
        channels=(Channel.in_app,),
        vars={"name": "Ravi", "verification_url": "http://x/v?t=1"},
    )
    assert len(results) == 1
    assert results[0].channel is Channel.in_app
    assert any("Ravi" in n["body"] for n in notifications.inbox("usr_x"))


def test_unknown_kind_raises():
    import pytest

    with pytest.raises(KeyError):
        notifications.send(kind="not_a_template", user_id="usr_x")
