import json

ROOT = "N:/Strata"
SRC = ROOT + "/strata-swift-iq3_xxs.json"

with open(SRC, "r", encoding="utf-8-sig") as f:
    cfg = json.load(f)

for spec in (2, 3, 5):
    out = json.loads(json.dumps(cfg))
    args = out["args"]
    i = args.index("--spec")
    args[i + 1] = str(spec)
    out["log"] = f"N:\\Strata\\spec-sweep-{spec}.log"
    name = f"ab-spec{spec}.json"
    with open(ROOT + "/" + name, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(name, "spec =", args[i + 1], "log =", out["log"])
