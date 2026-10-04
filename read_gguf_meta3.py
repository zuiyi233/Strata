import subprocess, struct

path = "L:/Qwen3.8/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf"

out = subprocess.run(["grep", "-aboE", r"qwen4exp\.[a-z._0-9]+", path], capture_output=True, text=True)
matches = {}
for line in out.stdout.splitlines():
    off, key = line.split(":", 1)
    matches.setdefault(key, int(off))
print(f"distinct keys: {len(matches)}")

WANT = ("general", "expert", "layer", "embed", "head", "context", "vocab",
        "feed", "ffn", "tensor", "n_", "parameter", "sizes")

with open(path, "rb") as f:
    for key in sorted(matches):
        if not any(w in key for w in WANT):
            continue
        off = matches[key]
        f.seek(off + len(key))
        t = struct.unpack("<I", f.read(4))[0]
        if t == 4: v = struct.unpack("<I", f.read(4))[0]
        elif t == 5: v = struct.unpack("<i", f.read(4))[0]
        elif t == 10: v = struct.unpack("<Q", f.read(8))[0]
        elif t == 11: v = struct.unpack("<q", f.read(8))[0]
        elif t == 6: v = round(struct.unpack("<f", f.read(4))[0], 4)
        elif t == 8:
            n = struct.unpack("<Q", f.read(8))[0]
            v = f.read(min(n, 64)).decode("utf-8", "replace")[:60]
        else: v = f"<t{t}>"
        print(f"{key} = {v}")