import json, time, urllib.request, sys, os

ROOT = r"N:/Strata"
BASE_URL = "http://127.0.0.1:8080"

PARA = ("The lighthouse keeper climbed the worn spiral stairs each morning, counted the brass gears of the great "
        "clockwork lamp, refilled the oil reservoir, checked the weather glass, and wrote the day's numbers into "
        "the leather ledger before the fog rolled back over the harbour wall. ")


def build():
    for name, chars in [("200k", 800_000), ("60k", 240_000)]:
        parts = []
        n = 0
        while n < chars:
            for i in range(200):
                parts.append(f"[{i:04d}] " + PARA)
                n += len(PARA) + 7
                if n >= chars:
                    break
        body = "".join(parts)[:chars]
        payload = {"model": "strata", "stream": True, "max_tokens": 8,
                   "messages": [{"role": "user", "content": body}]}
        path = os.path.join(ROOT, f"bench-payload-{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        print(name, "chars:", len(body), "->", path)


def run(tag):
    payload_name = "200k" if "3090" in tag else "60k"
    payload_path = os.path.join(ROOT, f"bench-payload-{payload_name}.json")
    with open(payload_path, "rb") as f:
        raw = f.read()
    req = urllib.request.Request(BASE_URL + "/v1/chat/completions", data=raw,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    chunks = 0
    with urllib.request.urlopen(req, timeout=3600) as resp:
        for line in resp:
            line = line.decode("utf-8", "replace").strip()
            if line.startswith("data: ") and line != "data: [DONE]":
                if ttft is None:
                    ttft = time.time() - t0
                chunks += 1
            if line == "data: [DONE]":
                break
    total = time.time() - t0
    out = {"tag": tag, "payload": payload_name,
           "ttft_s": round(ttft, 2) if ttft else None,
           "total_s": round(total, 2), "chunks": chunks}
    with open(os.path.join(ROOT, f"bench-200k-result-{tag}.json"), "w") as f:
        json.dump(out, f)
    print(json.dumps(out))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd.startswith("run"):
        run(cmd[3:] or "3090")
