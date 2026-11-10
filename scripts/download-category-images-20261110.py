#!/usr/bin/env python3
"""Download verified public Kurdunus category artwork into Shorash-owned repository."""
import json
import pathlib
import urllib.parse
import urllib.request
import time

base=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((base/"imports/kurdunus-category-images-20261110.json").read_text(encoding="utf-8"))
if len(manifest)!=16 or len(set(row["category_id"] for row in manifest))!=16:
    raise RuntimeError("Expected exactly 16 unique categories")
for index,row in enumerate(manifest,1):
    url=row["source_url"]
    if urllib.parse.urlparse(url).hostname!="catalog.kurdunus.com" or "/Public/" not in url:
        raise RuntimeError("Unexpected image host: "+url)
    target=base / row["target"]
    if target.exists() and target.stat().st_size>100:
        print(index, "Already downloaded",target)
        continue
    error=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"Accept":"image/*","User-Agent":"Mozilla/5.0 RESTBR-Shorash-Image-Migration/2.0"})
            with urllib.request.urlopen(req,timeout=35) as resp:
                data=resp.read(5_000_001)
                content_type=str(resp.headers.get("Content-Type","")).lower()
            if not (100 < len(data) <=5_000_000):
                raise ValueError("Size outside supported range")
            if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff") or (data[:4]==b"RIFF" and data[8:12]==b"WEBP")):
                raise ValueError("Not a valid PNG/JPG/WEBP image; type="+content_type)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            print(index,"/",len(manifest),target,len(data),"bytes")
            error=None
            break
        except Exception as exc:
            error=exc
            print("retry",attempt+1,str(exc))
            time.sleep(1)
    if error:
        raise RuntimeError("Unrecoverable category image fetch failure: "+str(error))
print("Verified "+str(len(manifest))+" category images saved")
