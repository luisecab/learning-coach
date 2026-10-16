from coach.storage import Store, slug


def test_roundtrip_and_log(tmp_path):
    s = Store(tmp_path / "vault")
    st = s.load()
    assert st["topics"] == {}
    st["topics"]["X"] = {"level": "0", "created": "2026-01-01", "lessons": 0}
    s.save(st)
    assert Store(tmp_path / "vault").load()["topics"]["X"]["level"] == "0"
    f = s.append_log("Git Rebase vs Merge", "hello")
    assert f.name == "git-rebase-vs-merge.md" and "hello" in f.read_text()


def test_slug():
    assert slug("  ??? ") == "topic"
