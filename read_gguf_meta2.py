import subprocess, struct, sys, re

path = "L:/Qwen3.8/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf"

KEYS = ["llama.expert_count", "llama.expert_used_count", "llama.attention.layer_count",
        "llama.embedding_length", "llama.attention.head_count", "llama.context_length",
        "llama.vocab_size", "llama.feed_forward_length", "llama.expert_feed_forward_length",
        "llama.attention.key_length", "llama.attention.value_length", "qwen4exp.expert_count"]

pat = "|".join(re.escape(k) for k in KEYS)
out = subprocess.run(["grep", "-aboE", pat, path], capture_output=True, text=True)
print("grep done, matches:", len(out.stdout.strip().splitlines()), "rc=", out.returncode)

offsets = {}
for line in out.stdout.splitlines():
    off, key = line.split(":", 1)
    offsets.setdefault(key, int(off))

with open(path, "rb") as f:
    for key in KEYS:
        off = offsets.get(key)
        if off is None:
            print(f"{key} = (not found directly; likely named differently)")
            continue
        f.seek(off + len(key))
        t = struct.unpack("<I", f.read(4))[0]
        if t == 4: v = struct.unpack("<I", f.read(4))[0]
        elif t == 5: v = struct.unpack("<i", f.read(4))[0]
        elif t == 10: v = struct.unpack("<Q", f.read(8))[0]
        elif t == 11: v = struct.unpack("<q", f.read(8))[0]
        elif t == 6: v = round(struct.unpack("<f", f.read(4))[0], 2)
        else: v = f"<type{t}>"
        print(f"{key} = {v}")