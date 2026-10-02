"""T15：趨勢報告（日報／週報／季報）範例與圖 F9、F10。

  python pipeline/trend_reports.py
輸入：aftersales.jsonl（date、source、author）、churn_verified.jsonl（金標 c）、churn_r4_all.jsonl（r4 p_churn）、
      aspect_labels.jsonl（a 面向、s 情緒、m 車型）、authors_risk.jsonl（作者風險等級）。
輸出：reports/T15_trend_reports.md、reports/figures/F9.png（季趨勢）、F10.png（週趨勢與預警）。
文字一律經 deidentify.mask_text；作者以 hid 對應風險等級，不輸出原帳號。
"""
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.stats.proportion import proportion_confint  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deidentify import compile_shop_map, hid, load_jsonl, load_salt, mask_text, scan_shops  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "T15_trend_reports.md"
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC"]
plt.rcParams["axes.unicode_minus"] = False
BLUE, BLUE_LIGHT, RED, GREY = "#2F5D8C", "#A9C3DC", "#C0392B", "#8A8F98"
ASPECTS = ["價格", "報價透明", "態度", "技術品質", "等待預約", "保固延保", "零件供應", "便利設施", "銷售交車"]
SPIKE_MULT, SPIKE_MIN = 3.0, 5  # 週量 ≥ 前 4 週平均 × 3（+200%）且 ≥ 5 句才亮燈


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return float(lo), float(hi)


def pct(k, n):
    return f"{100 * k / n:.1f}%" if n else "—"


