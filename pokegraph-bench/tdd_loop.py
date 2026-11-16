"""Level 3: a script drives the test loop; the local model only writes code.

usage: python tdd_loop.py <model> <workdir> [--budget 1200] [--log path.jsonl]

The workdir holds TASK.md, query/ and tests/test_given.py. Each step:
  1. run the tests, pick one failing test (fewest attempts first)
  2. send the model a fresh, short request: TASK.md, read-only helper files, the target file,
     that test's error, and notes from earlier failed attempts on it
  3. the model replies with either a probe (python run in the workdir, output fed back, max 3 per
     step) or the full new content of one file
  4. keep the change only if the score (passed, fewer errors) improves; otherwise roll back
Thinking: off on the first attempt at a test, on for retries. A runaway think is cut at a token
budget and the model is asked to answer directly from the tail of its reasoning (budget forcing).
"""
import argparse, ast, json, os, re, shutil, subprocess, sys, time, urllib.request
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("work")
ap.add_argument("--budget", type=int, default=1200)
ap.add_argument("--log", default=None)
ap.add_argument("--think-tokens", type=int, default=3000)
A = ap.parse_args()
W = os.path.abspath(A.work); T0 = time.time()
LOG = open(A.log or W + ".l3.jsonl", "a")
PY = sys.executable


def left(): return A.budget - (time.time() - T0)


def log(**kw):
    kw["t"] = round(time.time() - T0, 1); LOG.write(json.dumps(kw) + "\n"); LOG.flush()


SYSTEM = """You fix Python code so that given pytest tests pass. Use the tools: run_python to look things up, write_file to submit the complete new content of one file under query/. If tools are unavailable, reply in EXACTLY one of two forms:

(A) A probe, to look something up instead of guessing (data values, column names, graph schema, raw file format):
```probe
<short python code; it runs in the task directory with query/ importable; print what you need>
```

(B) The COMPLETE new content of ONE file:
FILE: query/<name>.py
```python
<entire file content>
```

Rules: never recall game data (natures, type chart, stats, moves) from memory when it can be looked up; probe it. Do not break tests that already pass. Keep the code simple. No explanations beyond one short sentence."""


def read(p, limit=None):
    try: s = open(p, errors="replace").read()
    except OSError: return None
    return s if limit is None or len(s) <= limit else s[:limit] + "\n...[truncated]"


def run_tests():
    x = W + "/.junit.xml"
    try: os.remove(x)
    except OSError: pass
    try:
        out = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=", "--tb=short",
                              f"--junitxml={x}", "tests/test_given.py"], cwd=W, capture_output=True, text=True,
                             timeout=max(30, min(300, left()))).stdout
    except subprocess.TimeoutExpired:
        return {"passed": 0, "errors": 99, "fails": {"__timeout__": "tests timed out (infinite loop or very slow code?)"}, "order": ["__timeout__"]}
    res = {"passed": 0, "errors": 0, "fails": {}, "order": []}
    try: root = ET.parse(x).getroot()
    except Exception:
        res["errors"] = 99; res["fails"]["__collect__"] = out[-2500:]; res["order"].append("__collect__"); return res
    for tc in root.iter("testcase"):
        name = tc.get("name") or tc.get("classname")
        bad = [c for c in tc if c.tag in ("failure", "error")]
        if not bad: res["passed"] += 1; continue
        if any(c.tag == "error" for c in bad): res["errors"] += 1
        msg = "\n".join(((c.get("message") or "") + "\n" + (c.text or "")) for c in bad)
        res["fails"][name] = msg[-2500:]; res["order"].append(name)
    if not res["order"] and res["passed"] == 0:
        res["errors"] = 99; res["fails"]["__collect__"] = out[-2500:]; res["order"].append("__collect__")
    res["missing"] = len(missing_modules())
    return res


def score(r): return (r["passed"], -r["errors"], -r.get("missing", 0))


def test_source(name):
    src = read(W + "/tests/test_given.py") or ""
    if len(src) < 5000: return src
    fn = name.split("[")[0]
    try:
        for n in ast.parse(src).body:
            if isinstance(n, ast.FunctionDef) and n.name == fn:
                start = min([d.lineno for d in n.decorator_list] + [n.lineno]) - 1
                return "\n".join(src.splitlines()[start:n.end_lineno])
    except SyntaxError: pass
    return src[:5000]


def missing_modules():
    src = read(W + "/tests/test_given.py") or ""
    mods = re.findall(r"^from (\w+) import", src, re.M)
    if "query/etl.py" in src or "etl.py" in src: mods.append("etl")
    return [m for m in dict.fromkeys(mods) if m not in ("pytest", "json", "os", "sys") and not os.path.exists(f"{W}/query/{m}.py")]


