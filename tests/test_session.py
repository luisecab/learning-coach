import json
from datetime import date, timedelta

import pytest

from coach.cli import main


def feeder(answers):
    it = iter(answers)
    return lambda prompt="": next(it)


def test_full_fake_session(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    d = str(tmp_path)
    today = date(2026, 3, 1)
    main(["--fake", "--dir", d, "start", "git rebase vs merge"], ask=feeder(["1"]), today=today)
    main(["--fake", "--dir", d, "learn"], ask=feeder(["git merge main", "rebase replays my commits on top of main"]), today=today)
    out = capsys.readouterr().out
    assert "Where it breaks" in out and "Score: 2/2" in out

    main(["--fake", "--dir", d, "review"], today=today)
    assert "Nothing due" in capsys.readouterr().out

    later = today + timedelta(days=2)
    main(["--fake", "--dir", d, "review"], ask=feeder(["rebase"]), today=later)
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["items"][0]["step"] == 1 and state["items"][0]["due"] == "2026-03-10"

    main(["--fake", "--dir", d, "review"], ask=feeder(["merge"]), today=date(2026, 3, 10))
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["items"][0]["step"] == 0 and state["items"][0]["due"] == "2026-03-11"

    capsys.readouterr()
    main(["--dir", d, "status"], today=date(2026, 3, 10))
    out = capsys.readouterr().out
    assert "2 asked, 100% answered, 50% correct" in out
    assert (tmp_path / "git-rebase-vs-merge.md").exists()
    assert "OPENROUTER" not in (tmp_path / "state.json").read_text()


def test_no_key_without_fake(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        main(["--dir", str(tmp_path), "start", "x"], ask=feeder(["0"]))
