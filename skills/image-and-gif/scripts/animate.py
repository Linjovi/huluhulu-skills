#!/usr/bin/env python3
"""
End-to-end animated GIF generator.

Pipeline:
  1) Call /v1/images/generations to produce a 3x3 grid PNG.
  2) Slice the grid into 9 frames and assemble them into an animated GIF.

Fixed settings: model=gpt-image-2, loop=0, no pingpong, no transparency.

Env vars:
  OPENAI_API_KEY   (required)
  OPENAI_BASE_URL  (optional)

Dependencies: Pillow (`pip install Pillow`).
"""

import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from generate_grid import generate_grid  # noqa: E402
from grid_to_gif import create_gif, prepare_frames  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Generate an animated GIF via a 3x3 grid")
    parser.add_argument("--prompt", required=True,
                        help="Animation description")
    parser.add_argument("--ratio", default="1:1",
                        help="Aspect ratio (default 1:1)")
    parser.add_argument("--references", nargs="+",
                        help="Reference images: file paths, http(s) URLs, or data URLs")
    parser.add_argument(
        "--output-dir", default="./generated_gifs", help="Output directory")
    parser.add_argument("--duration", type=int, default=120,
                        help="Frame duration in ms (default 120)")
    parser.add_argument("--frame-size", help="Resize each frame, e.g. 256x256")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    grid_path = generate_grid(
        prompt=args.prompt,
        ratio=args.ratio,
        references=args.references,
        output_dir=args.output_dir,
        output_path=os.path.join(args.output_dir, f"grid_{timestamp}.png"),
    )
    print(f"Grid saved: {grid_path}", file=sys.stderr)

    frames = prepare_frames(grid_path)

    frame_size = None
    if args.frame_size:
        parts = args.frame_size.lower().split("x")
        if len(parts) != 2:
            print(f"Invalid --frame-size: {args.frame_size}", file=sys.stderr)
            sys.exit(1)
        frame_size = (int(parts[0]), int(parts[1]))

    gif_path = os.path.join(args.output_dir, f"animation_{timestamp}.gif")
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
        "grid_path": grid_path,
        "gif_path": gif_path,
    }))


if __name__ == "__main__":
    main()
