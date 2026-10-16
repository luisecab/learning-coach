"""Plain-file storage: state.json plus one markdown log per topic (Obsidian-friendly)."""
import json
import re
from pathlib import Path

DEFAULT_DIR = Path.home() / ".learning-coach"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "topic"


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

    def append_log(self, topic: str, markdown: str) -> Path:
        f = self.root / f"{slug(topic)}.md"
        if not f.exists():
            f.write_text(f"# {topic}\n\n", encoding="utf-8")
        with f.open("a", encoding="utf-8") as fh:
            fh.write(markdown.rstrip() + "\n\n")
        return f
