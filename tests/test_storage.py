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


def test_slug_no_collision(tmp_path):
    assert slug("C++") == "c-plus-plus" and slug("C#") == "c-sharp"
    s = Store(tmp_path)
    a = s.append_log("Git: rebase", "x")
    b = s.append_log("git rebase", "y")
    assert a != b and s.append_log("git rebase", "z") == b