def load():
    sents = list(load_jsonl(P / "aftersales.jsonl"))
    gold = {r["sid"]: int(r["c"]) for r in load_jsonl(P / "churn_verified.jsonl")}
    r4 = {r["sid"]: float(r["p_churn"]) for r in load_jsonl(P / "churn_r4_all.jsonl")}
    asp = {r["sid"]: r for r in load_jsonl(P / "aspect_labels.jsonl")}
    level = {r["author_id"]: r["level"] for r in load_jsonl(P / "authors_risk.jsonl")}
    salt = load_salt()
    rows = []
    for s in sents:
        a = asp.get(s["sid"], {})
        rows.append({
            "sid": s["sid"], "date": s["date"], "source": s["source"], "text": s["text"],
            "aid": hid(salt, s["source"], s["author"]),
            "gold": gold.get(s["sid"], 0) >= 2, "p": r4.get(s["sid"], 0.0),
            "aspects": a.get("a") or [], "sent": a.get("s"), "model": a.get("m"),
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df["level"] = df["aid"].map(level).fillna("未評")
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["week"] = df["date"].dt.to_period("W-SUN").apply(lambda p: p.start_time.date())
    df["neg"] = df["sent"].apply(lambda v: v == -1)
    _, shop_pat = compile_shop_map(scan_shops(sents))
    counts = Counter()
    return df, (lambda t: mask_text(t or "", counts, shop_pat))


def explode_aspects(df):
    e = df[["sid", "quarter", "week", "date", "gold", "model", "aspects"]].explode("aspects").dropna(subset=["aspects"])
    return e[e["aspects"].isin(ASPECTS)]


def quarterly(df, n_q=12):
    qs = sorted(df["quarter"].unique())[-n_q:]
    d = df[df["quarter"].isin(qs)]
    g = d.groupby("quarter").agg(n=("sid", "size"), churn=("gold", "sum"), neg=("neg", "sum")).reindex(qs).fillna(0).astype(int)
    g["rate"] = g["churn"] / g["n"]
    ci = [wilson(k, n) for k, n in zip(g["churn"], g["n"])]
    g["lo"] = [c[0] for c in ci]
    g["hi"] = [c[1] for c in ci]
    e = explode_aspects(d)
    ea = e.groupby(["quarter", "aspects"]).agg(n=("sid", "size"), churn=("gold", "sum")).reset_index()
    return qs, g, ea


def weekly(df, n_w=26):
    last = df["date"].max()
    end_week = (last - pd.Timedelta(days=last.weekday())).date()  # 最後一個（可能不完整）週的週一
    wk = sorted(w for w in df["week"].unique() if w < end_week)[-n_w:]
    d = df[df["week"].isin(wk)]
    g = d.groupby("week").agg(n=("sid", "size"), churn=("gold", "sum"),
                              flagged=("p", lambda s: int((s >= 0.5).sum()))).reindex(wk).fillna(0).astype(int)
    e = explode_aspects(d)
    alerts = []
    for key in (["aspects"], ["model", "aspects"]):
        c = e.groupby(key + ["week"]).size().unstack("week").reindex(columns=wk).fillna(0)
        for idx, row in c.iterrows():
            vals = row.values
            for i in range(4, len(wk)):
                base = vals[i - 4:i].mean()
                if vals[i] >= SPIKE_MIN and vals[i] >= SPIKE_MULT * max(base, 1e-9):
                    name = idx if isinstance(idx, str) else " × ".join(str(x) for x in idx)
                    alerts.append({"week": wk[i], "item": name, "n": int(vals[i]), "base": round(float(base), 1)})
    return wk, g, alerts, e


def style(ax):
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def fig_quarterly(qs, g, ea):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw={"width_ratios": [1.1, 1]})
    fig.patch.set_facecolor("#F4F7FB")
    ax1.set_facecolor("#F4F7FB")
    ax2.set_facecolor("#F4F7FB")
    x = list(range(len(qs)))
    ax1.bar(x, g["n"], color=BLUE_LIGHT, label="售後句數")
    ax1.set_ylabel("售後句數（三站）")
    ax1.set_xticks(x, qs, rotation=45, ha="right")
    ax1b = ax1.twinx()
    ax1b.errorbar(x, 100 * g["rate"], yerr=[100 * (g["rate"] - g["lo"]), 100 * (g["hi"] - g["rate"])],
                  color=RED, marker="o", lw=2, capsize=3, label="流失率（金標）與 Wilson 95% 區間")
    ax1b.set_ylabel("流失率 %", color=RED)
    ax1b.set_ylim(0, max(25, 100 * g["hi"].max() + 2))
    ax1b.spines["top"].set_visible(False)
    ax1.set_title("季報：售後討論量與流失率（近 12 季）", loc="left", fontsize=14, fontweight="bold")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1b.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    top = ea.groupby("aspects")["churn"].sum().sort_values(ascending=False).head(5).index
    piv = ea[ea["aspects"].isin(top)].pivot(index="quarter", columns="aspects", values="churn").reindex(qs).fillna(0)
    for col, color in zip(top, [RED, BLUE, "#E07A72", "#5C84B0", GREY]):
        ax2.plot(x, piv[col], marker="o", lw=2, color=color, label=col)
    ax2.set_xticks(x, qs, rotation=45, ha="right")
    ax2.set_ylabel("流失句數")
    ax2.set_title("流失句主要面向的季走勢（前 5 面向）", loc="left", fontsize=14, fontweight="bold")
    ax2.legend(frameon=False)
    style(ax1)
    style(ax2)
    fig.text(0.01, 0.01, "母體是三站論壇發言者，最後一季只到 9/19；季報上線後改用 CRM／DMS 資料。", fontsize=10, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG / "F9.png", dpi=120, facecolor="#F4F7FB")
    plt.close(fig)


def fig_weekly(wk, g, alerts):
    fig, ax = plt.subplots(figsize=(16, 7.5))
    x = list(range(len(wk)))
    ax.bar(x, g["n"], color=BLUE_LIGHT, label="售後句數")
    ax.bar(x, g["churn"], color=RED, width=0.5, label="流失句（金標）")
    ax.plot(x, g["flagged"], color=BLUE, marker="o", lw=1.5, label="r4 判流失（p>=0.5）")
    ax.set_xticks(x, [w.strftime("%m/%d") for w in wk], rotation=45, ha="right")
    ax.set_ylabel("句數 / 週")
    ax.set_title("週報：近 26 週討論量、流失句與預警（週量達前 4 週平均 3 倍以上且 5 句以上）", loc="left", fontsize=14, fontweight="bold")
    by_week = {}
    for a in sorted(alerts, key=lambda a: -a["n"]):
        by_week.setdefault(a["week"], []).append(a["item"])
    ax.set_ylim(0, g["n"].max() * 1.45)
    for w, items in by_week.items():
        i = wk.index(w)
        label = "、".join(items[:2]) + (f" 等{len(items)}項" if len(items) > 2 else "")
        ax.annotate(label, (i, g["n"].iloc[i]), xytext=(0, 10), textcoords="offset points", ha="center", va="bottom",
                    fontsize=9.5, color=RED, rotation=90, arrowprops={"arrowstyle": "-", "color": RED, "lw": 0.8})
    ax.legend(frameon=False, loc="upper left")
    style(ax)
    fig.text(0.01, 0.01, "一次性爬取的快照，近幾週可能未抓齊；上線後為每日排程資料。", fontsize=10, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG / "F10.png", dpi=120, facecolor="white")
    plt.close(fig)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    df, mask = load()
    qs, gq, ea = quarterly(df)
    wk, gw, alerts, ew = weekly(df)
    fig_quarterly(qs, gq, ea)
    fig_weekly(wk, gw, alerts)

    L = ["# T15：趨勢報告範例（日報／週報／季報）與預警", "",
         f"日期：2026-09-30。資料：`aftersales.jsonl` {len(df):,} 句（{df['date'].min().date()} 至 {df['date'].max().date()}），"
         "流失以金標 c≥2、即時判斷以 r4 p_churn ≥ 0.5；面向、情緒、車型取 `aspect_labels.jsonl`。文字經去識別。",
         "圖：`reports/figures/F9.png`（季趨勢）、`F10.png`（週趨勢與預警）。", "",
         "## 0. 三種報告的分工", "",
         md_table(["報告", "頻率", "讀者", "內容", "趨勢方法"], [
             ["日報", "每日 08:00", "客服主管、服務廠專員", "昨日新句數、r4 判流失句與作者風險等級、面向分布、預警、待審話術數", "與前 7 日平均比較"],
             ["週報", "每週一", "售後主管", "本週量與流失句、面向與車型變化、預警清單、審核核准率、投遞與點擊", "週量對前 4 週平均；≥3 倍且 ≥5 句亮燈"],
             ["季報", "每季首週", "售後決策者、品牌", "流失率與 Wilson 區間、面向與車型結構、Persona 規模變化、KPI 三層級達成、模型重驗", "同季對比（YoY）、連續 12 季走勢、χ² 檢定"],
         ]), "",
         "母體限制：現在是一次性爬取的論壇快照，近幾週可能未抓齊，最後一季只到 9/19；上線後三種報告改讀 CRM／DMS 與每日排程資料，方法不變。", ""]

    q_last, q_prev = qs[-1], qs[-2]
    yoy = qs[-5] if len(qs) >= 5 else None
    r = gq.loc[q_last].to_dict()
    rp = gq.loc[q_prev].to_dict()
    for k in ('n', 'churn', 'neg'):
        r[k], rp[k] = int(r[k]), int(rp[k])
    line = (f"- 售後句 {r['n']:,}（{q_prev} 為 {rp['n']:,}）。流失句 {r['churn']}，流失率 {pct(r['churn'], r['n'])}"
            f"（Wilson 95% {100 * r['lo']:.1f}–{100 * r['hi']:.1f}%），{q_prev} 為 {pct(rp['churn'], rp['n'])}。")
    if yoy:
        line += f" 去年同季 {yoy} 為 {pct(int(gq.loc[yoy, 'churn']), int(gq.loc[yoy, 'n']))}。"
    L += [f"## 1. 季報範例：{q_last}（至 9/19，未滿季）", "", line,
          f"- 負面情緒句占 {pct(r['neg'], r['n'])}（{q_prev} {pct(rp['neg'], rp['n'])}）。", ""]
    rows = []
    for a in ASPECTS:
        cur = ea[(ea.quarter == q_last) & (ea.aspects == a)]
        prv = ea[(ea.quarter == q_prev) & (ea.aspects == a)]
        n1, c1 = (int(cur.n.iloc[0]), int(cur.churn.iloc[0])) if len(cur) else (0, 0)
        n0, c0 = (int(prv.n.iloc[0]), int(prv.churn.iloc[0])) if len(prv) else (0, 0)
        d = (c1 / n1 - c0 / n0) * 100 if n1 and n0 else None
        rows.append([a, n1, c1, pct(c1, n1), n0, pct(c0, n0), f"{d:+.1f} pp" if d is not None else "—"])
    L += ["面向 × 流失（本季 vs 上季）：", "", md_table(["面向", "本季句數", "流失句", "流失率", "上季句數", "上季流失率", "變化"], rows), ""]
    mq = df[(df.quarter == q_last) & df.model.notna()]["model"].value_counts().head(5)
    L += ["本季提到的車型（前 5）：" + "、".join(f"{m} {n}" for m, n in mq.items()), ""]
    src = df[df.quarter == q_last].groupby("source").agg(n=("sid", "size"), c=("gold", "sum"))
    L += ["來源：" + "、".join(f"{s} {int(v.n)} 句／流失 {int(v.c)}" for s, v in src.iterrows()), ""]
    ex = df[(df.quarter == q_last) & df.gold].sort_values("p", ascending=False).head(3)
    L += ["代表流失句（去識別）：", ""] + [f"- 「{mask(t)}」（{s}，r4 p={p:.2f}）" for t, s, p in zip(ex.text, ex.source, ex.p)] + [""]

    w_last = wk[-1]
    gl = gw.loc[w_last]
    base = gw.iloc[-5:-1]["n"].mean()
    L += [f"## 2. 週報範例：{w_last} 起的一週", "",
          f"- 售後句 {int(gl['n'])}（前 4 週平均 {base:.0f}；最後幾週為爬取快照未抓齊，量偏低），金標流失句 {int(gl['churn'])}，r4 判流失 {int(gl['flagged'])} 句。",
          f"- 近 26 週預警共 {len(alerts)} 次（規則：週量 ≥ 前 4 週平均 3 倍且 ≥ 5 句）。", ""]
    if alerts:
        L += [md_table(["週", "項目", "週量", "前 4 週平均"], [[a["week"], a["item"], a["n"], a["base"]] for a in sorted(alerts, key=lambda a: a['week'], reverse=True)[:12]]), ""]
    ewl = ew[ew.week == w_last].groupby("aspects").agg(n=("sid", "size"), c=("gold", "sum")).sort_values("n", ascending=False)
    L += ["本週面向：" + "、".join(f"{a} {int(v.n)}（流失 {int(v.c)}）" for a, v in ewl.iterrows()), ""]

    daily = df.groupby(df["date"].dt.date).size()
    day = max(d for d, n in daily.items() if n >= 5)
    prev7 = [d for d in daily.index if d < day][-7:]
    dd = df[df["date"].dt.date == day]
    flagged = dd[dd.p >= 0.5].sort_values("p", ascending=False)
    L += [f"## 3. 日報範例：{day}", "",
          f"- 新增售後句 {len(dd)}（前 7 日平均 {daily.loc[prev7].mean():.0f}）；r4 判流失 {len(flagged)} 句，"
          f"其中作者風險「高」{int((flagged.level == '高').sum())} 句、「中」{int((flagged.level == '中').sum())} 句。",
          "- 面向：" + ("、".join(f"{a} {n}" for a, n in Counter(x for xs in dd.aspects for x in xs).most_common(5)) or "無"),
          "- 預警：" + ("、".join(a["item"] for a in alerts if a["week"] == dd.week.iloc[0]) or "無"), "",
          "待審話術：依觸發規則產生的草稿數在上線後由資料庫 D 提供，本範例無。", "",
          "r4 判流失句（去識別，供客服溯源）：", ""]
    L += [f"- p={p:.2f}｜作者風險 {lv}｜{s}｜「{mask(t)}」"
          for p, lv, s, t in list(zip(flagged.p, flagged.level, flagged.source, flagged.text))[:8]] + [""]

    L += ["## 4. 方法與限制", "",
          "- 流失率用金標（Sonnet／GPT-5.6 Sol 複核 c≥2）；上線後每日只有 r4 判斷，季報再用人工抽樣校正。",
          "- 預警門檻（3 倍、5 句）是初版，回溯 26 週的誤報要由客服判讀後調整；車型 × 面向的量在論壇資料偏少，上線改用工單資料後會更穩。",
          "- 季報的同季對比要配 χ²；本範例只列比例與區間。",
          "- 全部文字經 `deidentify.mask_text`，作者以雜湊對應風險等級。"]
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT.name, "| quarters", qs[0], "-", qs[-1], "| weeks", wk[0], "-", wk[-1], "| alerts", len(alerts), "| day", day)


if __name__ == "__main__":
    main()
