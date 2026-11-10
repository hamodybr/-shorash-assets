#!/usr/bin/env python3
import json
import pathlib
import urllib.request
import time

root = pathlib.Path(__file__).resolve().parents[1]
items = json.loads((root / "imports/shorash-images-20261110.json").read_text(encoding="utf-8"))
for number, item in enumerate(items, start=1):
    image_name = item["file"]
    if "/" in image_name or "\\" in image_name or ".." in image_name or not image_name:
        raise ValueError("Invalid filename")
    target = root / item["target"]
    if target.exists() and target.stat().st_size > 100:
        print(number, "already saved:", target)
        continue
    url = "https://catalog.kurdunus.com/Public/" + image_name
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RestBrAssetMigration/1.0", "Accept":"image/*"})
            with urllib.request.urlopen(request, timeout=25) as res:
                data = res.read(8_000_001)
                mime = str(res.headers.get("Content-Type","")).lower()
                if len(data) > 8_000_000 or len(data) < 100:
                    raise ValueError("Invalid image size")
                image_magic = data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"RIFF") and data[8:12] == b"WEBP"
                if not image_magic:
                    raise ValueError("Downloaded file is not JPEG/PNG/WebP: " + mime)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                print(number, "/", len(items), target, len(data))
            error = None
            break
        except Exception as exc:
            error = exc
            print("retry", attempt + 1, url, str(exc))
            time.sleep(1)
    if error:
        raise RuntimeError("Image download failed, no commit will be made: " + url + ": " + str(error))
print("All", len(items), "images downloaded")
