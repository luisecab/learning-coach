"""Plain-file storage: state.json plus one markdown log per topic (Obsidian-friendly)."""
import hashlib
import json
import re
from pathlib import Path

DEFAULT_DIR = Path.home() / ".learning-coach"


def slug(text: str) -> str:
    t = text.lower().replace("+", " plus ").replace("#", " sharp ")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "topic"


class Store:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "state.json"

    def load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"current": None, "topics": {}, "items": [], "stats": {"asked": 0, "answered": 0, "correct": 0}}

    def save(self, state: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def log_path(self, topic: str) -> Path:
        """One file per topic; adds a short hash if another topic already owns the slug."""
        header = f"# {topic}\n"
        f = self.root / f"{slug(topic)}.md"
        if f.exists() and f.read_text(encoding="utf-8").split("\n", 1)[0] + "\n" != header:
            h = hashlib.sha1(topic.encode()).hexdigest()[:6]
            f = self.root / f"{slug(topic)}-{h}.md"
        return f

    def append_log(self, topic: str, markdown: str) -> Path:
        f = self.log_path(topic)
        if not f.exists():
            f.write_text(f"# {topic}\n\n", encoding="utf-8")
        with f.open("a", encoding="utf-8") as fh:
            fh.write(markdown.rstrip() + "\n\n")
        return f
