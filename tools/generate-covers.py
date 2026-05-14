import requests
import os
import time
from urllib.parse import quote

OUTPUT_DIR = "assets/images/rust-cookbook"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IMAGES = [
    ("11-faylovaya-sistema-cover.png", "pencil sketch, file system directory tree"),
    ("12-raznoe-cover.png", "pencil sketch, CPU processor chip"),
    ("13-operacionnaya-sistema-cover.png",
     "pencil sketch, operating system terminal shell"),
    ("14-obrabotka-teksta-cover.png", "pencil sketch, text processing regex patterns"),
    ("15-veb-razrabotka-cover.png", "pencil sketch, web development HTTP browser"),
]

for i, (filename, prompt) in enumerate(IMAGES):
    out_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(out_path):
        print(f"[{i+1}/{len(IMAGES)}] SKIP (exists): {filename}")
        continue

    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=480&nologo=true"
    print(f"[{i+1}/{len(IMAGES)}] Generating: {filename} — {prompt}")

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
        time.sleep(3)

print("\nDone!")
