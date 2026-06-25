"""MockProvider must be deterministic + cover the three decision branches."""

from app.clients.identity_verification import IdvDecision, MockProvider


def test_mock_deterministic_per_session_id():
    p = MockProvider()
    a = p.evaluate(session_id="idv_mock_test_alpha")
    b = p.evaluate(session_id="idv_mock_test_alpha")
    assert a.score == b.score
    assert a.decision == b.decision


def test_mock_returns_one_of_three_decisions():
    p = MockProvider()
    decisions = {p.evaluate(session_id=f"idv_mock_{i}").decision for i in range(50)}
    assert decisions.issubset({IdvDecision.approved, IdvDecision.needs_review, IdvDecision.rejected})


def test_start_session_returns_hosted_url():
    p = MockProvider()
    s = p.start_session(user_id="usr_x", return_url="http://example/cb")
    assert s["session_id"].startswith("idv_mock_")
    assert "session=" in s["hosted_url"]
