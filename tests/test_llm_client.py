import io
import json
import urllib.error

import pytest

from coach import llm as llm_mod
from coach.llm import LLMError, OpenAICompatLLM


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def client(monkeypatch, reply=None, exc=None):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-not-a-real-key")
    seen = {}

    def fake_urlopen(req, timeout):
        seen["req"] = req
        if exc:
            raise exc
        body = reply if isinstance(reply, bytes) else json.dumps(reply).encode()
        return Resp(body)

    monkeypatch.setattr(llm_mod.urllib.request, "urlopen", fake_urlopen)
    return OpenAICompatLLM(), seen


def ok(text):
    return {"choices": [{"message": {"content": text}}]}


def test_parses_content_and_sends_auth(monkeypatch):
    c, seen = client(monkeypatch, ok("  hello  "))
    assert c.ask("hi") == "hello"
    assert seen["req"].get_header("Authorization") == "Bearer test-not-a-real-key"
    assert seen["req"].full_url.endswith("/chat/completions")


def test_score_and_quiz_parsing(monkeypatch):
    c, _ = client(monkeypatch, ok("2|Clear and correct."))
    assert c.score("t", "ref", "mine") == (2, "Clear and correct.")
    c, _ = client(monkeypatch, ok("What is X? | Y"))
    assert c.quiz("t", "lesson") == ("What is X?", "Y")
    c, _ = client(monkeypatch, ok("no pipe here"))
    assert c.quiz("t", "lesson")[1] == ""


@pytest.mark.parametrize("code,needle", [(401, "OPENROUTER_API_KEY"), (429, "Rate limited"), (500, "HTTP 500")])
def test_http_errors(monkeypatch, code, needle):
    err = urllib.error.HTTPError("u", code, "x", {}, None)
    c, _ = client(monkeypatch, exc=err)
    with pytest.raises(LLMError, match=needle):
        c.ask("hi")


def test_timeout_network_and_bad_shapes(monkeypatch):
    for exc, needle in [(TimeoutError(), "timed out"), (urllib.error.URLError("dns"), "Could not reach")]:
        c, _ = client(monkeypatch, exc=exc)
        with pytest.raises(LLMError, match=needle):
            c.ask("hi")
    for reply in [b"not json", {"error": "x"}, {"choices": []}, {"choices": [{"message": {"content": None}}]}]:
        c, _ = client(monkeypatch, reply)
        with pytest.raises(LLMError):
            c.ask("hi")
