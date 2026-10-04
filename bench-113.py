"""A/B bench for the merged-forks engine vs the current 0.1.38 release engine.

Protocol per engine: start server.py with a bench config (port 8080), wait for /health,
run 6x fresh-8K-prefill + 512-token rounds and 3x fresh-64K rounds (unique marker paragraph
per round so the conversation cache never reuses the prompt), parse the engine log's DONE
line (authoritative), then one temperature-0 consistency probe. Kills the process tree after.
"""
import json, os, subprocess, sys, time, urllib.request, statistics

ROOT = "/data3t/strata-deploy/Strata-final"
PORT = 8080
HEALTH = f"http://127.0.0.1:{PORT}/health"
URL = f"http://127.0.0.1:{PORT}/v1/chat/completions"


def marker(i):
    return (f"Bench marker {i:03d}: the quartz weathervane above the harbour office turns in the "
            f"north-easterly breeze while the ferry logs its departure. ")


def variant_payload(base_path, i, out_path):
    d = json.load(open(base_path, encoding="utf-8"))
    d["messages"][0]["content"] = marker(i) + d["messages"][0]["content"]
    json.dump(d, open(out_path, "w", encoding="utf-8"))
    return out_path


def wait_health(timeout_s=900):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(HEALTH, timeout=3) as r:
                if r.status == 200:
                    return time.time() - t0
        except Exception:
            time.sleep(2)
    raise RuntimeError("engine did not become healthy")


def last_done(log_path, since_lines):
    """Return the last per-request summary line appended to the log after `since_lines` lines.

    server.py rewrites the engine's DONE line as:
    'strata serve: prompt N tokens = R reused + F read in P ms (X tok/s), G generated in D ms (Y tok/s), drafts accepted A of B'
    """
    for _ in range(60):
        with open(log_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if len(lines) > since_lines:
            for line in reversed(lines[since_lines:]):
                if "strata serve: prompt" in line and "generated in" in line:
                    return line.strip()
        time.sleep(1)
    raise RuntimeError("no serve summary line found")


def request_round(payload_path):
    raw = open(payload_path, "rb").read()
    req = urllib.request.Request(URL, data=raw, headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    with urllib.request.urlopen(req, timeout=3600) as resp:
        for line in resp:
            line = line.decode("utf-8", "replace").strip()
            if ttft is None and line.startswith("data: ") and line != "data: [DONE]":
                ttft = time.time() - t0
            if line == "data: [DONE]":
                break
    return ttft, time.time() - t0


import re
SUMMARY_RE = re.compile(
    r"prompt (\d+) tokens = (\d+) reused \+ (\d+) read in ([\d.]+) ms \(([\d.]+) tok/s\), "
    r"(\d+) generated in ([\d.]+) ms \(([\d.]+) tok/s\), drafts accepted (\d+) of (\d+)")


def parse_done(line):
    m = SUMMARY_RE.search(line)
    if not m:
        raise RuntimeError(f"unparsed summary line: {line}")
    g = dict(prompt_tokens=int(m.group(1)), reused=int(m.group(2)), read=int(m.group(3)),
             prompt_ms=float(m.group(4)), prefill_tok_s=float(m.group(5)),
             generated=int(m.group(6)), decode_ms=float(m.group(7)), decode_tok_s=float(m.group(8)),
             drafts_accepted=int(m.group(9)), drafts_offered=int(m.group(10)), finish="n/a")
    return g


def run_engine(config, tag, rounds8=6, rounds64=3):
    log = json.load(open(config, encoding="utf-8"))["log"]
    proc = subprocess.Popen([os.path.join(ROOT, ".venv", "Scripts", "python.exe"),
                             os.path.join(ROOT, "serve", "server.py"), "--engine", "strata",
                             "--config", config, "--port", str(PORT)], cwd=ROOT)
    results = {"tag": tag, "config": config}
    try:
        results["ready_s"] = round(wait_health(), 1)
        time.sleep(3)
        with open(log, encoding="utf-8", errors="replace") as f:
            base_lines = len(f.readlines())
        for size, n in (("8k", rounds8), ("64k", rounds64)):
            base = os.path.join(ROOT, f"bench-payload-{size}.json")
            tmp = os.path.join(ROOT, f"bench-merge-tmp-{size}.json")
            rounds = []
            for i in range(n):
                p = variant_payload(base, i, tmp)
                log_lines = sum(1 for _ in open(log, encoding="utf-8", errors="replace"))
                ttft, total = request_round(p)
                stat = parse_done(last_done(log, log_lines))
                stat.update(ttft_s=round(ttft, 2), wall_s=round(total, 2), round=i)
                rounds.append(stat)
                print(f"[{tag}] {size} r{i}: decode {stat['decode_tok_s']:.1f} tok/s "
                      f"prefill {stat['prefill_tok_s']:.0f} tok/s drafts {stat['drafts_accepted']}/{stat['drafts_offered']}")
            results[size] = rounds
            os.remove(tmp)
        # temperature-0 consistency probe
        payload = {"model": "strata", "stream": False, "temperature": 0, "max_tokens": 96,
                   "messages": [{"role": "user", "content": "In one sentence, what is a lighthouse?"}]}
        req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            results["probe"] = json.loads(r.read().decode())["choices"][0]["message"]["content"]
        return results
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        time.sleep(5)


def summarize(results):
    out = {"tag": results["tag"], "ready_s": results["ready_s"]}
    for size in ("8k", "64k"):
        r = results[size]
        out[f"{size}_decode_med"] = round(statistics.median(x["decode_tok_s"] for x in r), 2)
        out[f"{size}_prefill_med"] = round(statistics.median(x["prefill_tok_s"] for x in r), 0)
        out[f"{size}_draft_accept"] = round(statistics.median(
            x["drafts_accepted"] / x["drafts_offered"] for x in r if x["drafts_offered"]) * 100, 1)
    out["probe"] = results["probe"]
    return out


if __name__ == "__main__":
    which = sys.argv[1]
    config = os.path.join(ROOT, f"strata-merge-bench-{which}.json")
    res = run_engine(config, which)
    json.dump(res, open(os.path.join(ROOT, f"bench-merge-result-{which}.json"), "w"), indent=1)
    print(json.dumps(summarize(res), indent=1))
