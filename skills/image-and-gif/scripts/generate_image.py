#!/usr/bin/env python3
"""
Generate an image via the OpenAI-compatible /v1/images/generations endpoint.

Fixed model: gpt-image-2, fixed response_format: url.
Size is specified as a ratio string and mapped to exact pixel dimensions.

Env: OPENAI_API_KEY (required), OPENAI_BASE_URL (optional).
No third-party dependencies.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.environ.get(
    "OPENAI_BASE_URL", "https://api.openai.com").strip().rstrip("/")

REQUEST_TIMEOUT = 600

RATIO_MAP = {
    "1:1": "1024x1024",
    "16:9": "1672x941",
    "9:16": "941x1672",
    "4:3": "1443x1090",
    "3:4": "1090x1443",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
    "5:4": "1408x1120",
    "4:5": "1120x1408",
    "21:9": "1920x832",
    "9:21": "832x1920",
    "1:2": "896x1792",
    "2:1": "1792x896",
}


def _die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _require_key():
    if not OPENAI_API_KEY:
        _die(
            "OPENAI_API_KEY environment variable is required.\n"
            "  macOS / Linux: export OPENAI_API_KEY=\"sk-...\""
        )


def resolve_api_url(path="/v1/images/generations"):
    base = OPENAI_BASE_URL
    if base.endswith("/v1") and path.startswith("/v1/"):
        return f"{base}{path[3:]}"
    return f"{base}{path}"


def resolve_size(ratio):
    """Map a ratio string to exact pixel dimensions."""
    if ratio in RATIO_MAP:
        return RATIO_MAP[ratio]
    _die(
        f"Unsupported ratio '{ratio}'. "
        f"Supported: {', '.join(RATIO_MAP.keys())}"
    )


def _load_reference(ref):
    """Return a usable string for the `image` array."""
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    if not os.path.isfile(ref):
        _die(f"Reference not found: {ref}")
    mime, _ = mimetypes.guess_type(ref)
    if not mime:
        mime = "image/png"
    with open(ref, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _post_json(url, payload, headers):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body)
            msg = parsed.get("error", {}).get("message", err_body)
        except Exception:
            msg = err_body
        _die(f"HTTP {e.code} from {url}: {msg}")
    except urllib.error.URLError as e:
        _die(f"Request failed: {e.reason}")


def _save_item(item, output_path):
    if item.get("url"):
        print(f"Downloading image from {item['url']}", file=sys.stderr)
        try:
            urllib.request.urlretrieve(item["url"], output_path)
        except urllib.error.URLError as e:
            _die(f"Download failed: {e.reason}")
        return
    _die(f"Unrecognized response item (no url): {item}")


def generate_image(
    prompt,
    ratio="1:1",
    references=None,
    output_dir="./generated_images",
    output_path=None,
    file_prefix="image",
    no_download=False,
):
    """Call /v1/images/generations once.

    If no_download is True, returns the raw data item dict (containing url)
    instead of saving to disk. Otherwise returns the local file path.
    """
    _require_key()

    size = resolve_size(ratio)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "image": [_load_reference(r) for r in (references or [])],
        "size": size,
        "response_format": "url",
    }

    url = resolve_api_url("/v1/images/generations")
    print(f"POST {url}  model=gpt-image-2  size={size}  refs={len(payload['image'])}",
          file=sys.stderr)

    result = _post_json(url, payload, headers)

    data = result.get("data") or []
    if not data:
        _die(f"No image data in response: {result}")

    item = data[0]

    if no_download:
        return item

    os.makedirs(output_dir, exist_ok=True)
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir, f"{file_prefix}_{timestamp}.png")

    _save_item(item, output_path)

    usage = result.get("usage")
    if usage:
        print(f"usage: {usage}", file=sys.stderr)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate a single image via /v1/images/generations"
    )
    parser.add_argument("--prompt", required=True, help="Image description")
    parser.add_argument("--ratio", default="1:1",
                        help=f'Aspect ratio (default 1:1). Supported: {", ".join(RATIO_MAP.keys())}')
    parser.add_argument("--references", nargs="+",
                        help="Reference images: file paths, http(s) URLs, or data URLs")
    parser.add_argument(
        "--output-dir", default="./generated_images", help="Output directory")
    parser.add_argument("--output-path", help="Explicit output PNG path")
    parser.add_argument("--file-prefix", default="image",
                        help="Output filename prefix (default 'image')")
    parser.add_argument("--no-download", action="store_true",
                        help="Do not save the image locally; return remote_url instead")
    args = parser.parse_args()

    result = generate_image(
        prompt=args.prompt,
        ratio=args.ratio,
        references=args.references,
        output_dir=args.output_dir,
        output_path=args.output_path,
        file_prefix=args.file_prefix,
        no_download=args.no_download,
    )

    if args.no_download:
        out = {"success": True}
        if isinstance(result, dict) and result.get("url"):
            out["remote_url"] = result["url"]
        print(json.dumps(out))
    else:
        print(f"Image saved: {result}", file=sys.stderr)
        print(json.dumps({"success": True, "local_path": result}))


if __name__ == "__main__":
    main()
