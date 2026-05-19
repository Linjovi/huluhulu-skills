#!/usr/bin/env python3
"""
AI Image Generation Script — draw-image skill runtime.

Self-contained, no third-party dependencies.
API key is read from the GRSAI_API_KEY environment variable.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# ████████████████████████████████████████████████████████████████████████
# ██                                                                    ██
# ██         ⚠️  GRSAI_API_KEY CONFIGURATION REQUIRED ⚠️               ██
# ██                                                                    ██
# ██   YOU MUST SET THE ENVIRONMENT VARIABLE BEFORE RUNNING            ██
# ██                                                                    ██
# ██         ENV VARIABLE: GRSAI_API_KEY                               ██
# ██                                                                    ██
# ██   Example (macOS / Linux):                                        ██
# ██       export GRSAI_API_KEY="your_api_key_here"                    ██
# ██                                                                    ██
# ██   Example (Windows PowerShell):                                   ██
# ██       $env:GRSAI_API_KEY="your_api_key_here"                      ██
# ██                                                                    ██
# ████████████████████████████████████████████████████████████████████████

GRSAI_API_KEY = os.environ.get("GRSAI_API_KEY", "").strip()
if not GRSAI_API_KEY:
    raise RuntimeError(
        """
╔══════════════════════════════════════════════════════════════╗
║                   GRSAI_API_KEY REQUIRED                     ║
╠══════════════════════════════════════════════════════════════╣
║  Environment variable GRSAI_API_KEY is not set.              ║
║                                                              ║
║  macOS / Linux:                                              ║
║      export GRSAI_API_KEY="your_api_key_here"                ║
║      source ~/.zshrc                                         ║
║                                                              ║
║  Windows PowerShell:                                         ║
║      $env:GRSAI_API_KEY="your_api_key_here"                  ║
║                                                              ║
║  Then run the program again.                                 ║
╚══════════════════════════════════════════════════════════════╝
"""
    )

API_BASE = "https://grsai.dakka.com.cn"
REQUEST_TIMEOUT = 300  # 5 minutes


def _make_request(url, data, headers):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8").strip()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Request failed: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _generate_image(prompt, model, aspect_ratio, quality, images):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRSAI_API_KEY}",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images or [],
        "replyType": "json",
    }
    if aspect_ratio:
        payload["aspectRatio"] = aspect_ratio
    if quality:
        payload["quality"] = quality

    print(f"Submitting generation request (json mode, timeout={REQUEST_TIMEOUT}s)...", file=sys.stderr)
    result = _make_request(f"{API_BASE}/v1/api/generate", payload, headers)

    status = result.get("status", "")
    if status == "violation":
        print(f"Content violation: {result.get('error', '')}", file=sys.stderr)
        sys.exit(1)
    elif status == "failed":
        print(f"Generation failed: {result.get('error', '')}", file=sys.stderr)
        sys.exit(1)
    elif status != "succeeded":
        print(f"Unexpected status '{status}': {result}", file=sys.stderr)
        sys.exit(1)

    results = result.get("results", [])
    if not results:
        print("No results in response", file=sys.stderr)
        sys.exit(1)

    return results[0]["url"]


def _download_image(image_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = image_url.split("?")[0].rsplit(".", 1)[-1] if "." in image_url else "png"
    filepath = os.path.join(output_dir, f"image_{timestamp}.{ext}")

    print(f"Downloading from {image_url}", file=sys.stderr)
    try:
        urllib.request.urlretrieve(image_url, filepath)
    except urllib.error.URLError as e:
        print(f"Download failed: {e.reason}", file=sys.stderr)
        sys.exit(1)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Generate image via grsai API")
    parser.add_argument("--prompt", required=True, help="Image prompt")
    parser.add_argument("--model", default="gpt-image-2", help="Model name")
    parser.add_argument("--aspect-ratio", default="1024x1024", help="Aspect ratio, e.g. 1024x1024, 16:9")
    parser.add_argument(
        "--quality", choices=["auto", "low", "medium", "high"], help="Image quality"
    )
    parser.add_argument(
        "--images", nargs="+", help="Reference images (base64 or URLs)"
    )
    parser.add_argument(
        "--output-dir", default="./generated_images", help="Local save directory"
    )
    args = parser.parse_args()

    image_url = _generate_image(
        args.prompt,
        args.model,
        args.aspect_ratio,
        args.quality,
        args.images,
    )

    local_path = _download_image(image_url, args.output_dir)

    print(json.dumps({"success": True, "local_path": local_path, "remote_url": image_url}))


if __name__ == "__main__":
    main()
