#!/usr/bin/env python3
"""
Generate a 3x3 grid image whose 9 cells are 9 consecutive frames of an action.

Wraps the user's prompt with a hard-constrained grid template, then calls the
shared generate_image() helper.

Env: OPENAI_API_KEY (required), OPENAI_BASE_URL (optional).
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from generate_image import generate_image, resolve_size  # noqa: E402


GRID_PROMPT_TEMPLATE = """Generate ONE single square image. The image content shows 9 consecutive frames of an animation arranged as a 3x3 mosaic (each frame occupies exactly 1/9 of the image area; frame side = image_side / 3).

ABSOLUTE LAYOUT RULES (must obey, do NOT violate):
1. EDGE-TO-EDGE tiling. Frames touch each other with ZERO gap, ZERO padding, ZERO border, ZERO white space, ZERO gutter, ZERO seam, ZERO dividing line, ZERO outline. The boundary between adjacent frames is implicit / mathematical (at exactly 1/3 and 2/3 positions of the image), NEVER drawn or visible.
2. NO frame numbers, NO labels, NO captions, NO watermarks, NO text of any kind anywhere.
3. All 9 frames share IDENTICAL camera angle, framing, scale, background color, lighting and art style — as if rendered from the same scene with only the subject's pose changing across frames.
4. NO element crosses a frame boundary; each pose stays fully inside its 1/9 region.
5. STRICT EQUAL CELLS. All 9 cells have the same width and the same height (cell_w = cell_h = image_side / 3 EXACTLY). The 3 columns are vertically aligned at x = 0, image_side/3, 2*image_side/3, image_side; the 3 rows are horizontally aligned at y = 0, image_side/3, 2*image_side/3, image_side. Do NOT make the center column or any single cell wider or narrower than the others.
6. SUBJECT CENTERED WITH SAFETY MARGIN. In every frame, the subject is placed at the geometric center of its own cell, with at least 15% padding between the subject's bounding box and EACH of the four cell edges. The subject never approaches a cell edge; the outer 15% of every cell is safe-margin background.

Frame order (left to right, top to bottom):
  frame1 frame2 frame3
  frame4 frame5 frame6
  frame7 frame8 frame9

Animation content:
{user_prompt}"""


def generate_grid(prompt, ratio="1:1", references=None,
                  output_dir="./generated_gifs", output_path=None,
                  no_download=False):
    size = resolve_size(ratio)
    wrapped = GRID_PROMPT_TEMPLATE.format(user_prompt=prompt)
    return generate_image(
        prompt=wrapped,
        ratio=ratio,
        references=references,
        output_dir=output_dir,
        output_path=output_path,
        file_prefix="grid",
        no_download=no_download,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3x3 animation grid image")
    parser.add_argument("--prompt", required=True,
                        help="Animation description")
    parser.add_argument("--ratio", default="1:1",
                        help="Aspect ratio (default 1:1)")
    parser.add_argument("--references", nargs="+",
                        help="Reference images: file paths, http(s) URLs, or data URLs")
    parser.add_argument(
        "--output-dir", default="./generated_gifs", help="Output directory")
    parser.add_argument("--output-path", help="Explicit output PNG path")
    parser.add_argument("--no-download", action="store_true",
                        help="Do not save the grid locally; return remote_url instead")
    args = parser.parse_args()

    size = resolve_size(args.ratio)
    w_h = size.lower().split("x")
    if len(w_h) == 2 and w_h[0] != w_h[1]:
        print(f"WARNING: non-square size {size}; the grid is meant to be square.",
              file=sys.stderr)

    result = generate_grid(
        prompt=args.prompt,
        ratio=args.ratio,
        references=args.references,
        output_dir=args.output_dir,
        output_path=args.output_path,
        no_download=args.no_download,
    )

    if args.no_download:
        out = {"success": True}
        if isinstance(result, dict) and result.get("url"):
            out["remote_url"] = result["url"]
        print(json.dumps(out))
    else:
        print(f"Grid saved: {result}", file=sys.stderr)
        print(json.dumps({"success": True, "grid_path": result}))


if __name__ == "__main__":
    main()
