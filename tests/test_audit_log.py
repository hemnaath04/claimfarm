"""Audit log writes and reads back JSONL rows."""


from app.storage import audit_log


def test_record_then_tail(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit_log, "LOG_PATH", log_path)
    audit_log.record(actor="usr_test", action="test.action", target="t1")
    audit_log.record(actor="usr_test", action="test.action", target="t2", metadata={"k": "v"})
    rows = audit_log.tail(10)
    assert len(rows) == 2
    assert rows[0]["target"] == "t1"
    assert rows[1]["metadata"] == {"k": "v"}


def test_tail_handles_missing_file(tmp_path, monkeypatch):
    log_path = tmp_path / "does_not_exist.jsonl"
    monkeypatch.setattr(audit_log, "LOG_PATH", log_path)
    assert audit_log.tail(10) == []
