#!/usr/bin/env python3
"""
Generate a 3x3 grid image whose 9 cells are 9 consecutive frames of an action.

Supports three image-generation providers via --provider:
  - gpt-image   : OpenAI /v1/images/generations  (env: OPENAI_API_KEY, OPENAI_BASE_URL)
  - nanobanana  : Google Gemini generateContent   (env: GEMINI_API_KEY, GEMINI_BASE_URL)
  - seedream    : Volcano Ark /v3/images/generations (env: ARK_API_KEY, ARK_BASE_URL)

No third-party dependencies (stdlib only).
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

# ── Grid prompt template (hard constraint) ──────────────────────────────

GRID_PROMPT_TEMPLATE = """Generate ONE single square image. The image content shows 9 consecutive frames of an animation arranged as a 3x3 mosaic (each frame occupies exactly 1/9 of the image area; frame side = image_side / 3).

ABSOLUTE LAYOUT RULES (must obey, do NOT violate):
1. EDGE-TO-EDGE tiling. Frames touch each other with ZERO gap, ZERO padding, ZERO border, ZERO white space, ZERO gutter, ZERO seam, ZERO dividing line, ZERO outline. The boundary between adjacent frames is implicit / mathematical (at exactly 1/3 and 2/3 positions of the image), NEVER drawn or visible.
2. NO frame numbers, NO labels, NO captions, NO watermarks, NO text of any kind anywhere.
3. All 9 frames share IDENTICAL camera angle, framing, scale, background color, lighting and art style — as if rendered from the same scene with only the subject's pose changing across frames.
4. NO element crosses a frame boundary; each pose stays fully inside its 1/9 region.
5. STRICT EQUAL CELLS. All 9 cells have the same width and the same height (cell_w = cell_h = image_side / 3 EXACTLY). The 3 columns are vertically aligned at x = 0, image_side/3, 2*image_side/3, image_side; the 3 rows are horizontally aligned at y = 0, image_side/3, 2*image_side/3, image_side. Do NOT make the center column or any single cell wider or narrower than the others.
6. SUBJECT CENTERED WITH SAFETY MARGIN. In every frame, the subject is placed at the geometric center of its own cell, with at least 15% padding between the subject's bounding box and EACH of the four cell edges. The subject never approaches a cell edge; the outer 15% of every cell is safe-margin background.
7. FIXED SUBJECT ANCHOR (critical for animation). The subject's torso/head center must occupy the EXACT SAME position within every cell — identical horizontal AND vertical coordinates across all 9 frames. Only small local features (eyes, mouth, paws, tail tip) may move; the body core must NOT drift, bounce, or shift between frames.
8. STABLE BASELINE. If the subject stands or sits, its ground contact point (paws/feet/base) stays on the same horizontal line in every frame. Do NOT lift, drop, or slide the whole body while animating.

Frame order (left to right, top to bottom):
  frame1 frame2 frame3
  frame4 frame5 frame6
  frame7 frame8 frame9

