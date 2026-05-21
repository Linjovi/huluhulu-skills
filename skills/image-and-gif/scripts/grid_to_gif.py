#!/usr/bin/env python3
"""
Slice a 3x3 grid PNG into 9 frames and combine them into an animated GIF.

Cells are cut by even thirds (w/3, h/3). The upstream prompt template is
responsible for producing a gutter-free, edge-to-edge mosaic; if the model
still bleeds visible dividers, regenerate the grid rather than post-processing.

Requires Pillow:
    pip install Pillow
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with:  pip install Pillow", file=sys.stderr)
    sys.exit(1)


def _die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def split_grid(grid_path, rows=3, cols=3):
    img = Image.open(grid_path).convert("RGBA")
    w, h = img.size
    cell_w = w // cols
    cell_h = h // rows
    frames = []
    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            upper = r * cell_h
            frames.append(img.crop((left, upper, left + cell_w, upper + cell_h)))
    return frames


def create_gif(frames, gif_path, duration_ms=120, loop=0, frame_size=None,
               pingpong=False, transparent=False):
    if frame_size:
        frames = [f.resize(frame_size, Image.LANCZOS) for f in frames]

    if pingpong and len(frames) > 2:
        frames = list(frames) + list(reversed(frames[1:-1]))

    if transparent:
        prepared = [f.convert("RGBA") for f in frames]
        save_kwargs = dict(disposal=2, transparency=0)
    else:
        prepared = [f.convert("RGB") for f in frames]
        save_kwargs = {}

    prepared[0].save(
        gif_path,
        save_all=True,
        append_images=prepared[1:],
        format="GIF",
        duration=duration_ms,
        loop=loop,
        optimize=True,
        **save_kwargs,
    )


def main():
    parser = argparse.ArgumentParser(description="Slice 3x3 grid into GIF")
    parser.add_argument("--grid", required=True, help="Path to the 3x3 grid PNG")
    parser.add_argument("--output-dir", default="./generated_gifs", help="Output directory")
    parser.add_argument("--gif-path", help="Explicit output GIF path (overrides --output-dir)")
    parser.add_argument("--duration", type=int, default=120, help="Frame duration in ms (default 120)")
    parser.add_argument("--frame-size", help="Resize each frame, e.g. 256x256")
    args = parser.parse_args()

    if not os.path.isfile(args.grid):
        _die(f"Grid file not found: {args.grid}")

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gif_path = args.gif_path or os.path.join(args.output_dir, f"animation_{timestamp}.gif")

    frame_size = None
    if args.frame_size:
        parts = args.frame_size.lower().split("x")
        if len(parts) != 2:
            _die(f"Invalid --frame-size: {args.frame_size}")
        frame_size = (int(parts[0]), int(parts[1]))

    frames = split_grid(args.grid)

    create_gif(
        frames=frames,
        gif_path=gif_path,
        duration_ms=args.duration,
        loop=0,
        frame_size=frame_size,
        pingpong=False,
        transparent=False,
    )

    print(f"GIF saved: {gif_path}", file=sys.stderr)
    print(json.dumps({
        "success": True,
        "gif_path": gif_path,
    }))


if __name__ == "__main__":
    main()
