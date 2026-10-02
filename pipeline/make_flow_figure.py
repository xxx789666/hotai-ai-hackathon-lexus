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


def box(ax, x, y, w, h, text, fill=PROC, edge=BLUE, size=11, bold_first=True, lw=1.4, ls="-", bold_lines=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=fill, ec=edge, lw=lw, ls=ls, zorder=3))
    lines = text.split("\n")
    if bold_first:
        title = "\n".join(lines[:bold_lines])
        rest = "\n".join(lines[bold_lines:])
        if bold_lines == 1:
            ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center", fontsize=size + 0.5, fontweight="bold",
                    color=INK, zorder=4)
            if rest:
                ax.text(x + w / 2, y + (h - 3.2) / 2 - 0.4, rest, ha="center", va="center", fontsize=size - 1.2,
                        color="#3C4653", zorder=4, linespacing=1.35)
        else:
            # 標題兩行（中文括註後單行超出方塊）。其餘方塊仍走上面的單行路徑。
            ax.text(x + w / 2, y + h - 1.5, title, ha="center", va="top", fontsize=size + 0.5, fontweight="bold",
                    color=INK, zorder=4, linespacing=1.1)
            if rest:
                title_span = bold_lines * (size + 0.5) / 72 * 12 * 1.15
                body_center = y + (h - 1.5 - title_span) / 2
                ax.text(x + w / 2, body_center, rest, ha="center", va="center", fontsize=size - 1.2,
                        color="#3C4653", zorder=4, linespacing=1.35)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, zorder=4,
                linespacing=1.35)


def arrow(ax, p, q, color=BLUE, lw=1.6, style="-|>", ms=14, path=None, zorder=2):
    if path is None:
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))
        return
    pts = [p] + path + [q]
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))


