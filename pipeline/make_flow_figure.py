"""F8：AI 方案運作流程圖（兩個迴路、四個資料庫、五個 Dashboard），給簡報 P6 與 L7 文件用。

  python pipeline/make_flow_figure.py   → reports/figures/F8.png
不讀任何資料。方塊文字對齊 v2.6（f5f2a1b）；L0–L7 與兩個產出標示是後來加上的。
畫布配合簡報第 9 頁圖區高度，用斷行容納全文，不靠刪字。
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
GREY = "#5C6570"

# 寬度對齊簡報內容區。高度對齊第 9 頁圖區，12pt 投影才不會被縮小。
FIG_W, FIG_H = 12.42, 4.74

# v2.6 圖上必須還在的句子。產出標題與 L# 是額外標示，不取代這些句子。
REQUIRED = [
    "每日排程：新留言 → 標註與風險 → 日報 → Dashboard",
    "事件觸發：CRM 訊號・客訴結案 → Persona（客群輪廓）→ RAG 話術 → 人工核准 → 投遞 → KPI 回饋",
    "每日抓新留言",
    "三站公開論壇",
    "作者雜湊、店名",
    "人名遮蔽（L1）",
    "原始輿情",
    "去識別版，可溯源",
    "r4 逐句判流失、面向",
    "風險分數",
    "Persona（客群輪廓）",
    "日報・週報・季報",
    "趨勢分析、200% 預警",
    "日／週／季報、預警紀錄",
    "1 戰情總覽",
    "2 報告池・3 原始輿情",
    "CRM 命中 R1–R8（含 R5 待料）",
    "客訴結案 → 第 7 天回訪",
    "或風險分數升為高",
    "四類之一",
    "未分類 → 觀察名單",
    "檢索條款 → 生成",
    "第二輪事實查核",
    "Dashboard 5 審核佇列",
    "核准或改寫才投遞",
    "LINE・App",
    "Email・專員電話",
    "點擊・預約・回廠",
    "寫回 CRM",
    "客訴回訪不計頻率上限",
    "觀察名單車主也回訪",
    "知識庫 76 條・保固條款",
    "Dashboard 4 可查閱",
    "溝通佇列：草稿、審核",
    "狀態、投遞結果",
    "風險升為高 → 觸發",
    "回頭校正觸發門檻",
    "再訓練 r4",
    "資料庫與模型都在",
    "和泰內網，不出門",
    "論壇文字只作研究語料",
    "上線後輸入改為",
    "工單與客訴文字",
]

DRAWN = []
OWNED = []  # (artist, x0, y0, x1, y1) 方塊內文字必須落在方塊內
FREE = []  # 不在方塊裡、也不得壓到方塊的文字


def layer_tag(ax, x, y, w, h, label):
    """標籤貼在方塊右上角內緣，標題留在左側。"""
    tw = 0.36 if len(label) <= 2 else (0.58 if len(label) <= 4 else 0.88)
    th = 0.20
    bx = x + w - tw - 0.04
    by = y + h - th - 0.04
    ax.add_patch(FancyBboxPatch((bx, by), tw, th, boxstyle="round,pad=0,rounding_size=0.04",
                                fc=BLUE, ec=BLUE, lw=0, zorder=6))
    artist = ax.text(bx + tw / 2, by + th / 2, label, ha="center", va="center", fontsize=8,
                     color="white", fontweight="bold", zorder=7)
    OWNED.append((artist, bx, by, bx + tw, by + th))


def box(ax, x, y, w, h, text, fill=PROC, edge=BLUE, size=12, lw=1.2, ls="-", tag=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=fill, ec=edge, lw=lw, ls=ls, zorder=3))
    DRAWN.append(text)
    lines = text.split("\n")
    # 有標籤時標題讓出右上角，但仍從方塊頂緣起排，不為標籤多空一列。
    top = y + h - 0.06
    step = (size / 72) * 1.12
    for i, line in enumerate(lines):
        yy = top - i * step
        if i == 0:
            artist = ax.text(x + 0.06, yy, line, ha="left", va="top", fontsize=size, fontweight="bold",
                             color=INK, zorder=4)
        else:
            artist = ax.text(x + w / 2, yy, line, ha="center", va="top", fontsize=size,
                             color="#3C4653", zorder=4)
        OWNED.append((artist, x + 0.04, y + 0.03, x + w - 0.04, y + h - 0.02))
    if tag:
        layer_tag(ax, x, y, w, h, tag)


def arrow(ax, p, q, color=BLUE, lw=1.3, style="-|>", ms=11, path=None, zorder=2):
    if path is None:
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))
        return
    pts = [p] + path + [q]
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, zorder=zorder, solid_capstyle="round")
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=zorder))


def note(ax, x, y, s, size=12, color=GREY, ha="left", va="top", **kw):
    DRAWN.append(s)
    artist = ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, zorder=4, **kw)
    FREE.append(artist)
    return artist


def data_bbox(artist, renderer, ax):
    bb = artist.get_window_extent(renderer)
    inv = ax.transData.inverted()
    (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def overlaps(a, b, pad=0.0):
    return a[0] < b[2] - pad and a[2] > b[0] + pad and a[1] < b[3] - pad and a[3] > b[1] + pad


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=160)
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)
    ax.axis("off")
    fig.patch.set_facecolor("#F4F7FB")

    # 上帶包住產出 1 與七個方塊；下帶包住產出 2 與溝通迴路。兩帶之間留空給回流標籤。
    ax.add_patch(FancyBboxPatch((0.05, 3.10), 12.32, 1.56, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=BAND_TOP, ec="#D5DEE8", lw=0.6, zorder=1))
    ax.add_patch(FancyBboxPatch((0.05, 0.04), 12.32, 2.78, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=BAND_BOT, ec="#E4D4D4", lw=0.6, zorder=1))

    note(ax, 0.14, 4.58, "產出 1：AI 網路輿情洞察系統架構與報告",
         size=12, color=BLUE, va="center", fontweight="bold")
    note(ax, 0.14, 4.36, "洞察迴路｜每日排程：新留言 → 標註與風險 → 日報 → Dashboard",
         size=11, color=BLUE, va="center")

    gap = 0.06
    w = (12.22 - 6 * gap) / 7
    xs = [0.10 + i * (w + gap) for i in range(7)]
    yt, ht = 3.18, 1.02
    top = [
        ("論壇爬蟲", "每日抓新留言\n三站公開論壇", PROC, BLUE, "L0"),
        ("去重・去識別", "作者雜湊、店名\n人名遮蔽（L1）", PROC, BLUE, "L1"),
        ("資料庫 B", "原始輿情\n去識別版，可溯源", DB_FILL, DB_EDGE, "L2"),
        ("流失判斷", "r4 逐句判流失、面向\n→ 風險分數 →\nPersona（客群輪廓）", PROC, BLUE, "L3·L4·L5"),
        ("洞察報告", "日報・週報・季報\n趨勢分析、200% 預警", PROC, BLUE, None),
        ("資料庫 A", "報告池\n日／週／季報、\n預警紀錄", DB_FILL, DB_EDGE, None),
        ("Dashboard 1–3", "1 戰情總覽\n2 報告池・\n3 原始輿情", PROC, BLUE, None),
    ]
    for x, (head, body, f, e, tg) in zip(xs, top):
        box(ax, x, yt, w, ht, head + "\n" + body, fill=f, edge=e,
            ls="--" if head.startswith("Dashboard") else "-", tag=tg, size=12)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + w, yt + ht * 0.42), (b, yt + ht * 0.42))

    note(ax, 0.28, 2.70, "產出 2：針對目標 Persona（客群輪廓）的 AI 溝通計畫與系統流程",
         size=12, color=HUMAN_EDGE, va="center", fontweight="bold")
    note(ax, 0.28, 2.50, "溝通迴路｜事件觸發：CRM 訊號・客訴結案 → Persona（客群輪廓）→ RAG 話術 → 人工核准 → 投遞 → KPI 回饋",
         size=10.5, color=HUMAN_EDGE, va="center")

    yb, hb = 1.08, 1.22
    bot = [
        ("觸發事件", "CRM 命中 R1–R8\n（含 R5 待料）\n客訴結案 → \n第 7 天回訪\n或風險分數升為高", PROC, BLUE, "L4"),
        ("判定 Persona", "（客群輪廓）\n四類之一\n未分類 → 觀察名單", PROC, BLUE, "L5"),
        ("RAG 生成話術", "檢索條款 → 生成\n→ 第二輪事實查核", PROC, BLUE, "L6"),
        ("人工審核", "Dashboard 5 \n審核佇列\n核准或改寫才投遞", HUMAN_FILL, HUMAN_EDGE, None),
        ("投遞", "LINE・App\nEmail・專員電話", PROC, BLUE, "L7"),
        ("KPI 回饋", "點擊・預約・回廠\n寫回 CRM", PROC, BLUE, "L7"),
    ]
    for x, (head, body, f, e, tg) in zip(xs[:6], bot):
        box(ax, x, yb, w, hb, head + "\n" + body, fill=f, edge=e,
            lw=1.8 if head == "人工審核" else 1.2, tag=tg, size=12)
    for a, b in zip(xs[:5], xs[1:6]):
        arrow(ax, (a + w, yb + 0.36), (b, yb + 0.36))

    note(ax, xs[0] + 0.04, 0.96, "客訴回訪不計頻率上限；\n觀察名單車主也回訪", size=11, color=GREY, va="top", linespacing=1.15)

    box(ax, xs[2], 0.14, w, 0.82, "資料庫 C\n知識庫 76 條・\n保固條款\nDashboard 4 可查閱",
        fill=DB_FILL, edge=DB_EDGE, size=12)
    arrow(ax, (xs[2] + w / 2, 0.96), (xs[2] + w / 2, yb), color=DB_EDGE)
    box(ax, xs[3], 0.14, w, 0.82, "資料庫 D\n溝通佇列：\n草稿、審核\n狀態、投遞結果",
        fill=DB_FILL, edge=DB_EDGE, size=12)
    arrow(ax, (xs[3] + w / 2, yb), (xs[3] + w / 2, 0.96), color=DB_EDGE, style="<|-|>")

    # 橫線在兩帶空檔。直向箭頭貼左緣下來，不穿過產出 2 與溝通迴路標題。
    arrow(ax, (xs[3] + w / 2, yt), (xs[0] + 0.04, yb + hb),
          path=[(xs[3] + w / 2, 2.96), (0.08, 2.96)], color=GREY, lw=1.15)
    risk = note(ax, (xs[1] + xs[2] + w) / 2, 3.02, "風險升為高 → 觸發",
                size=11, color=GREY, ha="center", va="bottom",
                bbox=dict(fc="#F4F7FB", ec="none", pad=0.15))

    arrow(ax, (xs[5] + w * 0.72, yb), (xs[0] + 0.08, 0.06),
          path=[(xs[5] + w * 0.72, 0.06)], color=HUMAN_EDGE, lw=1.15)
    note(ax, xs[4] + 0.02, 0.55, "回頭校正觸發門檻，\n再訓練 r4",
         size=11, color=HUMAN_EDGE, ha="left", va="center", linespacing=1.1)

    note(ax, xs[6] + 0.02, 2.28, "資料庫與模型都在\n和泰內網，不出門；\n論壇文字只作\n研究語料，\n上線後輸入改為\n工單與客訴文字。",
         size=11, color="#3C4653", va="top", linespacing=1.15)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    problems = []
    patches = [p for p in ax.patches if isinstance(p, FancyBboxPatch)]
    patch_boxes = []
    for p in patches:
        bb = data_bbox(p, renderer, ax)
        # 色帶很大，只拿方塊（寬度小於 3 吋）做壓線檢查。
        if bb[2] - bb[0] < 3:
            patch_boxes.append(bb)
    for artist, x0, y0, x1, y1 in OWNED:
        bb = data_bbox(artist, renderer, ax)
        if bb[0] < x0 - 0.02 or bb[2] > x1 + 0.02 or bb[1] < y0 - 0.02 or bb[3] > y1 + 0.02:
            problems.append(f"出框 {artist.get_text()!r} {tuple(round(v, 2) for v in bb)}")
    for artist in FREE:
        bb = data_bbox(artist, renderer, ax)
        if bb[0] < -0.02 or bb[2] > FIG_W + 0.02 or bb[1] < -0.02 or bb[3] > FIG_H + 0.02:
            problems.append(f"出圖 {artist.get_text()!r} {tuple(round(v, 2) for v in bb)}")
        if artist is risk:
            for pb in patch_boxes:
                if overlaps(bb, pb, pad=0.01):
                    problems.append(f"風險標籤壓到方塊 {tuple(round(v, 2) for v in pb)}")
    blob = "".join(DRAWN).replace("\n", "")
    missing = [s for s in REQUIRED if s not in blob]
    if missing:
        problems.append("缺字：" + "、".join(missing))
    if problems:
        plt.close(fig)
        raise SystemExit("F8 檢查失敗：\n" + "\n".join(problems))

    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "F8.png"
    fig.savefig(out, dpi=160, facecolor="#F4F7FB")
    plt.close(fig)
    from PIL import Image
    im = Image.open(out)
    print(f"F8.png {im.size[0]}×{im.size[1]}")
    print(f"v2.6 文字清單 {len(REQUIRED)} 條都在繪圖字串裡，方塊內文字未出框")


if __name__ == "__main__":
    main()
