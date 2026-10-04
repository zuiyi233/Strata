import zlib, struct, base64, json

def make_png(path, w, h):
    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    # diagonal gradient: distinct content per patch
    row = b""
    rows = []
    for y in range(h):
        row = b""
        for x in range(w):
            row += bytes(((x * 7 + y * 3) & 255, (y * 5) & 255, (x * 11) & 255))
        rows.append(b"\x00" + row)
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return png

for w, h in ((1024, 1024), (512, 512)):
    png = make_png(f"N:/Strata/test-image-{w}.png", w, h)
    b64 = base64.b64encode(png).decode()
    payload = {
        "model": "strata", "stream": True, "max_tokens": 8,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "What is the dominant color pattern in this image?"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}
        ]}]
    }
    with open(f"N:/Strata/bench-payload-image-{w}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"image {w}x{h}: png={len(png)}B b64={len(b64)//1024}KiB payload saved")