def target_for(err):
    miss = missing_modules()
    if miss: return f"query/{miss[0]}.py"
    frames = re.findall(r"query/(\w+)\.py", err)
    given = {"kuzu_conn", "stats"} if os.path.exists(W + "/graph") else set()
    for f in reversed(frames):
        if f not in given: return f"query/{f}.py"
    src = read(W + "/tests/test_given.py") or ""
    mods = re.findall(r"^from (\w+) import", src, re.M) or ["etl"]
    return f"query/{mods[0]}.py"


def chat(messages, think, temp):
    """Stream one reply. Returns (content, thinking, how) where how is ok|think_cap|time_cap|error."""
    body = {"model": A.model, "messages": messages, "stream": True, "think": think, "tools": TOOLS,
            "options": {"temperature": temp, "num_predict": 8192}}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    content, thinking, how, calls = [], [], "ok", []
    cap_t = min(420, max(20, left() - 5)); t0 = time.time(); think_tok = 0
    try:
        with urllib.request.urlopen(req, timeout=cap_t + 30) as r:
            for line in r:
                ev = json.loads(line); m = ev.get("message") or {}
                if m.get("thinking"): thinking.append(m["thinking"]); think_tok += 1
                if m.get("content"): content.append(m["content"])
                calls += m.get("tool_calls") or []
                if ev.get("done"): break
                if think_tok > A.think_tokens and not content and not calls: how = "think_cap"; break
                if time.time() - t0 > cap_t: how = "time_cap"; break
    except Exception as e:
        how = f"error: {e}"
    return "".join(content), "".join(thinking), how, calls


