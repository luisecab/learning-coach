from datetime import date

from coach.schedule import is_due, next_review

D = date(2026, 1, 1)


def test_correct_pushes_later():
    assert next_review(-1, True, D) == (0, date(2026, 1, 3))
    assert next_review(0, True, D) == (1, date(2026, 1, 8))
    assert next_review(1, True, D) == (2, date(2026, 1, 31))
    assert next_review(2, True, D) == (2, date(2026, 1, 31))


def test_wrong_comes_back_sooner():
    assert next_review(2, False, D) == (0, date(2026, 1, 2))


def test_is_due():
    assert is_due("2026-01-01", D) and not is_due("2026-01-02", D)
