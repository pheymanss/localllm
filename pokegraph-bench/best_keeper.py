"""Keep the best version of a run's code while the agent works.

usage: python best_keeper.py <workdir> <pristine-task-dir> <hidden-test.py> <conftest.py> <best-dir>
Polls <workdir>/query every few seconds. When it changes, scores a copy (pristine task + that query/)
with the hidden tests; if the pass count beats the best so far, saves it to <best-dir>/query and
writes <best-dir>/best.json. Stops after a final check when <workdir>.stop exists.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

work, pristine, hidden, conftest, best = sys.argv[1:6]
stop = work.rstrip("/") + ".stop"
os.makedirs(best, exist_ok=True)
state = {"pass": -1, "total": 0, "at": None, "checks": 0}
t0 = time.time()


def digest():
    h = hashlib.sha1()
    q = os.path.join(work, "query")
    for root, _, files in sorted(os.walk(q)):
        for f in sorted(files):
            if f.endswith(".py"):
                p = os.path.join(root, f)
                try:
                    h.update(p.encode()); h.update(open(p, "rb").read())
                except OSError:
                    pass
    return h.hexdigest()


def score():
    with tempfile.TemporaryDirectory(prefix="pgbest") as tmp:
        d = os.path.join(tmp, "t")
        shutil.copytree(pristine, d)
        shutil.rmtree(os.path.join(d, "query"), ignore_errors=True)
        shutil.copytree(os.path.join(work, "query"), os.path.join(d, "query"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(hidden, d); shutil.copy(conftest, d)
        try:
            out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
                                  os.path.basename(hidden)], cwd=d, capture_output=True, text=True, timeout=300).stdout
        except subprocess.TimeoutExpired:
            return
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        p = re.search(r"(\d+) passed", tail); f = re.search(r"(\d+) (failed|error)", tail)
        passed = int(p.group(1)) if p else 0
        state["checks"] += 1
        if passed > state["pass"]:
            # Save exactly the code that was scored (copied before testing, so no race with the agent).
            shutil.rmtree(os.path.join(best, "query"), ignore_errors=True)
            shutil.copytree(os.path.join(d, "query"), os.path.join(best, "query"),
                            ignore=shutil.ignore_patterns("__pycache__"))
            state.update({"pass": passed, "total": passed + (int(f.group(1)) if f else 0), "at": int(time.time() - t0)})
            json.dump(state, open(os.path.join(best, "best.json"), "w"))


last = None
while True:
    final = os.path.exists(stop)
    if os.path.isdir(os.path.join(work, "query")):
        h = digest()
        if h != last:
            last = h
            score()
    if final:
        break
    time.sleep(5)
json.dump(state, open(os.path.join(best, "best.json"), "w"))
