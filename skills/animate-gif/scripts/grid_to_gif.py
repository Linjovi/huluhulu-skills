#!/usr/bin/env python3
"""
Slice a 3x3 grid PNG into 9 frames and combine them into an animated GIF.

Cells are cut by even thirds (w/3, h/3). Post-split alignment recenters each
frame's subject so animation does not jitter. White backgrounds use color
masking; all other backgrounds use border-proximity detection with reference-
frame gap fill.

Requires Pillow:
    pip install Pillow
"""

import argparse
import json
import os
import sys
from datetime import datetime
from statistics import median

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with:  pip install Pillow", file=sys.stderr)
    sys.exit(1)

WHITE = (255, 255, 255)


def _die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _corner_pixels(frame, patch=8):
    w, h = frame.size
    patch = min(patch, w, h)
    corners = [
        frame.crop((0, 0, patch, patch)),
        frame.crop((w - patch, 0, w, patch)),
        frame.crop((0, h - patch, patch, h)),
        frame.crop((w - patch, h - patch, w, h)),
    ]
    pixels = []
    for corner in corners:
        pixels.extend(corner.getdata())
    return pixels


def _color_distance(rgb, ref_rgb):
    return sum((a - b) ** 2 for a, b in zip(rgb, ref_rgb)) ** 0.5


def is_white_background(frame, tolerance=30):
    for r, g, b, a in _corner_pixels(frame):
        if a < 200:
            return False
        if _color_distance((r, g, b), WHITE) > tolerance:
            return False
    return True


def _is_foreground_border(px, x, y, w, h, strip, threshold):
    rgb = px[x, y][:3]
    dists = []
    for bx in range(strip):
        dists.append(_color_distance(rgb, px[bx, y][:3]))
        dists.append(_color_distance(rgb, px[w - 1 - bx, y][:3]))
    for by in range(strip):
        dists.append(_color_distance(rgb, px[x, by][:3]))
        dists.append(_color_distance(rgb, px[x, h - 1 - by][:3]))
    return min(dists) > threshold


def subject_bbox(frame, white_bg, color_threshold=35):
    px = frame.load()
    w, h = frame.size
    strip = max(4, min(w, h) // 16)

    if white_bg:
        def is_fg(x, y): return _color_distance(
            px[x, y][:3], WHITE) > color_threshold
    else:
        def is_fg(x, y): return _is_foreground_border(
            px, x, y, w, h, strip, color_threshold)

    min_x, min_y, max_x, max_y = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if is_fg(x, y):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x:
        return None
    return (min_x, min_y, max_x + 1, max_y + 1)


def _shift_frame(frame, dx, dy, white_bg, ref_frame=None):
    if dx == 0 and dy == 0:
        return frame

    w, h = frame.size
    if white_bg:
        canvas = Image.new("RGBA", (w, h), (*WHITE, 255))
        canvas.paste(frame, (dx, dy))
        return canvas

    base = (ref_frame or frame).copy()
    canvas = base.convert("RGBA")
    canvas.paste(frame, (dx, dy))
    return canvas


def align_frames(frames):
    white_bg = all(is_white_background(f) for f in frames)
    bboxes = [subject_bbox(f, white_bg=white_bg) for f in frames]
    anchors = []
    for bb in bboxes:
        if bb is None:
            continue
        left, top, right, bottom = bb
        anchors.append(((left + right) / 2, (top + bottom) / 2))
    if not anchors:
        return frames

    ref_ax = median(ax for ax, _ay in anchors)
    ref_ay = median(ay for _ax, ay in anchors)
    ref_frame = frames[next(
        i for i, bb in enumerate(bboxes) if bb is not None)]

    aligned = []
    for frame, bbox in zip(frames, bboxes):
        if bbox is None:
            aligned.append(frame)
            continue
        left, top, right, bottom = bbox
        ax = (left + right) / 2
        ay = (top + bottom) / 2
        dx = int(round(ref_ax - ax))
        dy = int(round(ref_ay - ay))
        aligned.append(_shift_frame(
            frame, dx, dy, white_bg, ref_frame=ref_frame))
    return aligned


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
            frames.append(
                img.crop((left, upper, left + cell_w, upper + cell_h)))
    return frames


def prepare_frames(grid_path, rows=3, cols=3):
    frames = split_grid(grid_path, rows=rows, cols=cols)
    return align_frames(frames)


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
    parser.add_argument("--grid", required=True,
                        help="Path to the 3x3 grid PNG")
    parser.add_argument(
        "--output-dir", default="./generated_gifs", help="Output directory")
    parser.add_argument(
        "--gif-path", help="Explicit output GIF path (overrides --output-dir)")
    parser.add_argument("--duration", type=int, default=120,
                        help="Frame duration in ms (default 120)")
    parser.add_argument("--frame-size", help="Resize each frame, e.g. 256x256")
    args = parser.parse_args()

    if not os.path.isfile(args.grid):
        _die(f"Grid file not found: {args.grid}")

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gif_path = args.gif_path or os.path.join(
        args.output_dir, f"animation_{timestamp}.gif")

    frame_size = None
    if args.frame_size:
        parts = args.frame_size.lower().split("x")
        if len(parts) != 2:
            _die(f"Invalid --frame-size: {args.frame_size}")
        frame_size = (int(parts[0]), int(parts[1]))

    frames = prepare_frames(args.grid)

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
