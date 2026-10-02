"""檢查簡報形狀是否交疊，或超出頁面、壓到頁尾來源列。

  python deck/check_layout.py deck/初賽簡報_v2.9.pptx

包含關係（文字框在卡片裡、小標在大方塊裡）不算重疊。
若同版預覽圖存在，另外印出每張的 PIL 空白比例：
內容區（約 1.05 吋到 7.05 吋）裡 R、G、B 都 ≥ 250 的像素占比。
淺底色卡片不算白。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

EMU = 914400
OVERLAP_IN = 0.04
CONTAIN_TOL = 0.03
FOOTER_Y = 7.16
SLIDE_PAD = 0.02


def inches(value) -> float:
    return float(value) / EMU


def shape_text(shape) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return " ".join(p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip())


def walk(shapes):
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(shape.shapes)
            continue
        yield shape


def box_of(shape):
    return (
        inches(shape.left),
        inches(shape.top),
        inches(shape.left) + inches(shape.width),
        inches(shape.top) + inches(shape.height),
    )


def contains(outer, inner, tol=CONTAIN_TOL) -> bool:
    return (
        outer[0] <= inner[0] + tol
        and outer[1] <= inner[1] + tol
        and outer[2] >= inner[2] - tol
        and outer[3] >= inner[3] - tol
    )


def intersection(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0), max(0.0, y1 - y0)


def label(shape, text) -> str:
    snippet = text.replace("\n", " ")[:28]
    kind = str(shape.shape_type).split(".")[-1]
    return f"{kind}:{snippet}" if snippet else kind


def check_slide(slide, index: int, slide_w: float, slide_h: float):
    items = []
    for shape in walk(slide.shapes):
        try:
            rect = box_of(shape)
        except (TypeError, AttributeError):
            continue
        items.append((shape, rect, shape_text(shape)))
    overlaps = []
    for i, (sa, ra, ta) in enumerate(items):
        for sb, rb, tb in items[i + 1 :]:
            iw, ih = intersection(ra, rb)
            if iw <= OVERLAP_IN or ih <= OVERLAP_IN:
                continue
            if contains(ra, rb) or contains(rb, ra):
                continue
            overlaps.append((label(sa, ta), label(sb, tb), iw, ih))
    outside = []
    for shape, rect, text in items:
        x0, y0, x1, y1 = rect
        reasons = []
        if x0 < -SLIDE_PAD or y0 < -SLIDE_PAD or x1 > slide_w + SLIDE_PAD or y1 > slide_h + SLIDE_PAD:
            reasons.append("超出頁面")
        # 頁尾來源列與頁碼本身從 FOOTER_Y 起算，不當作壓線。
        if y0 < FOOTER_Y - 0.02 and y1 > FOOTER_Y + 0.02:
            reasons.append("壓到頁尾來源列")
        if reasons:
            outside.append((label(shape, text), ",".join(reasons), rect))
    return overlaps, outside


def whitespace(png: Path, slide_w: float, slide_h: float) -> float:
    im = Image.open(png).convert("RGB")
    px_per_in = im.width / slide_w
    x0 = int(0.30 * px_per_in)
    x1 = int((slide_w - 0.30) * px_per_in)
    y0 = int(1.05 * px_per_in)
    y1 = int(min(7.05, slide_h) * px_per_in)
    crop = im.crop((x0, y0, x1, y1))
    white = 0
    total = crop.width * crop.height
    pixels = list(crop.get_flattened_data()) if hasattr(crop, "get_flattened_data") else list(crop.getdata())
    for r, g, b in pixels:
        if r >= 250 and g >= 250 and b >= 250:
            white += 1
    return 100.0 * white / total if total else 0.0


def preview_dir(pptx: Path) -> Path | None:
    name = pptx.stem
    marker = "_v"
    if marker not in name:
        return None
    version = name.rsplit(marker, 1)[1]
    folder = pptx.parent / "preview" / f"v{version}"
    return folder if folder.is_dir() else None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("用法：python deck/check_layout.py deck/初賽簡報_vX.Y.pptx")
        return 2
    path = Path(sys.argv[1])
    prs = Presentation(str(path))
    slide_w = inches(prs.slide_width)
    slide_h = inches(prs.slide_height)
    overlap_n = 0
    outside_n = 0
    for i, slide in enumerate(prs.slides, start=1):
        overlaps, outside = check_slide(slide, i, slide_w, slide_h)
        overlap_n += len(overlaps)
        outside_n += len(outside)
        if not overlaps and not outside:
            continue
        print(f"第 {i} 頁")
        for a, b, iw, ih in overlaps:
            print(f"  重疊 {iw:.2f}x{ih:.2f} 吋  {a}  /  {b}")
        for name, reason, rect in outside:
            print(f"  {reason}  {name}  ({rect[0]:.2f},{rect[1]:.2f})-({rect[2]:.2f},{rect[3]:.2f})")
    print(f"重疊 {overlap_n} 處，超出或壓線 {outside_n} 處，共 {len(prs.slides)} 頁")
    folder = preview_dir(path)
    if folder is None:
        print("找不到預覽圖，略過 PIL 空白")
        return 0
    print("PIL 空白（內容區 RGB≥250）")
    for png in sorted(folder.glob("slide-*.png")):
        ratio = whitespace(png, slide_w, slide_h)
        print(f"  {png.name}  {ratio:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
