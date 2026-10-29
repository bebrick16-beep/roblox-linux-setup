#!/usr/bin/env python3
"""Build the RobloxLegacy Xcursor theme.

The theme is generated locally from:
  * the public "Roblox Legacy Cursors 2006-2013" preview pack (black arrow), and
  * cursor textures that already ship inside the user's own Mocktail payload.

No Roblox or third-party cursor artwork is stored in this repository.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("python-pillow is required: sudo pacman -S python-pillow")

THEME = "RobloxLegacy"
SIZES = (24, 32, 48, 64)
PACK_URL = (
    "https://cdn.custom-cursor.com/packs/13002/"
    "roblox-legacy-cursors-2006-2013-pack.png"
)

HOME = Path.home()
FLATPAK_ID = "space.bigrat.mocktail"
SANDBOX_ICONS = HOME / f".var/app/{FLATPAK_ID}/data/icons"
HOST_ICONS = HOME / ".local/share/icons"
PAYLOADS = HOME / f".var/app/{FLATPAK_ID}/data/mocktail/payloads"

# alias -> real cursor file
ALIASES = {
    "9": "hand2",
    "hand": "hand2",
    "hand1": "hand2",
    "pointer": "hand2",
    "pointing_hand": "hand2",
    "ibeam": "xterm",
    "text": "xterm",
    "vertical-text": "xterm",
    "cross": "crosshair",
    "cross_reverse": "crosshair",
    "diamond_cross": "crosshair",
    "tcross": "crosshair",
}

ALL_NAMES = """
alias all-scroll arrow cell circle closedhand col-resize context-menu copy
cross cross_reverse default diamond_cross draft e-resize ew-resize fleur
forbidden grabbing grab hand1 hand help ibeam move ne-resize nesw-resize
no-drop not-allowed n-resize ns-resize nw-resize nwse-resize openhand pencil
plus pointer pointing_hand progress right_ptr row-resize sb_down_arrow
sb_h_double_arrow sb_left_arrow sb_right_arrow sb_up_arrow sb_v_double_arrow
se-resize size_bdiag size_fdiag size_hor size_ver s-resize sw-resize tcross
text top_left_arrow vertical-text wait watch whats_this w-resize zoom-in
zoom-out
""".split()


def find_textures() -> Path | None:
    if not PAYLOADS.is_dir():
        return None
    candidates = []
    for payload in PAYLOADS.iterdir():
        tex = payload / "assets/content/textures"
        if (tex / "Cursors/KeyboardMouse/ArrowCursor.png").is_file():
            candidates.append(tex)
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def trim(im: Image.Image) -> Image.Image:
    box = im.getbbox()
    return im.crop(box) if box else im


def remove_shadow(im: Image.Image) -> Image.Image:
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 40 or (a < 200 and r < 40 and g < 40 and b < 40):
                px[x, y] = (0, 0, 0, 0)
    return im


def top_tip(im: Image.Image) -> tuple[int, int]:
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] > 128:
                return x, y
    return 0, 0


def download(url: str) -> bytes:
    # custom-cursor.com's CDN returns 403 for browser-like UAs, but allows curl's.
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.8.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except Exception:
        import subprocess

        return subprocess.check_output(["curl", "-fsSL", url], timeout=120)


def load_legacy(pack: str) -> Image.Image:
    if pack.startswith(("http://", "https://")):
        tmp = Path(tempfile.mkstemp(suffix=".png")[1])
        tmp.write_bytes(download(pack))
        path = tmp
    else:
        path = Path(pack)
    im = Image.open(path).convert("RGBA")
    im = im.crop((0, 0, im.width // 2, im.height))
    return trim(remove_shadow(im))


def render(src: Image.Image, size: int, hot: tuple[int, int]) -> tuple[Image.Image, tuple[int, int]]:
    sw, sh = src.size
    scale = min(size / sw, size / sh)
    nw, nh = max(1, round(sw * scale)), max(1, round(sh * scale))
    resized = src.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox, oy = (size - nw) // 2, (size - nh) // 2
    canvas.alpha_composite(resized, (ox, oy))
    hx = min(size - 1, max(0, round(ox + hot[0] * scale)))
    hy = min(size - 1, max(0, round(oy + hot[1] * scale)))
    return canvas, (hx, hy)


def xcursor_chunk(size: int, im: Image.Image, hot: tuple[int, int]) -> bytes:
    out = bytearray()
    for r, g, b, a in im.getdata():
        out += struct.pack(
            "<I", (a << 24) | ((r * a // 255) << 16) | ((g * a // 255) << 8) | (b * a // 255)
        )
    header = struct.pack(
        "<IIIIIIIII", 36, 0xFFFD0002, size, 1, im.width, im.height, hot[0], hot[1], 0
    )
    return header + bytes(out)


def write_xcursor(path: Path, images: list[tuple[int, Image.Image, tuple[int, int]]]) -> None:
    chunks = [(size, xcursor_chunk(size, im, hot)) for size, im, hot in images]
    pos = 16 + len(chunks) * 12
    toc, body = bytearray(), bytearray()
    for size, chunk in chunks:
        toc += struct.pack("<III", 0xFFFD0002, size, pos)
        body += chunk
        pos += len(chunk)
    data = struct.pack("<IIII", 0x72756358, 16, 0x00010000, len(chunks)) + toc + body
    path.write_bytes(data)


def build_theme(tex: Path, pack: str, out_dir: Path) -> None:
    legacy = load_legacy(pack)
    hand = trim(Image.open(tex / "Cursors/KeyboardMouse/ArrowCursor.png").convert("RGBA"))
    beam = trim(Image.open(tex / "Cursors/KeyboardMouse/IBeamCursor.png").convert("RGBA"))
    reticle = trim(Image.open(tex / "MouseLockedCursor.png").convert("RGBA"))

    sources = {
        "left_ptr": (legacy, (0, 0)),
        "hand2": (hand, top_tip(hand)),
        "xterm": (beam, (beam.width // 2, beam.height // 2)),
        "crosshair": (reticle, (reticle.width // 2, reticle.height // 2)),
    }

    cursors = out_dir / "cursors"
    cursors.mkdir(parents=True, exist_ok=True)
    for name, (src, hot) in sources.items():
        images = [(s, *render(src, s, hot)) for s in SIZES]
        write_xcursor(cursors / name, images)

    for alias in ALL_NAMES:
        link = cursors / alias
        if link.is_symlink() or link.exists():
            link.unlink()
        os.symlink(ALIASES.get(alias, "left_ptr"), link)

    (out_dir / "index.theme").write_text(
        f"[Icon Theme]\nName={THEME}\nComment=Roblox legacy cursor (black arrow)\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=PACK_URL, help="PNG pack path or URL")
    ap.add_argument("--textures", type=Path, help="override Mocktail textures dir")
    args = ap.parse_args()

    tex = args.textures or find_textures()
    if tex is None:
        sys.exit(
            "Mocktail cursor textures not found.\n"
            "Run `roblox` once (it downloads the game payload), then rerun this script."
        )

    build_theme(tex, args.pack, HOST_ICONS / THEME)
    print(f"installed {HOST_ICONS / THEME}")

    if SANDBOX_ICONS.is_dir():
        build_theme(tex, args.pack, SANDBOX_ICONS / THEME)
        print(f"installed {SANDBOX_ICONS / THEME}")

    print(f"done: Xcursor theme '{THEME}' ({', '.join(map(str, SIZES))} px)")


if __name__ == "__main__":
    main()