def main():
    fig, ax = plt.subplots(figsize=(16, 7.5))
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim(0, 192)
    ax.set_ylim(-1, 89)
    ax.axis("off")

    # 兩個帶狀區
    ax.add_patch(FancyBboxPatch((1, 52), 190, 38, boxstyle="round,pad=0,rounding_size=2", fc=BAND_TOP, ec="#D5DEE8", lw=1, zorder=1))
    ax.add_patch(FancyBboxPatch((1, 0), 190, 49, boxstyle="round,pad=0,rounding_size=2", fc=BAND_BOT, ec="#E4D4D4", lw=1, zorder=1))
    ax.text(3, 85.5, "洞察迴路｜每日排程：新留言 → 標註與風險 → 日報 → Dashboard", fontsize=13, fontweight="bold", color=BLUE, va="center")
    ax.text(28, 45.5, "溝通迴路｜事件觸發：CRM 訊號・客訴結案 → Persona（客群輪廓） → RAG 話術 → 人工核准 → 投遞 → KPI 回饋", fontsize=13, fontweight="bold", color=HUMAN_EDGE, va="center")

    # 上帶：7 個方塊。下帶觸發方塊改三行後，上下方塊一起加高 2，避免字擠出框。
    w, h, yt = 23, 17, 58
    xs = [2, 29.5, 57, 84.5, 112, 139.5, 167]
    top = [
        ("論壇爬蟲", "每日抓新留言\n三站公開論壇", PROC, BLUE),
        ("去重・去識別", "作者雜湊、店名\n人名遮蔽（L1）", PROC, BLUE),
        ("資料庫 B", "原始輿情\n去識別版，可溯源", DB_FILL, DB_EDGE),
        ("流失判斷 L3–L5", "r4 逐句判流失、面向\n→ 風險分數 →\nPersona（客群輪廓）", PROC, BLUE),
        ("洞察報告", "日報・週報・季報\n趨勢分析、200% 預警", PROC, BLUE),
        ("資料庫 A", "報告池\n日／週／季報、預警紀錄", DB_FILL, DB_EDGE),
        ("Dashboard 1–3", "1 戰情總覽\n2 報告池・3 原始輿情", PROC, BLUE),
    ]
    for x, (head, body, f, e) in zip(xs, top):
        box(ax, x, yt, w, h, head + "\n" + body, fill=f, edge=e, ls="--" if head.startswith("Dashboard") else "-")
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + w, yt + h / 2), (b, yt + h / 2))

    # 下帶：6 個方塊 + 2 個資料庫
    yb = 22
    bot = [
        ("觸發事件", "CRM 命中 R1–R8（含 R5 待料）\n客訴結案 → 第 7 天回訪\n或風險分數升為高", PROC, BLUE),
        ("判定 Persona\n（客群輪廓）", "四類之一\n未分類 → 觀察名單", PROC, BLUE),
        ("RAG 生成話術", "檢索條款 → 生成\n→ 第二輪事實查核", PROC, BLUE),
        ("人工審核", "Dashboard 5 審核佇列\n核准或改寫才投遞", HUMAN_FILL, HUMAN_EDGE),
        ("投遞", "LINE・App\nEmail・專員電話", PROC, BLUE),
        ("KPI 回饋", "點擊・預約・回廠\n寫回 CRM", PROC, BLUE),
    ]
    for x, (head, body, f, e) in zip(xs[:6], bot):
        box(ax, x, yb, w, h, head + "\n" + body, fill=f, edge=e, lw=2.2 if head == "人工審核" else 1.4,
            size=10 if head == "觸發事件" else 11,
            bold_lines=2 if head.startswith("判定 Persona") else 1)
    for a, b in zip(xs[:5], xs[1:6]):
        arrow(ax, (a + w, yb + h / 2), (b, yb + h / 2))
    # 回饋箭在 x=13.5 垂直上升，小字放箭頭右側、觸發方塊正下方。12pt 單行會伸進第二格下方，改兩行。
    ax.text(16.2, 18.6, "客訴回訪不計頻率上限；\n觀察名單車主也回訪", fontsize=12, color=GREY,
            ha="left", va="center", zorder=4, linespacing=1.25)

    # 資料庫 C、D 與 Dashboard 4
    box(ax, 57, 3, 23, 13, "資料庫 C\n知識庫 76 條・保固條款\nDashboard 4 可查閱", fill=DB_FILL, edge=DB_EDGE)
    arrow(ax, (68.5, 16), (68.5, yb), color=DB_EDGE)
    box(ax, 92, 3, 23, 13, "資料庫 D\n溝通佇列：草稿、審核\n狀態、投遞結果", fill=DB_FILL, edge=DB_EDGE)
    arrow(ax, (100, yb), (100, 16), color=DB_EDGE, style="<|-|>")

    # 上帶 → 下帶：風險分數升高也會觸發
    arrow(ax, (96, yt), (13.5, yb + h), path=[(96, 50.5), (13.5, 50.5)], color=GREY, lw=1.4)
    ax.text(55, 51.8, "風險升為高 → 觸發", fontsize=11, color=GREY, ha="center", va="bottom")

    # KPI 回饋 → 校正門檻與模型
    arrow(ax, (151, yb), (13.5, yb), path=[(151, 1.2), (13.5, 1.2)], color=HUMAN_EDGE, lw=1.4, style="-|>")
    ax.text(140, 3.0, "回頭校正觸發門檻，\n再訓練 r4", fontsize=11, color=HUMAN_EDGE, ha="center", va="bottom", linespacing=1.3)

    # 右下註記
    ax.text(166, 37, "資料庫與模型都在\n和泰內網，不出門；\n論壇文字只作研究語料，\n上線後輸入改為\n工單與客訴文字。", fontsize=10, color="#3C4653", va="top", linespacing=1.4)

    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "F8.png"
    fig.savefig(out, dpi=120, facecolor="white")
    plt.close(fig)
    from PIL import Image
    wpx, hpx = Image.open(out).size
    print(f"F8.png {wpx}×{hpx}")


if __name__ == "__main__":
    main()
