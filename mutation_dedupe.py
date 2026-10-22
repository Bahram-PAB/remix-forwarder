"""One-run mutation checks for the file-name dedupe feature.

Each mutation rewrites bot.py, runs the test suite, expects a FAILURE, then
restores the original. bot.py working copy is untouched on exit.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(r"C:\Users\Bahram\podcast-forwarder")
BOT = ROOT / "bot.py"
ORIG = BOT.read_bytes()

MUTATIONS = [
    ("cron check drops the name key",
     "if id_dup or name_dup:", "if id_dup:"),
    ("backfill check drops the name key",
     "if already_sent(state, key) or (\r\n                                fname and already_sent(state, name_key(fname))):",
     "if already_sent(state, key):"),
    ("send path forgets to record the name in the cron loop",
     "remember_sent(state, media_key(handle, msg))\r\n                    if fname:\r\n                        remember_sent(state, name_key(fname))",
     "remember_sent(state, media_key(handle, msg))"),
    ("seed's one-shot guard removed (re-sweeps wantonly)",
     '    if any(k.startswith("f:") for k in sent):\r\n        return 0\r\n',
     ""),
    ("seed loop no longer records names",
     "            sent[name_key(fname)] = 1\r\n            added += 1\r\n",
     "            added += 0\r\n"),
]


def run_tests():
    r = subprocess.run([sys.executable, "-X", "utf8", "test_bot.py"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    # "FAILED" on the summary, or unittest's "OK"
    tail = (r.stdout + r.stderr)[-400:]
    return ("FAILED" in tail or "ERROR" in tail), tail


def main():
    passed = []
    for name, old, new in MUTATIONS:
        src = ORIG.decode("utf-8")
        if old not in src:
            print(f"[SKIP] pattern not found: {name}")
            continue
        mutated = src.replace(old, new)
        assert mutated != src, name
        BOT.write_bytes(mutated.encode("utf-8"))
        try:
            failed, tail = run_tests()
            if failed:
                passed.append(name)
                print(f"[CAUGHT ✓] {name}")
            else:
                print(f"[SURVIVED ✗] {name}")
                print(tail)
        finally:
            BOT.write_bytes(ORIG)
    print(f"\n{len(passed)}/{len(MUTATIONS)} mutations caught")
    if len(passed) != len(MUTATIONS):
        sys.exit(1)


if __name__ == "__main__":
    main()
