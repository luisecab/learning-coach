# learning-coach

A small CLI that fights forgetting when you learn with chatbots. The loop is **try first, then explain**:

1. You get a small problem *before* any explanation, and you type an attempt.
2. The coach shows where your attempt breaks (a counterexample), then explains.
3. You explain it back in 1-2 lines and get a score.
4. The lesson goes into a markdown log, and a quiz item is scheduled for review at about 2 days, 1 week, then 1 month. A right answer pushes it later. A wrong answer brings it back the next day.

## Install

```bash
pip install git+https://github.com/luisecab/learning-coach
# or from a clone: pip install -e ".[test]"
```

## Quickstart (offline, no key)

`--fake` uses canned, deterministic responses for a few built-in example topics: `python decorators`, `git rebase vs merge`, `prompt caching`.

```bash
coach --fake start "python decorators"
coach --fake learn
coach --fake review     # items are first due 2 days after a lesson
coach status
```

## Use a real model

Any OpenAI-compatible endpoint works. By default it uses OpenRouter with a free model.

```bash
export OPENROUTER_API_KEY=...            # read from the environment only, never written to disk
export COACH_MODEL=some/model            # optional
export COACH_BASE_URL=https://...        # optional, any OpenAI-compatible /v1 base URL
coach start "prompt caching"
```

## Where data lives

Data goes to `~/.learning-coach` by default. Use `--dir` to put it somewhere else, for example inside an Obsidian vault: `coach --dir ~/Vault/learning learn`. The folder holds `state.json` (topics, quiz items, stats) and one `<topic>.md` log per topic.

## Limitations

- Feedback is only as good as the model, and free models can be slow, rate-limited, or wrong.
- Fake mode is a demo. It always returns the same problem and quiz for each example topic.
- The scheduler is a simple fixed ladder (2/7/30 days), not SM-2 or FSRS.
- It is single-user with no sync. Wrong or empty answers count as incorrect.
- Real-model replies are parsed loosely (`score|feedback`, `question|answer`).

## License

MIT
