import requests
import os
import time
from urllib.parse import quote

IMAGES = [
    # Tokio series
    ("tokio/tokio-cover.png", "pencil sketch, async runtime engine"),
    ("tokio/01-obzor-cover.png", "pencil sketch, server network overview"),
    ("tokio/02-nastroyka-cover.png", "pencil sketch, terminal setup"),
    ("tokio/03-sozdanie-potokov-cover.png", "pencil sketch, spawning threads"),
    ("tokio/04-obshchee-sostoyanie-cover.png",
     "pencil sketch, shared database lock"),
    ("tokio/05-kanaly-cover.png", "pencil sketch, message channels pipes"),
    ("tokio/06-vvod-vyvod-cover.png", "pencil sketch, input output data stream"),
    ("tokio/07-kadrirovanie-cover.png", "pencil sketch, data framing packets"),
    ("tokio/08-asinkhronnost-cover.png", "pencil sketch, gears async machinery"),
    ("tokio/09-vybor-cover.png", "pencil sketch, branching path selection"),
    ("tokio/10-potoki-cover.png", "pencil sketch, flowing data stream"),
]

for i, (filepath, prompt) in enumerate(IMAGES):
    out_path = os.path.join("assets/images", filepath)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if os.path.exists(out_path):
        print(f"[{i+1}/{len(IMAGES)}] SKIP (exists): {filepath}")
        continue

    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=480&nologo=true"
    print(f"[{i+1}/{len(IMAGES)}] Generating: {filepath} — {prompt}")

    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()

        with open(out_path, "wb") as f:
            f.write(resp.content)

        size_kb = len(resp.content) / 1024
        print(f"  -> Saved ({size_kb:.0f} KB)")
    except Exception as e:
        print(f"  -> ERROR: {e}")

    if i < len(IMAGES) - 1:
        time.sleep(5)

print("\nDone!")
