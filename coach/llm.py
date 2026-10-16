"""LLM backends: any OpenAI-compatible endpoint, or a deterministic offline fake."""
import json
import os
import socket
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

EXAMPLES = {
    "python decorators": {
        "problem": "Write a decorator `twice` so that calling a decorated f() runs f two times.",
        "counterexample": "If your wrapper does `return f` instead of calling it, f() runs zero extra times; and forgetting *args/**kwargs breaks f(x).",
        "explanation": (
            "A decorator takes a function and returns a new one:\n\n"
            "    def twice(f):\n"
            "        def wrapper(*args, **kwargs):\n"
            "            f(*args, **kwargs)\n"
            "            return f(*args, **kwargs)\n"
            "        return wrapper\n"
        ),
        "quiz": ("What does a decorator return?", "a function"),
    },
    "git rebase vs merge": {
        "problem": "Your feature branch is 3 commits behind main. Name one way to update it that keeps history linear.",
        "counterexample": "`git merge main` works but adds a merge commit, so history is not linear.",
        "explanation": "`git rebase main` replays your commits on top of main, giving linear history but rewriting commit hashes; avoid rebasing shared branches.",
        "quiz": ("Which command rewrites commit hashes: rebase or merge?", "rebase"),
    },
    "prompt caching": {
        "problem": "You send the same 5k-token system prompt with every request. How would you order the prompt to benefit from caching?",
        "counterexample": "Putting a timestamp at the start of the prompt changes the prefix every call, so nothing is ever cached.",
        "explanation": "Caches match on an identical prefix: put stable content (system prompt, docs) first and variable content (user question) last.",
        "quiz": ("Caching matches on an identical prefix or suffix?", "prefix"),
    },
}


class LLMError(SystemExit):
    """A friendly, user-facing backend error (exits the CLI with a message)."""


class FakeLLM:
    """Canned, deterministic responses. Needs no key or network."""

    _warned = False

    def _ex(self, topic: str) -> dict:
        key = topic.lower()
        if key not in EXAMPLES and not self._warned:
            self._warned = True
            print(f"[fake mode] No canned lesson for '{topic}'; using the 'python decorators' example. "
                  f"Built-in topics: {', '.join(EXAMPLES)}", file=sys.stderr)
        return EXAMPLES.get(key, EXAMPLES["python decorators"])

    def level_question(self, topic):
        return f"On a scale of 0-3, how well do you know '{topic}'? What have you used it for?"

    def problem(self, topic, level):
        return self._ex(topic)["problem"]

    def critique(self, topic, problem, attempt):
        ex = self._ex(topic)
        return f"Where it breaks: {ex['counterexample']}\n\nExplanation: {ex['explanation']}"

    def score(self, topic, explanation, user_text):
        words = len(user_text.split())
        return (2 if words >= 5 else 1 if words else 0), "Fake scorer: rewards a full-sentence explain-back."

    def quiz(self, topic, lesson):
        return self._ex(topic)["quiz"]

    def grade(self, question, expected, answer):
        return expected.lower() in answer.lower()


class OpenAICompatLLM(FakeLLM):
    """Minimal chat-completions client (stdlib only). Key comes from the environment only."""

    def __init__(self):
        self.key = os.environ.get("OPENROUTER_API_KEY")
        if not self.key:
            raise SystemExit("OPENROUTER_API_KEY is not set. Export it, or run with --fake.")
        self.base = os.environ.get("COACH_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        self.model = os.environ.get("COACH_MODEL", DEFAULT_MODEL)

    def ask(self, prompt: str) -> str:
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(
            f"{self.base}/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            hints = {401: "API key rejected (401). Check OPENROUTER_API_KEY.",
                     403: "Access denied (403). Check your key and model permissions.",
                     404: "Endpoint or model not found (404). Check COACH_BASE_URL / COACH_MODEL.",
                     429: "Rate limited (429). Free models are busy; wait a bit or set COACH_MODEL."}
            raise LLMError(hints.get(e.code, f"Model API returned HTTP {e.code}."))
        except (socket.timeout, TimeoutError):
            raise LLMError("Model API timed out. Try again, or use --fake.")
        except urllib.error.URLError as e:
            raise LLMError(f"Could not reach {self.base}: {e.reason}. Check your network or COACH_BASE_URL.")
        except ValueError:
            raise LLMError("Model API returned something that is not JSON.")
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError
            return content.strip()
        except (KeyError, IndexError, TypeError):
            raise LLMError("Unexpected reply shape from the model API (no choices[0].message.content).")

    def level_question(self, topic):
        return self.ask(f"Ask ONE short question to gauge a learner's level in '{topic}'. Output only the question.")

    def problem(self, topic, level):
        return self.ask(f"Learner level: {level!r}. Give ONE small problem on '{topic}' they should attempt "
                        "BEFORE any explanation. Do not explain or hint. Output only the problem.")

    def critique(self, topic, problem, attempt):
        return self.ask(f"Problem: {problem}\nLearner attempt: {attempt}\nFirst show a concrete counterexample "
                        "or case where the attempt breaks (or confirm it holds), then a short clear explanation.")

    def score(self, topic, explanation, user_text):
        out = self.ask(f"Reference: {explanation}\nLearner explain-back: {user_text}\nScore 0-2 for correctness. "
                       "Reply as '<score>|<one-line feedback>'.")
        s, _, fb = out.partition("|")
        try:
            return max(0, min(2, int(s.strip()[:1]))), fb.strip()
        except ValueError:
            return 1, out

    def quiz(self, topic, lesson):
        out = self.ask(f"From this lesson on '{topic}':\n{lesson}\nWrite one short quiz question and a short "
                       "expected answer. Reply as 'question|answer'.")
        q, _, a = out.partition("|")
        return q.strip(), a.strip()

    def grade(self, question, expected, answer):
        out = self.ask(f"Question: {question}\nExpected: {expected}\nAnswer: {answer}\nIs the answer correct? Reply yes or no.")
        return out.lower().startswith("y")


def get_llm(fake: bool):
    return FakeLLM() if fake else OpenAICompatLLM()
