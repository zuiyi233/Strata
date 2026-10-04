import zlib, struct, base64, json, sys

def make_png(path, w=64, h=64):
    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x20\x40\xa0" * w for _ in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return png

png = make_png("N:/Strata/test-image.png")
b64 = base64.b64encode(png).decode()
payload = {
    "model": "strata", "stream": True, "max_tokens": 128,
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Describe this image in one short sentence."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}
    ]}]
}
with open("N:/Strata/bench-payload-image.json", "w", encoding="utf-8") as f:
    json.dump(payload, f)
print("png bytes:", len(png), "-> N:/Strata/test-image.png + bench-payload-image.json")
