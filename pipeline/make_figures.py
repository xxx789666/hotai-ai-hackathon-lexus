"""T10 圖表初稿。中文用 Microsoft JhengHei，白底，1600×900 以上。

  python pipeline/make_figures.py
  另：f_pipeline() 寫 reports/figures/F9_pipeline.png（不在 main 裡，避免連動重畫）。

F1、F2 的分子分母沿用 reports/T7_stats_tests.md，誤差線為依該表重算的 Wilson 95% CI。
F6 用 r4 ep2 的 600 句測試集（jev_lora_r4_ep2_pilot.jsonl）。
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"

BLUE = "#2F5D8C"
BLUE_MID = "#5C84B0"
BLUE_LIGHT = "#A9C3DC"
RED = "#C0392B"
RED_MID = "#E07A72"
RED_LIGHT = "#F3C1BD"
INK = "#1A1A1A"
GRID = "#E6E6E6"
PAPER = "#F4F7FB"

# T7 §3 面向 × 流失（有此面向且流失 / 有此面向 n）
ASPECT_TABLE = [
    ("價格", 587, 3908),
    ("技術品質", 287, 3225),
    ("保固延保", 109, 1521),
    ("銷售交車", 19, 1367),
    ("態度", 62, 1306),
    ("報價透明", 106, 1115),
    ("零件供應", 139, 803),
    ("便利設施", 20, 677),
    ("等待預約", 20, 271),
]
# T7 §2 作者層級來源 × 流失
SOURCE_TABLE = [
    ("PTT", 315, 2230),
    ("Mobile01", 504, 2764),
    ("Dcard", 95, 1400),
]
SOURCE_ORDER = ("mobile01", "ptt", "dcard")
SOURCE_LABEL = {"mobile01": "Mobile01", "ptt": "PTT", "dcard": "Dcard"}


def wilson(k: int, n: int, z: float = 1.96):
    if n <= 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    return p, max(0.0, center - margin), min(1.0, center + margin)


def png_size(path: Path) -> tuple[int, int]:
    import struct

    with path.open("rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(f"{path.name} 不是 PNG")
        f.read(4)
        if f.read(4) != b"IHDR":
            raise RuntimeError(f"{path.name} 缺少 IHDR")
        w, h = struct.unpack(">II", f.read(8))
    return w, h


def setup():
    hits = [
        f for f in font_manager.fontManager.ttflist
        if "jhenghei" in f.name.lower() or Path(f.fname).name.lower().startswith("msjh")
    ]
    if not hits:
        raise RuntimeError("找不到 Microsoft JhengHei")
    plt.rcParams["font.family"] = "Microsoft JhengHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = PAPER
    plt.rcParams["savefig.facecolor"] = PAPER
    plt.rcParams["axes.facecolor"] = PAPER
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15
    plt.rcParams["legend.fontsize"] = 14
    plt.rcParams["axes.titlesize"] = 18
    FIG.mkdir(parents=True, exist_ok=True)


def new_fig(w=12.4, h=4.2):
    """寬度對齊簡報內容區。14pt 以上在等寬投影時約 ≥ 28px。"""
    fig, ax = plt.subplots(figsize=(w, h), dpi=160)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=15)
    return fig, ax


def finish(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=160, facecolor=PAPER)
    plt.close(fig)
    w, h = png_size(path)
    if w < 1600 or h < 300:
        raise RuntimeError(f"{path.name} 只有 {w}×{h}")
    print(f"{path.name} {w}×{h}")


def load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def f1_aspects():
    rows = []
    for name, k, n in ASPECT_TABLE:
        p, lo, hi = wilson(k, n)
        rows.append((name, p, lo, hi, k, n))
    rows.sort(key=lambda r: -r[1])
    fig, ax = new_fig(12.4, 4.2)
    labels = [r[0] for r in rows]
    y = [r[1] * 100 for r in rows]
    yerr = [[(r[1] - r[2]) * 100 for r in rows], [(r[3] - r[1]) * 100 for r in rows]]
    colors = [RED if i == 0 else BLUE for i in range(len(rows))]
    ax.bar(labels, y, color=colors, width=0.72, zorder=3)
    ax.errorbar(labels, y, yerr=yerr, fmt="none", ecolor=INK, elinewidth=1.4, capsize=5, zorder=4)
    top = rows[0]
    ax.set_title(
        f"{top[0]}流失率最高（{top[1] * 100:.1f}%），銷售交車最低",
        fontsize=20, color=INK, pad=10,
    )
    ax.set_ylabel("流失率（%）", fontsize=16)
    ax.set_ylim(0, max(r[3] for r in rows) * 100 * 1.28)
    for i, r in enumerate(rows):
        ax.text(i, r[1] * 100 + 0.6, f"{r[1] * 100:.1f}", ha="center", va="bottom", fontsize=16, color=INK)
    finish(fig, FIG / "F1.png")


def f2_sources():
    rows = []
    for name, k, n in SOURCE_TABLE:
        p, lo, hi = wilson(k, n)
        rows.append((name, p, lo, hi))
    fig, ax = new_fig(12.4, 2.35)
    labels = [r[0] for r in rows]
    y = [r[1] * 100 for r in rows]
    yerr = [[(r[1] - r[2]) * 100 for r in rows], [(r[3] - r[1]) * 100 for r in rows]]
    peak = max(range(len(rows)), key=lambda i: rows[i][1])
    colors = [RED if i == peak else BLUE for i in range(len(rows))]
    ax.bar(labels, y, color=colors, width=0.62, zorder=3)
    ax.errorbar(labels, y, yerr=yerr, fmt="none", ecolor=INK, elinewidth=1.1, capsize=4, zorder=4)
    hi = rows[peak]
    dcard = next(r for r in rows if r[0] == "Dcard")
    ax.set_title(
        f"{hi[0]} 論壇發言者流失率 {hi[1] * 100:.1f}%，高於 Dcard 的 {dcard[1] * 100:.1f}%",
        fontsize=18, color=INK, pad=8,
    )
    ax.set_ylabel("論壇發言者流失率（%）", fontsize=16)
    ax.set_ylim(0, max(r[3] for r in rows) * 100 * 1.35)
    for i, r in enumerate(rows):
        ax.text(i, r[1] * 100 + 0.4, f"{r[1] * 100:.1f}", ha="center", va="bottom", fontsize=18, color=INK)
    finish(fig, FIG / "F2.png")


def f3_alts():
    import sys
    sys.path.insert(0, str(ROOT / "pipeline"))
    from label_aspects import ALTS

    pos = {r["sid"] for r in load_jsonl(P / "churn_positives.jsonl")}
    counts = Counter()
    for rec in load_jsonl(P / "aspect_labels.jsonl"):
        if rec["sid"] not in pos:
            continue
        for name in rec.get("alt") or []:
            if name in ALTS:
                counts[name] += 1
    rows = sorted(((name, counts[name]) for name in ALTS), key=lambda kv: -kv[1])
    fig, ax = new_fig(12.4, 4.2)
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    colors = [RED if i == 0 else BLUE for i in range(len(rows))]
    ax.bar(labels, vals, color=colors, width=0.72, zorder=3)
    ax.set_title(
        f"1,671 句流失裡，替代去向以{labels[0]}最多（{vals[0]} 句）",
        fontsize=20, color=INK, pad=10,
    )
    ax.set_ylabel("句數（一句可多選）", fontsize=16)
    ax.set_ylim(0, max(vals) * 1.22)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.015, str(v), ha="center", va="bottom", fontsize=16, color=INK)
    finish(fig, FIG / "F3.png")


def f4_risk_source():
    rows = load_jsonl(P / "authors_risk.jsonl")
    levels = ("低", "中", "高")
    stacks = {src: [] for src in SOURCE_ORDER}
    for lv in levels:
        sub = [r for r in rows if r["level"] == lv]
        c = Counter(r["source"] for r in sub)
        for src in SOURCE_ORDER:
            stacks[src].append(c.get(src, 0))
    fig, ax = new_fig(12.4, 2.35)
    import numpy as np

    x = np.arange(len(levels))
    bottom = np.zeros(len(levels))
    palette = {
        "mobile01": (BLUE_LIGHT, RED_LIGHT),
        "ptt": (BLUE_MID, RED_MID),
        "dcard": (BLUE, RED),
    }
    for src in SOURCE_ORDER:
        vals = np.array(stacks[src], dtype=float)
        colors = [palette[src][0], palette[src][0], palette[src][1]]
        ax.bar(x, vals, bottom=bottom, color=colors, width=0.62, label=SOURCE_LABEL[src], zorder=3)
        bottom += vals
    n_high = sum(stacks[src][2] for src in SOURCE_ORDER)
    n_all = len(rows)
    ax.set_title(
        f"高風險發言者 {n_high} 人，占全部發言者 {n_high / n_all * 100:.1f}%",
        fontsize=18, color=INK, pad=8,
    )
    ax.set_xticks(x, levels)
    ax.set_xlabel("風險等級（紅＝高）", fontsize=16)
    ax.set_ylabel("發言者數", fontsize=16)
    ax.legend(frameon=False, ncol=3, loc="upper right", fontsize=14)
    ax.set_ylim(0, max(bottom) * 1.18)
    finish(fig, FIG / "F4.png")


PERSONA_ORDER = ("過保精算派", "品質失望派", "口碑建議者", "靜默出走者", "未分類")


def f5_heatmap():
    risk = {r["author_id"]: r for r in load_jsonl(P / "authors_risk.jsonl")}
    persona_rows = load_jsonl(P / "authors_persona.jsonl")
    import sys
    sys.path.insert(0, str(ROOT / "pipeline"))
    from label_aspects import ASPECTS

    order = [name for name in PERSONA_ORDER if any(r["persona"] == name for r in persona_rows)]
    mat = []
    for name in order:
        members = [risk[r["author_id"]] for r in persona_rows if r["persona"] == name]
        mat.append([
            sum(m["aspect_n"][a] / m["n"] for m in members) / len(members)
            for a in ASPECTS
        ])
    import numpy as np

    data = np.array(mat) * 100
    fig, ax = plt.subplots(figsize=(12.4, 3.5), dpi=160)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    im = ax.imshow(data, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(ASPECTS)), ASPECTS, rotation=25, ha="right", fontsize=14)
    ax.set_yticks(range(len(order)), order, fontsize=14)
    ax.tick_params(axis="both", labelsize=14)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            color = "white" if val > data.max() * 0.62 else INK
            ax.text(j, i, f"{val:.0f}", ha="center", va="center", color=color, fontsize=15)
    # 標出最高的一格，用紅框而不是另做 3D。
    flat = int(np.argmax(data))
    i, j = divmod(flat, data.shape[1])
    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=RED, linewidth=2.2))
    ax.set_title(
        "過保精算派近半句子在談價格，品質失望派則集中在技術品質",
        fontsize=18, color=INK, pad=8,
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.outline.set_visible(False)
    cbar.set_label("面向出現比例（%）", fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    fig.tight_layout()
    path = FIG / "F5.png"
    fig.savefig(path, dpi=160, facecolor=PAPER)
    plt.close(fig)
    w, h = png_size(path)
    if w < 1600 or h < 400:
        raise RuntimeError(f"F5 只有 {w}×{h}")
    print(f"F5.png {w}×{h}")


def f7_persona_risk():
    risk = {r["author_id"]: r for r in load_jsonl(P / "authors_risk.jsonl")}
    persona_rows = [
        r for r in load_jsonl(P / "authors_persona.jsonl")
        if r["persona"] in PERSONA_ORDER
    ]
    order = [name for name in PERSONA_ORDER if any(r["persona"] == name for r in persona_rows)]
    counts, risks = [], []
    for name in order:
        members = [risk[r["author_id"]] for r in persona_rows if r["persona"] == name]
        counts.append(len(members))
        risks.append(sum(m["risk"] for m in members) / len(members))
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 2.85), dpi=160)
    fig.patch.set_facecolor(PAPER)
    peak = int(np.argmax(risks))
    for ax in axes:
        ax.set_facecolor(PAPER)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    colors = [RED if i == peak else BLUE for i in range(len(order))]
    axes[0].bar(order, counts, color=colors, width=0.72, zorder=3)
    axes[0].set_ylabel("發言者數", fontsize=15)
    for i, n in enumerate(counts):
        axes[0].text(i, n + max(counts) * 0.02, str(n), ha="center", va="bottom", fontsize=16, color=INK)
    axes[0].set_ylim(0, max(counts) * 1.22)
    axes[1].bar(order, risks, color=colors, width=0.72, zorder=3)
    axes[1].set_ylabel("平均風險分", fontsize=15)
    axes[1].set_ylim(0, 1.08)
    for i, v in enumerate(risks):
        axes[1].text(i, v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=16, color=INK)
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=15, labelsize=14)
        ax.tick_params(axis="y", labelsize=14)
    top_n = int(np.argmax(counts))
    if top_n == peak:
        title = f"{order[peak]}人數最多，平均風險也最高"
    else:
        title = f"{order[top_n]}人數最多，{order[peak]}平均風險最高"
    fig.suptitle(title, fontsize=18, color=INK)
    fig.tight_layout()
    path = FIG / "F7.png"
    fig.savefig(path, dpi=160, facecolor=PAPER)
    plt.close(fig)
    w, h = png_size(path)
    if w < 1600 or h < 300:
        raise RuntimeError(f"F7 只有 {w}×{h}")
    print(f"F7.png {w}×{h}")


def f6_calibration():
    gold = {}
    for rec in load_jsonl(P / "churn_verified.jsonl"):
        gold[rec["sid"]] = 1 if int(rec["c"]) >= 2 else 0
    xs, ys = [], []
    for rec in load_jsonl(P / "jev_lora_r4_ep2_pilot.jsonl"):
        p = float(rec["churn_p"]["2"]) + float(rec["churn_p"]["3"])
        xs.append(p)
        ys.append(gold[rec["sid"]])
    import numpy as np

    xs, ys = np.array(xs), np.array(ys)
    edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0000001]
    means, rates, ns = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (xs >= lo) & (xs < hi)
        if mask.sum() == 0:
            continue
        means.append(float(xs[mask].mean()))
        rates.append(float(ys[mask].mean()))
        ns.append(int(mask.sum()))
    fig, ax = new_fig(12.4, 2.35)
    ax.plot([0, 1], [0, 1], color="#B0B0B0", linewidth=1.2, linestyle="--", zorder=2)
    colors = [RED if m >= 0.8 else BLUE for m in means]
    ax.scatter([m * 100 for m in means], [r * 100 for r in rates], s=[max(80, n) for n in ns], c=colors, zorder=3)
    for m, r, n in zip(means, rates, ns):
        ax.text(m * 100, r * 100 + 3, f"n={n}", ha="center", va="bottom", fontsize=15, color=INK)
    hi = max(range(len(means)), key=lambda i: means[i])
    ax.set_title(
        f"高分仍偏高：預測接近 {means[hi] * 100:.0f}% 時，實際流失是 {rates[hi] * 100:.0f}%",
        fontsize=18, color=INK, pad=8,
    )
    ax.set_xlabel("桶內平均預測機率（%）", fontsize=16)
    ax.set_ylabel("實際流失比例（%）", fontsize=16)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(axis="both", color=GRID, linewidth=0.8)
    finish(fig, FIG / "F6.png")


def f_pipeline():
    """資料處理鏈。數字轉抄簡報 P5 與 T7 品質報告，不重算。不進 main()，避免連動重畫 F1–F7。"""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(16, 3.2), dpi=120)
    fig.patch.set_facecolor(PAPER)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 32)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])
    nodes = [
        ("爬取留言", "22.5 萬則"),
        ("切句・去重・去識別", "23.6 萬句"),
        ("售後關鍵詞篩選", "21,183 句"),
        ("五指標品質檢查", "超過 78 字只標記"),
        ("進入標註", "供模型與報告"),
    ]
    w, h, y = 26, 24, 4
    gap = 6.2
    xs = [3 + i * (w + gap) for i in range(5)]
    for i, ((title, sub), x) in enumerate(zip(nodes, xs)):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc="#EAF1F8", ec=BLUE, lw=1.6))
        ax.text(x + w / 2, y + 14.2, str(i + 1), ha="center", va="center", fontsize=16,
                color=BLUE, fontweight="bold")
        ax.text(x + w / 2, y + 9.2, title, ha="center", va="center", fontsize=15,
                color=INK, fontweight="bold")
        ax.text(x + w / 2, y + 4.6, sub, ha="center", va="center", fontsize=14, color="#3C4653")
        if i < 4:
            ax.add_patch(FancyArrowPatch((x + w + 0.3, y + h / 2), (x + w + gap - 0.3, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=16, color=BLUE, lw=1.6))
    FIG.mkdir(parents=True, exist_ok=True)
    path = FIG / "F9_pipeline.png"
    fig.savefig(path, dpi=120, facecolor=PAPER)
    plt.close(fig)
    print(f"F9_pipeline.png {png_size(path)[0]}×{png_size(path)[1]}")


def main():
    setup()
    f1_aspects()
    f2_sources()
    f3_alts()
    f6_calibration()
    if (P / "authors_risk.jsonl").exists() and (P / "authors_persona.jsonl").exists():
        f4_risk_source()
        f5_heatmap()
        f7_persona_risk()
    else:
        print("skip F4 F5：風險表或 persona 尚未產出")


if __name__ == "__main__":
    main()
