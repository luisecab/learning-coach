"""coach: try first, then explain."""
import argparse
from datetime import date

from .llm import EXAMPLES, get_llm
from .schedule import is_due, next_review
from .storage import DEFAULT_DIR, Store


def cmd_start(store, llm, args, ask, today):
    state = store.load()
    q = llm.level_question(args.topic)
    level = ask(q + "\n> ")
    state["topics"][args.topic] = {"level": level, "created": today.isoformat(), "lessons": 0}
    state["current"] = args.topic
    store.save(state)
    store.append_log(args.topic, f"## Started {today}\n- Level question: {q}\n- Answer: {level}")
    print(f"Topic '{args.topic}' saved. Next: coach learn")


def cmd_learn(store, llm, args, ask, today):
    state = store.load()
    topic = args.topic or state["current"]
    if topic not in state["topics"]:
        raise SystemExit("No topic yet. Run: coach start \"<topic>\"")
    t = state["topics"][topic]
    problem = llm.problem(topic, t["level"])
    print(f"Try this first (no peeking):\n{problem}")
    attempt = ask("Your attempt> ")
    critique = llm.critique(topic, problem, attempt)
    print("\n" + critique)
    back = ask("\nExplain it back in 1-2 lines> ")
    score, feedback = llm.score(topic, critique, back)
    print(f"Score: {score}/2. {feedback}")
    question, answer = llm.quiz(topic, critique)
    _, due = next_review(-1, True, today)  # first review in ~2 days
    state["items"].append({"topic": topic, "q": question, "a": answer, "step": 0, "due": due.isoformat()})
    t["lessons"] += 1
    store.save(state)
    store.append_log(topic, f"## Lesson {today}\n**Problem:** {problem}\n\n**Attempt:** {attempt}\n\n"
                            f"{critique}\n\n**Explain-back ({score}/2):** {back}\n\n**Quiz:** {question} -> {answer}")
    print(f"Saved. Review due {due}.")


def cmd_review(store, llm, args, ask, today):
    state = store.load()
    due = [i for i in state["items"] if is_due(i["due"], today)]
    if not due:
        print("Nothing due. Nice.")
        return
    for item in due:
        ans = ask(f"[{item['topic']}] {item['q']}\n> ")
        st = state["stats"]
        st["asked"] += 1
        if ans.strip():
            st["answered"] += 1
        ok = bool(ans.strip()) and llm.grade(item["q"], item["a"], ans)
        st["correct"] += ok
        item["step"], d = next_review(item["step"], ok, today)
        item["due"] = d.isoformat()
        print(("Correct" if ok else f"Not quite. Expected: {item['a']}") + f" (next: {d})")
    store.save(state)


def cmd_status(store, llm, args, ask, today):
    state = store.load()
    if not state["topics"]:
        print("No topics. Try: coach --fake start \"" + next(iter(EXAMPLES)) + "\"")
        return
    for name, t in state["topics"].items():
        n = sum(1 for i in state["items"] if i["topic"] == name and is_due(i["due"], today))
        print(f"- {name}: {t['lessons']} lessons, {n} due")
    st = state["stats"]
    rate = st["answered"] / st["asked"] * 100 if st["asked"] else 0
    pct = st["correct"] / st["answered"] * 100 if st["answered"] else 0
    print(f"Quiz: {st['asked']} asked, {rate:.0f}% answered, {pct:.0f}% correct")


def build_parser():
    p = argparse.ArgumentParser(prog="coach", description=__doc__)
    p.add_argument("--dir", default=str(DEFAULT_DIR), help="data folder (e.g. inside an Obsidian vault)")
    p.add_argument("--fake", action="store_true", help="offline canned responses, no API key needed")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start", help="create a topic")
    s.add_argument("topic")
    s.set_defaults(fn=cmd_start)
    l = sub.add_parser("learn", help="try a problem, then get an explanation")
    l.add_argument("--topic")
    l.set_defaults(fn=cmd_learn)
    sub.add_parser("review", help="quiz due items").set_defaults(fn=cmd_review)
    sub.add_parser("status", help="show progress").set_defaults(fn=cmd_status)
    return p


def main(argv=None, ask=input, today=None):
    args = build_parser().parse_args(argv)
    llm = get_llm(args.fake) if args.cmd != "status" else None
    args.fn(Store(args.dir), llm, args, ask, today or date.today())


if __name__ == "__main__":
    main()
