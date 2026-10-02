"""F8：AI 方案運作流程圖（兩個迴路、四個資料庫、五個 Dashboard），給簡報 P6 與 L7 文件用。

  python pipeline/make_flow_figure.py   → reports/figures/F8.png（1920×900）
不讀任何資料；內容依 L7運作流程_2026-09-30.md。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#2F5D8C"
INK = "#1A1A1A"
PROC = "#EAF1F8"
DB_FILL, DB_EDGE = "#F6EFE3", "#8A6D3B"
HUMAN_FILL, HUMAN_EDGE = "#F3C1BD", "#C0392B"
BAND_TOP, BAND_BOT = "#F7F9FC", "#FBF7F7"
GREY = "#8A8F98"


def layer_tag(ax, x, y, w, h, label):
    """標籤坐在方塊右上角外緣，標題左對齊，避免壓字。"""
    n = len(label)
    tw = 8.0 if n <= 2 else (12.2 if n <= 4 else 20.0)
    th = 3.6
    bx = x + w - tw
    by = y + h + 0.25
    ax.add_patch(FancyBboxPatch((bx, by), tw, th, boxstyle="round,pad=0,rounding_size=0.45",
                                fc=BLUE, ec=BLUE, lw=0, zorder=5))
    ax.text(bx + tw / 2, by + th / 2, label, ha="center", va="center", fontsize=12,
            color="white", fontweight="bold", zorder=6)


def box(ax, x, y, w, h, text, fill=PROC, edge=BLUE, size=13, bold_first=True, lw=1.4, ls="-", bold_lines=1, tag=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                fc=fill, ec=edge, lw=lw, ls=ls, zorder=3))
    lines = text.split("\n")
    if bold_first:
        title = "\n".join(lines[:bold_lines])
        rest = "\n".join(lines[bold_lines:])
        ax.text(x + 0.8, y + h - 4.4, title, ha="left", va="center", fontsize=size + 1, fontweight="bold",
                color=INK, zorder=4, linespacing=1.05)
        if rest:
            ax.text(x + w / 2, y + (h - 5.2) / 2, rest, ha="center", va="center", fontsize=size,
                    color="#3C4653", zorder=4, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, zorder=4,
                linespacing=1.25)
    if tag:
        layer_tag(ax, x, y, w, h, tag)


def arrow(ax, p, q, color=BLUE, lw=1.6, style="-|>", ms=14, path=None, zorder=2):
    if path is None:
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))
        return
    pts = [p] + path + [q]
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))


def main():
    fig, ax = plt.subplots(figsize=(12.4, 4.15), dpi=160)
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 78)
    ax.axis("off")
    fig.patch.set_facecolor("#F4F7FB")

    ax.add_patch(FancyBboxPatch((1, 43), 198, 34, boxstyle="round,pad=0,rounding_size=1.4", fc=BAND_TOP, ec="#D5DEE8", lw=1, zorder=1))
    ax.add_patch(FancyBboxPatch((1, 0.6), 198, 41, boxstyle="round,pad=0,rounding_size=1.4", fc=BAND_BOT, ec="#E4D4D4", lw=1, zorder=1))
    ax.text(3, 74.6, "產出 1：AI 網路輿情洞察系統架構與報告", fontsize=14, fontweight="bold", color=BLUE, va="center")
    ax.text(3, 38.4, "產出 2：針對目標 Persona（客群輪廓）的 AI 溝通計畫與系統流程", fontsize=14, fontweight="bold", color=HUMAN_EDGE, va="center")

    w, h, yt = 25, 14.5, 52.2
    xs = [3, 30.5, 58, 85.5, 113, 140.5, 168]
    # L2 沒有獨立的每日步驟方塊。L7 文件 §3：資料庫 B 存放去識別留言與標註結果。
    top = [
        ("論壇爬蟲", "每日新留言", PROC, BLUE, "L0"),
        ("去重・去識別", "遮蔽店名、人名", PROC, BLUE, "L1"),
        ("資料庫 B", "去識別與標註", DB_FILL, DB_EDGE, "L2"),
        ("流失判斷", "r4 機率、再派客群", PROC, BLUE, "L3·L4·L5"),
        ("洞察報告", "日週季報、預警", PROC, BLUE, None),
        ("資料庫 A", "報告池", DB_FILL, DB_EDGE, None),
        ("Dashboard", "戰情・報告・輿情", PROC, BLUE, None),
    ]
    for x, (head, body, f, e, tg) in zip(xs, top):
        box(ax, x, yt, w, h, head + "\n" + body, fill=f, edge=e, ls="--" if head.startswith("Dashboard") else "-", tag=tg)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + w, yt + h / 2), (b, yt + h / 2))

    # 下帶：6 個方塊 + 2 個資料庫
    yb = 17.2
    # 觸發對 L4、Persona 對 L5、RAG 對 L6、投遞與 KPI 對 L7（L7運作流程_2026-09-30.md）。人工審核沒有層號。
    bot = [
        ("觸發事件", "客訴或風險升高", PROC, BLUE, "L4"),
        ("判定 Persona", "四種客群輪廓", PROC, BLUE, "L5"),
        ("RAG 生成話術", "只引用知識庫", PROC, BLUE, "L6"),
        ("人工審核", "核准才投遞", HUMAN_FILL, HUMAN_EDGE, None),
        ("投遞", "LINE・電話", PROC, BLUE, "L7"),
        ("KPI 回饋", "寫回 CRM", PROC, BLUE, "L7"),
    ]
    for x, (head, body, f, e, tg) in zip(xs[:6], bot):
        box(ax, x, yb, w, h, head + "\n" + body, fill=f, edge=e, lw=2.2 if head == "人工審核" else 1.4, tag=tg)
    for a, b in zip(xs[:5], xs[1:6]):
        arrow(ax, (a + w, yb + h / 2), (b, yb + h / 2))
    # 回饋箭在 x=13.5 垂直上升，小字放箭頭右側、觸發方塊正下方。12pt 單行會伸進第二格下方，改兩行。
    box(ax, 58, 1.6, 25, 11.2, "資料庫 C\n知識庫 76 條", fill=DB_FILL, edge=DB_EDGE, size=13)
    arrow(ax, (70.5, 12.8), (70.5, yb), color=DB_EDGE)
    box(ax, 90, 1.6, 25, 11.2, "資料庫 D\n溝通佇列", fill=DB_FILL, edge=DB_EDGE, size=13)
    arrow(ax, (102.5, yb), (102.5, 12.8), color=DB_EDGE, style="<|-|>")

    arrow(ax, (98, yt), (15.5, yb + h), path=[(98, 48.6), (15.5, 48.6)], color=GREY, lw=1.4)
    ax.text(56, 49.2, "風險升為高 → 觸發", fontsize=12, color=GREY, ha="center", va="bottom")


    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "F8.png"
    fig.savefig(out, dpi=160, facecolor="#F4F7FB")
    plt.close(fig)
    from PIL import Image
    wpx, hpx = Image.open(out).size
    print(f"F8.png {wpx}×{hpx}")


if __name__ == "__main__":
    main()
