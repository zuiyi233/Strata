import struct, sys

path = sys.argv[1]

fd = open(path, "rb")
# budget: only parse the first 1 MB of metadata (all small scalar keys live there)
BUDGET = 1 << 20
read = fd.read
taken = 0

def take(n):
    global taken
    if taken + n > BUDGET:
        raise RuntimeError(f"budget exhausted at ~{taken // 1024} KiB")
    b = read(n)
    if len(b) != n:
        raise RuntimeError("short read")
    taken += n
    return b

magic = take(4)
assert magic == b"GGUF", magic
version, tensor_count = struct.unpack("<IQ", take(12))
kv_count = struct.unpack("<Q", take(8))[0]
print(f"gguf v{version} tensors={tensor_count} kv={kv_count}")

def rd_str():
    n = struct.unpack("<Q", take(8))[0]
    if n > BUDGET:
        raise RuntimeError("huge string")
    return take(n).decode("utf-8", "replace")

def rd_val(t, depth=0):
    if t == 0: return take(1)[0]
    if t == 1: return struct.unpack("<b", take(1))[0]
    if t == 2: return struct.unpack("<H", take(2))[0]
    if t == 3: return struct.unpack("<h", take(2))[0]
    if t == 4: return struct.unpack("<I", take(4))[0]
    if t == 5: return struct.unpack("<i", take(4))[0]
    if t == 6: return struct.unpack("<f", take(4))[0]
    if t == 7: return bool(take(1)[0])
    if t == 8: return rd_str()
    if t == 9:
        n = struct.unpack("<Q", take(8))[0]
        et = struct.unpack("<I", take(4))[0]
        if n > 4096:
            return f"<arr n={n} et={et} (skipped)>"
        return [rd_val(et, depth + 1) for _ in range(n)]
    if t == 10: return struct.unpack("<Q", take(8))[0]
    if t == 11: return struct.unpack("<q", take(8))[0]
    if t == 12: return struct.unpack("<d", take(8))[0]
    if t == 13: return struct.unpack("<e", take(2))[0]
    return f"<type{t}>"

KEYS = ("general.architecture", "general.name", "llama.expert_count",
        "llama.expert_used_count", "llama.attention.layer_count",
        "llama.embedding_length", "llama.attention.head_count",
        "llama.context_length", "llama.vocab_size", "llama.feed_forward_length",
        "llama.expert_feed_forward_length", "llama.attention.key_length")

n_read = 0
for i in range(kv_count):
    try:
        k = rd_str()
        t = struct.unpack("<I", take(4))[0]
        v = rd_val(t)
        n_read += 1
        if k in KEYS:
            print(f"[{i}] {k} = {v}", flush=True)
    except RuntimeError as e:
        print(f"stop at kv[{i}]: {e}", flush=True)
        break
print(f"kv scanned: {n_read}", flush=True)
fd.close()