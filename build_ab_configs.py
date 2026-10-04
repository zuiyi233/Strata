import json

SRC = r"N:/Strata/strata-swift-iq3_xxs.json"

base = json.load(open(SRC, encoding="utf-8"))


def save(cfg, name):
    path = rf"N:/Strata/{name}"
    json.dump(cfg, open(path, "w", encoding="utf-8"), indent=1)
    print(name, "->", "kv:", end=" ")
    a = cfg["args"]
    print(a[a.index("--kv") + 1], "| peer:", "--peer-device" in a)


# 变体1：KV 换 q4_0（Ampere tensor core），其余不动
q40 = json.loads(json.dumps(base))
i = q40["args"].index("int8")
q40["args"][i] = "q4_0"
save(q40, "ab-q40.json")

# 变体2：q4_0 + peer-device 1（T10 专家层，就地计算）
qp = json.loads(json.dumps(q40))
qp["args"] += ["--peer-device", "1"]
save(qp, "ab-q40-peer.json")