Animation content:
{user_prompt}"""


# ── Helpers ─────────────────────────────────────────────────────────────

REQUEST_TIMEOUT = 600


def _die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _load_reference(ref):
    """Return a dict usable across providers: {'url': ...} or {'data': b64, 'mime': ...}."""
    if ref.startswith(("http://", "https://")):
        return {"url": ref}
    if ref.startswith("data:"):
        # data:image/png;base64,xxxx
        header, _, b64 = ref.partition(",")
        mime = "image/png"
        if ";" in header:
            mime = header[5:].split(";")[0] or mime
        return {"data": b64, "mime": mime}
    if not os.path.isfile(ref):
        _die(f"Reference not found: {ref}")
    mime, _ = mimetypes.guess_type(ref)
    if not mime:
        mime = "image/png"
    with open(ref, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return {"data": b64, "mime": mime}


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


def _download(url, output_path):
    print(f"Downloading image from {url}", file=sys.stderr)
    try:
        urllib.request.urlretrieve(url, output_path)
    except urllib.error.URLError as e:
        _die(f"Download failed: {e.reason}")


def _save_b64(b64_data, output_path):
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64_data))


# ── Provider: gpt-image (OpenAI-compatible) ─────────────────────────────

def _generate_gpt_image(prompt, references, output_path):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _die("OPENAI_API_KEY environment variable is required.\n"
             "  macOS / Linux: export OPENAI_API_KEY=\"sk-...\"")
    base_url = os.environ.get(
        "OPENAI_BASE_URL", "https://api.openai.com").strip().rstrip("/")
    # Resolve URL: handle base URLs that already end with /v1
    path = "/v1/images/generations"
    if base_url.endswith("/v1") and path.startswith("/v1/"):
        url = f"{base_url}{path[3:]}"
    else:
        url = f"{base_url}{path}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    image_arr = []
    for ref in (references or []):
        r = _load_reference(ref)
        if "url" in r:
            image_arr.append(r["url"])
        else:
            image_arr.append(f"data:{r['mime']};base64,{r['data']}")

    payload = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "image": image_arr,
        "size": "1024x1024",
        "response_format": "url",
    }
    print(f"POST {url}  provider=gpt-image  model=gpt-image-1  size=1024x1024  "
          f"refs={len(image_arr)}", file=sys.stderr)
    result = _post_json(url, payload, headers)
    data = result.get("data") or []
    if not data:
        _die(f"No image data in response: {result}")
    item = data[0]
    if item.get("url"):
        _download(item["url"], output_path)
    elif item.get("b64_json"):
        _save_b64(item["b64_json"], output_path)
    else:
        _die(f"Unrecognized response item: {item}")


# ── Provider: nanobanana (Google Gemini) ────────────────────────────────

def _generate_nanobanana(prompt, references, output_path):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        _die("GEMINI_API_KEY environment variable is required.\n"
             "  macOS / Linux: export GEMINI_API_KEY=\"...\"")
    base_url = os.environ.get(
        "GEMINI_BASE_URL",
        "https://generativelanguage.googleapis.com").strip().rstrip("/")
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

    url = (f"{base_url}/v1beta/models/{model}:generateContent"
           f"?key={api_key}")

    headers = {"Content-Type": "application/json"}

    parts = [{"text": prompt}]
    for ref in (references or []):
        r = _load_reference(ref)
        if "data" in r:
            parts.append({
                "inline_data": {
                    "mime_type": r["mime"],
                    "data": r["data"],
                }
            })
        elif "url" in r:
            # Gemini file URI or GCS URI would go here; for http URLs,
            # download and convert to inline_data
            try:
                with urllib.request.urlopen(r["url"]) as resp:
                    img_bytes = resp.read()
                b64 = base64.b64encode(img_bytes).decode("ascii")
                ct = resp.headers.get("Content-Type", "image/png")
                parts.append({
                    "inline_data": {
                        "mime_type": ct,
                        "data": b64,
                    }
                })
            except Exception:
                _die(f"Failed to load reference URL: {r['url']}")

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    print(f"POST {base_url}/v1beta/models/{model}:generateContent  "
          f"provider=nanobanana  refs={len(parts)-1}", file=sys.stderr)
    result = _post_json(url, payload, headers)

    candidates = result.get("candidates") or []
    if not candidates:
        _die(f"No candidates in Gemini response: {result}")

    content = candidates[0].get("content", {})
    parts_resp = content.get("parts", [])
    for part in parts_resp:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            _save_b64(inline["data"], output_path)
            return
    _die(f"No image data in Gemini response parts: {parts_resp}")


# ── Provider: seedream (Volcano Engine Ark) ─────────────────────────────

def _generate_seedream(prompt, references, output_path):
    api_key = os.environ.get("ARK_API_KEY", "").strip()
    if not api_key:
        _die("ARK_API_KEY environment variable is required.\n"
             "  macOS / Linux: export ARK_API_KEY=\"...\"")
    base_url = os.environ.get(
        "ARK_BASE_URL",
        "https://ark.cn-beijing.volces.com").strip().rstrip("/")
    model = os.environ.get("ARK_IMAGE_MODEL", "seedream-4.0")
    url = f"{base_url}/api/v3/images/generations"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    image_arr = []
    for ref in (references or []):
        r = _load_reference(ref)
        if "url" in r:
            image_arr.append({"url": r["url"]})
        else:
            image_arr.append({
                "url": f"data:{r['mime']};base64,{r['data']}"
            })

    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "response_format": "url",
    }
    if image_arr:
        payload["image"] = image_arr

    print(f"POST {url}  provider=seedream  model={model}  size=1024x1024  "
          f"refs={len(image_arr)}", file=sys.stderr)
    result = _post_json(url, payload, headers)
    data = result.get("data") or []
    if not data:
        _die(f"No image data in response: {result}")
    item = data[0]
    if item.get("url"):
        _download(item["url"], output_path)
    elif item.get("b64_json"):
        _save_b64(item["b64_json"], output_path)
    else:
        _die(f"Unrecognized response item: {item}")


# ── Provider dispatch ───────────────────────────────────────────────────

PROVIDERS = {
    "gpt-image": _generate_gpt_image,
    "nanobanana": _generate_nanobanana,
    "seedream": _generate_seedream,
}


def generate_grid(prompt, provider="gpt-image", references=None,
                  output_dir="./generated_gifs", output_path=None):
    """Generate a 3x3 grid image and save it locally. Returns the file path."""
    if provider not in PROVIDERS:
        _die(
            f"Unknown provider '{provider}'. Supported: {', '.join(PROVIDERS)}")

    wrapped = GRID_PROMPT_TEMPLATE.format(user_prompt=prompt)

    os.makedirs(output_dir, exist_ok=True)
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"grid_{timestamp}.png")

    PROVIDERS[provider](wrapped, references, output_path)
    return output_path


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate 3x3 animation grid image (multi-provider)")
    parser.add_argument("--prompt", required=True,
                        help="Animation description (subject + action + style)")
    parser.add_argument("--provider", default="gpt-image",
                        choices=list(PROVIDERS.keys()),
                        help="Image generation provider (default: gpt-image)")
    parser.add_argument("--references", nargs="+",
                        help="Reference images: file paths, http(s) URLs, or data URLs")
    parser.add_argument("--output-dir", default="./generated_gifs",
                        help="Output directory (default: ./generated_gifs)")
    parser.add_argument("--output-path",
                        help="Explicit output PNG path (overrides --output-dir)")
    args = parser.parse_args()

    grid_path = generate_grid(
        prompt=args.prompt,
        provider=args.provider,
        references=args.references,
        output_dir=args.output_dir,
        output_path=args.output_path,
    )

    print(f"Grid saved: {grid_path}", file=sys.stderr)
    print(json.dumps({"success": True, "grid_path": grid_path}))


if __name__ == "__main__":
    main()
