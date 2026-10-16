"""Spaced review: ~2 days, 1 week, 1 month. Correct moves up a step, wrong resets."""
from datetime import date, timedelta

INTERVALS = [2, 7, 30]  # days


def next_review(step: int, correct: bool, today: date) -> tuple[int, date]:
    """Return (new_step, due_date). Correct pushes later; wrong brings it back sooner."""
    if correct:
        step = min(step + 1, len(INTERVALS) - 1)
    else:
        step = 0
    days = INTERVALS[step] if correct else 1
    return step, today + timedelta(days=days)


def is_due(due: str, today: date) -> bool:
    return date.fromisoformat(due) <= today