TOOLS = [
    {"type": "function", "function": {"name": "run_python", "description": "Run a short Python snippet in the task directory (query/ is importable) and see its printed output. Use it to look up data instead of guessing.",
     "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Replace ONE file under query/ with its complete new content. This ends your turn: the tests are run on it.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
]


def ask(messages, think, temp):
    if os.environ.get("FAKE_REF"):   # test mode: answer with the reference file for the current target
        tgt = re.search(r"# Current (query/\w+\.py)", messages[1]["content"]).group(1)
        return f"FILE: {tgt}\n```python\n" + open(os.path.join(os.environ["FAKE_REF"], os.path.basename(tgt))).read() + "```", []
    content, thinking, how, calls = chat(messages, think, temp)
    if how.startswith("error"): time.sleep(5)
    log(ev="llm", think=think, temp=temp, how=how, think_chars=len(thinking), out_chars=len(content), calls=[c["function"]["name"] for c in calls])
    if how in ("think_cap", "time_cap") and not content.strip() and not calls and left() > 30:
        # Budget forcing: keep the reasoning so far, demand a direct answer.
        tail = thinking[-2500:]
        forced = messages + [{"role": "assistant", "content": ""},
                             {"role": "user", "content": "Stop deliberating. Your reasoning so far ended with:\n<<<\n" + tail +
                              "\n>>>\nCommit to the most likely answer now and reply in form (A) or (B) only."}]
        forced = [m for m in forced if m["content"] != "" or m["role"] != "assistant"]
        content, thinking2, how, calls = chat(forced, False, temp)
        log(ev="llm_forced", how=how, out_chars=len(content))
    return content, calls


def run_probe(code, shell=False):
    try:
        cmd = ["/bin/zsh", "-c", code] if shell else [PY, "-c", "import sys; sys.path.insert(0,'query')\n" + code]
        p = subprocess.run(cmd, cwd=W, capture_output=True, text=True, timeout=60)
        out = (p.stdout + ("\nSTDERR:\n" + p.stderr[-1200:] if p.returncode else ""))
    except subprocess.TimeoutExpired:
        out = "probe timed out after 60s"
    return out[:2500] + ("\n...[truncated]" if len(out) > 2500 else "")


def parse(reply, calls=()):
    for c in calls:
        f = c.get("function") or {}; a = f.get("arguments") or {}; n = f.get("name", "")
        if isinstance(a, str):
            try: a = json.loads(a)
            except Exception: a = {}
        if "content" in a and ("path" in a or "file_path" in a): return "file", a.get("path") or a.get("file_path"), a["content"]
        if "code" in a: return "probe", None, a["code"]
        if "command" in a or "cmd" in a: return "shell", None, a.get("command") or a.get("cmd")
    m = re.search(r"```probe\s*\n(.*?)```", reply, re.S)
    if m: return "probe", None, m.group(1)
    m = re.search(r"FILE:\s*`?([\w/.\-]+\.py)`?\s*\n+```(?:python|py)?\s*\n(.*?)```", reply, re.S)
    if m: return "file", m.group(1), m.group(2)
    m = re.search(r"```(?:python|py)\s*\n(.*?)```", reply, re.S)
    if m: return "file", None, m.group(1)
    return "none", None, None


TASK = read(W + "/TASK.md", 9000)
helpers = ""
for f in ("kuzu_conn.py", "stats.py"):
    s = read(f"{W}/query/{f}") if os.path.exists(W + "/graph") else None
    if s: helpers += f"\n--- query/{f} (given, read-only) ---\n{s}\n"

best = run_tests(); bestdir = W + ".l3best"
shutil.rmtree(bestdir, ignore_errors=True); shutil.copytree(W + "/query", bestdir) if os.path.isdir(W + "/query") else os.makedirs(bestdir)
os.makedirs(W + "/query", exist_ok=True)
attempts, notes = {}, {}
log(ev="start", passed=best["passed"], errors=best["errors"], failing=len(best["order"]))
steps = 0
while best["order"] and left() > 25:
    steps += 1
    name = min(best["order"], key=lambda n: (attempts.get(n, 0), best["order"].index(n)))
    k = attempts.get(name, 0); attempts[name] = k + 1
    err = best["fails"][name]; target = target_for(err)
    think = k % 3 != 0                      # 1st try fast, retries think
    temp = [0.6, 0.6, 0.9][k % 3]
    cur = read(f"{W}/{target}")
    total = best["passed"] + len(best["order"])
    user = (f"# TASK.md\n{TASK}\n{helpers}\n# Current {target}\n" + (f"```python\n{cur}\n```" if cur else "(does not exist yet: write it)") +
            f"\n\n# Test status: {best['passed']} of {total} pass.\n# Focus on this failing test: {name}\n```python\n{test_source(name)}\n```\n"
            f"# Error\n```\n{err}\n```\n")
    if notes.get(name): user += "\n# Earlier attempts at this test failed:\n" + "\n".join(notes[name][-3:]) + "\n"
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    applied = False
    for probe_i in range(4):
        if left() < 25: break
        reply, calls = ask(msgs, think, temp)
        kind, path, body = parse(reply, calls)
        log(ev="reply", test=name, attempt=k, kind=kind, path=path, chars=len(reply), via="tool" if calls else "text")
        if kind in ("probe", "shell") and probe_i < 3:
            out = run_probe(body, shell=(kind == "shell"))
            if calls:
                msgs += [{"role": "assistant", "content": reply, "tool_calls": calls[:1]},
                         {"role": "tool", "content": out + "\n(Next: look up more, or call write_file with the complete file.)"}]
            else:
                msgs += [{"role": "assistant", "content": reply},
                         {"role": "user", "content": f"Probe output:\n```\n{out}\n```\nNow reply with another probe or with the file (form B)."}]
            continue
        if kind != "file":
            notes.setdefault(name, []).append("- reply had no FILE block"); break
        path = path if path and path.startswith("query/") and ".." not in path else target
        if os.path.basename(path) in ("kuzu_conn.py", "stats.py") and os.path.exists(W + "/graph"):
            notes.setdefault(name, []).append(f"- tried to edit read-only {path}"); break
        old = read(f"{W}/{path}")
        open(f"{W}/{path}", "w").write(body)
        new = run_tests(); applied = True
        if score(new) > score(best):
            log(ev="accept", test=name, path=path, passed=new["passed"], errors=new["errors"])
            best = new; shutil.rmtree(bestdir, ignore_errors=True); shutil.copytree(W + "/query", bestdir,
                                                                                    ignore=shutil.ignore_patterns("__pycache__"))
        else:
            e2 = new["fails"].get(name, "this test passed but other tests broke")
            notes.setdefault(name, []).append(f"- attempt {k+1}: score {new['passed']} passed (was {best['passed']}); error: {e2.strip()[-400:]}")
            log(ev="reject", test=name, path=path, passed=new["passed"], errors=new["errors"])
            if old is None: os.remove(f"{W}/{path}")
            else: open(f"{W}/{path}", "w").write(old)
        break
log(ev="end", passed=best["passed"], failing=len(best["order"]), steps=steps, secs=round(time.time() - T0))
print(json.dumps({"passed": best["passed"], "total": best["passed"] + len(best["order"]), "steps": steps}))
