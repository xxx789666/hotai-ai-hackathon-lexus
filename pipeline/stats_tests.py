"""PB-03 來源／面向／流失原因的統計檢定。可重跑，不呼叫雲端模型。"""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT = ROOT / "reports" / "T7_stats_tests.md"

SOURCES = ["ptt", "mobile01", "dcard"]
SOURCE_LABEL = {"ptt": "PTT", "mobile01": "Mobile01", "dcard": "Dcard"}
ASPECTS = ["價格", "技術品質", "保固延保", "銷售交車", "態度", "報價透明", "零件供應", "便利設施", "等待預約"]
PAIRS = [("ptt", "mobile01"), ("ptt", "dcard"), ("mobile01", "dcard")]


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def last_by_sid(rows):
    last = {}
    for row in rows:
        last[row["sid"]] = row
    return last


def cramers_v(chi2, n, r, c):
    denom = n * min(r - 1, c - 1)
    return math.sqrt(chi2 / denom) if denom else float("nan")


def fmt_p(p):
    if p < 0.001:
        return "p<.001"
    return f"p={p:.3f}"


def wilson(k, n):
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return float(lo), float(hi)


def odds_ratio_ci(a, b, c, d):
    note = ""
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        note = "（含 0 格，Haldane–Anscombe +0.5）"
    ratio = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    log_r = math.log(ratio)
    return ratio, math.exp(log_r - 1.96 * se), math.exp(log_r + 1.96 * se), note


def chi_block(table):
    arr = np.array(table, dtype=float)
    chi2, p, dof, expected = chi2_contingency(arr, correction=False)
    n = int(arr.sum())
    v = cramers_v(chi2, n, arr.shape[0], arr.shape[1])
    return chi2, p, dof, expected, n, v


def rate_table(groups):
    """groups: ordered list of (label, n_churn, n_total)."""
    lines = ["| 組 | 流失 | n | 流失率 | Wilson 95% CI |", "| --- | ---: | ---: | ---: | --- |"]
    for label, k, n in groups:
        lo, hi = wilson(k, n)
        lines.append(f"| {label} | {k} | {n} | {k / n:.1%} | {lo:.1%}–{hi:.1%} |")
    return "\n".join(lines)


def pairwise(groups):
    """groups dict label -> (k, n). Bonferroni m=3."""
    lines = [
        "| 比較 | z | p | Bonferroni p | 顯著（α=0.05/3） |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    bits = []
    for a, b in PAIRS:
        k1, n1 = groups[a]
        k2, n2 = groups[b]
        z, p = proportions_ztest([k1, k2], [n1, n2], alternative="two-sided")
        adj = min(1.0, float(p) * 3)
        sig = "是" if adj < 0.05 else "否"
        lines.append(
            f"| {SOURCE_LABEL[a]} vs {SOURCE_LABEL[b]} | {float(z):.2f} | {float(p):.4g} | {adj:.4g} | {sig} |"
        )
        bits.append((a, b, float(z), float(p), adj, sig, k1 / n1, k2 / n2))
    return "\n".join(lines), bits


def source_section(title, groups_order, narrative):
    labels = []
    table = []
    gmap = {}
    for label, k, n in groups_order:
        labels.append(label)
        gmap[label] = (k, n)
        table.append([k, n - k])
    chi2, p, dof, expected, n, v = chi_block(table)
    lo_exp = expected.min()
    pair_md, bits = pairwise(gmap)
    body = f"""### {title}

{rate_table(groups_order)}

χ²({dof}, N={n}) = {chi2:.2f}，{fmt_p(p)}，Cramér's V = {v:.3f}。最小期望次數 {lo_exp:.1f}。未使用 Yates 校正。

{pair_md}

簡報可以怎麼寫：{narrative(chi2, p, v, bits)}
"""
    return body, chi2, p, v


def main():
    sents = load_jsonl(DATA / "aftersales.jsonl")
    verified = last_by_sid(load_jsonl(DATA / "churn_verified.jsonl"))
    aspects = last_by_sid(load_jsonl(DATA / "aspect_labels.jsonl"))
    positives = load_jsonl(DATA / "churn_positives.jsonl")

    by_sid = {r["sid"]: r for r in sents}
    churn = {sid: int(row["c"]) >= 2 for sid, row in verified.items()}
    assert len(by_sid) == 21183

    # sentence-level source
    sent_g = []
    for src in SOURCES:
        rows = [r for r in sents if r["source"] == src]
        k = sum(1 for r in rows if churn.get(r["sid"], False))
        sent_g.append((src, k, len(rows)))

    def sent_narr(chi2, p, v, bits):
        return (
            f"句子層級三來源流失率不同（χ²={chi2:.1f}，{fmt_p(p)}，Cramér's V={v:.3f}，屬小效果）。"
            "此層級同作者多句不獨立，只作描述；簡報應以作者層級為準。"
        )

    # author-level
    authors = defaultdict(list)
    for r in sents:
        authors[(r["source"], r.get("author") or "")].append(r["sid"])
    auth_g = []
    for src in SOURCES:
        keys = [k for k in authors if k[0] == src]
        k = sum(1 for key in keys if any(churn.get(sid, False) for sid in authors[key]))
        auth_g.append((src, k, len(keys)))

    def auth_narr(chi2, p, v, bits):
        rates = {a: k / n for a, k, n in auth_g}
        hi = max(SOURCES, key=lambda s: rates[s])
        lo = min(SOURCES, key=lambda s: rates[s])
        return (
            f"{SOURCE_LABEL[hi]} 作者流失率顯著高於 {SOURCE_LABEL[lo]}"
            f"（作者層級 χ²={chi2:.1f}，{fmt_p(p)}，Cramér's V={v:.3f}，屬小效果）。"
            "母體是論壇發言者，不是全體車主。"
        )

    # aspects
    aspect_rows = []
    tables_2x2 = []
    for name in ASPECTS:
        a = b = c = d = 0
        for r in sents:
            has = name in (aspects.get(r["sid"], {}).get("a") or [])
            pos = churn.get(r["sid"], False)
            if has and pos:
                a += 1
            elif has and not pos:
                b += 1
            elif not has and pos:
                c += 1
            else:
                d += 1
        chi2, p, dof, expected, n, v = chi_block([[a, b], [c, d]])
        phi = math.sqrt(chi2 / n)
        ratio, lo, hi, note = odds_ratio_ci(a, b, c, d)
        rate = a / (a + b) if (a + b) else float("nan")
        aspect_rows.append((name, a, a + b, rate, chi2, p, v, phi, ratio, lo, hi, note, expected.min()))
        tables_2x2.append((name, a, b, c, d))

    # 9x2 uses aspect-present counts only (multi-label; rows not exclusive)
    nine = [[row[1], row[2] - row[1]] for row in aspect_rows]
    chi9, p9, dof9, exp9, n9, v9 = chi_block(nine)

    # t2 x source
    t2_src = Counter()
    for r in positives:
        t2_src[(r.get("t2") or "（空）", r["source"])] += 1
    t2_levels = sorted({k[0] for k in t2_src}, key=lambda t: -sum(t2_src[(t, s)] for s in SOURCES))
    raw_table = [[t2_src[(t, s)] for s in SOURCES] for t in t2_levels]
    raw_exp = chi2_contingency(np.array(raw_table, dtype=float), correction=False)[3]
    small = sorted({t2_levels[i] for i, row in enumerate(raw_exp) for v in row if v < 5})
    keep = [t for t in t2_levels if t not in small]
    merged_label = "其他（合併期望<5之小類）"
    merged_levels = keep + ([merged_label] if small else [])
    merged = []
    for t in keep:
        merged.append([t2_src[(t, s)] for s in SOURCES])
    if small:
        merged.append([sum(t2_src[(t, s)] for t in small) for s in SOURCES])
    chi_t, p_t, dof_t, exp_t, n_t, v_t = chi_block(merged)

    model_by_src = Counter()
    for r in sents:
        model_by_src[(r["source"], verified[r["sid"]].get("model"))] += 1

    sent_md, _, _, _ = source_section("1. 來源 × 流失（句子層級）", sent_g, sent_narr)
    auth_md, chi_a, p_a, v_a = source_section("2. 來源 × 流失（作者層級，主要結果）", auth_g, auth_narr)

    aspect_header = (
        "| 面向 | 有此面向且流失 | 有此面向 n | 流失率 | χ² | p | Cramér's V | Phi | 勝算比 | 95% CI |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"
    )
    aspect_lines = [aspect_header]
    for name, a, n_has, rate, chi2, p, v, phi, ratio, lo, hi, note, emin in aspect_rows:
        aspect_lines.append(
            f"| {name} | {a} | {n_has} | {rate:.1%} | {chi2:.1f} | {fmt_p(p)} | {v:.3f} | {phi:.3f} | {ratio:.2f}{note} | {lo:.2f}–{hi:.2f} |"
        )
    by_rate = sorted(aspect_rows, key=lambda r: r[3])
    lo_asp, hi_asp = by_rate[0], by_rate[-1]
    aspect_narr = (
        f"流失率最高的面向是{hi_asp[0]}（{hi_asp[3]:.1%}，勝算比 {hi_asp[8]:.2f}，95% CI {hi_asp[9]:.2f}–{hi_asp[10]:.2f}），"
        f"最低的是{lo_asp[0]}（{lo_asp[3]:.1%}，勝算比 {lo_asp[8]:.2f}，95% CI {lo_asp[9]:.2f}–{lo_asp[10]:.2f}）。"
        "分母是全部 21,183 句；沒有該面向標記者算入「無」。"
    )

    raw_md = ["| t2 | " + " | ".join(SOURCE_LABEL[s] for s in SOURCES) + " |", "| --- | ---: | ---: | ---: |"]
    for t in t2_levels:
        raw_md.append("| " + t + " | " + " | ".join(str(t2_src[(t, s)]) for s in SOURCES) + " |")
    merged_md = ["| t2（檢定用） | " + " | ".join(SOURCE_LABEL[s] for s in SOURCES) + " |", "| --- | ---: | ---: | ---: |"]
    for t, row in zip(merged_levels, merged):
        merged_md.append("| " + t + " | " + " | ".join(str(int(x)) for x in row) + " |")

    model_bits = "、".join(
        f"{SOURCE_LABEL[s]} {model} {n}" for (s, model), n in sorted(model_by_src.items())
    )

    text = f"""# T7 統計檢定（PB-03）

金標取 `churn_verified.jsonl` 同 sid 最後一筆（本檔每 sid 一筆），流失＝c≥2。面向取 `aspect_labels.jsonl` 的 `a`（多選）。來源取 `aftersales.jsonl`。套件：scipy、statsmodels（系統 Python 3.12）。χ² 未用 Yates 校正。效果量 Cramér's V：0.1 小、0.3 中、0.5 大（慣用門檻）。

## 作者層級是主要結果

同作者多句不獨立（iPAS 科目 2 p.93）。句子層級檢定只描述分布；推論用作者層級（作者＝source + author，任一句 c≥2 即該作者流失）。

{auth_md}

{sent_md}

## 3. 面向 × 流失

九個面向各做 2×2（有此面向 vs 無）×（流失 vs 否）。勝算比＝（有面向且流失／有面向未流失）÷（無面向且流失／無面向未流失）。

{chr(10).join(aspect_lines)}

簡報可以怎麼寫：{aspect_narr}

九面向 9×2 表（列＝面向、欄＝流失／未流失；多選所以各列不互斥，χ² 只描述面向之間流失人數是否不均，不能當成獨立樣本的關聯檢定）：χ²({dof9}, N={n9}) = {chi9:.1f}，{fmt_p(p9)}，Cramér's V = {v9:.3f}。最小期望次數 {exp9.min():.1f}。

## 4. 流失原因 t2 × 來源

母體是 `churn_positives.jsonl`（n={len(positives)}），不是全部售後句。

{chr(10).join(raw_md)}

原始表有期望次數 < 5 的格子，涉及：{"、".join(small) if small else "（無）"}。scipy 的 Fisher exact 只支援 2×2，因此把這些小類合併成「其他」後再做 χ²（未用蒙地卡羅）。

{chr(10).join(merged_md)}

合併後 χ²({dof_t}, N={n_t}) = {chi_t:.1f}，{fmt_p(p_t)}，Cramér's V = {v_t:.3f}。最小期望次數 {exp_t.min():.1f}。

簡報可以怎麼寫：流失句的原因結構與來源有關（合併小類後 χ²={chi_t:.1f}，{fmt_p(p_t)}，Cramér's V={v_t:.3f}）。小類已合併，不要把「信任破裂」等個位數原因單獨說成來源差異。

## 5. 限制

- 三來源複核模型不同：{model_bits}。Mobile01／PTT 為 Sonnet、Dcard 為 GPT-5.6 Sol；重疊句一致率 98.4%（見 iPAS 對照與既有複核紀錄）。
- 母體是三個論壇的公開發言者，不是全體 Lexus 車主。Dcard 偏購車階段，句子層級流失率會被作者重複發言放大或縮小。
- 樣本量大，p 值容易顯著；簡報要併報 Cramér's V 或勝算比與信賴區間（iPAS 科目 2 p.92）。
- 面向是多選，9×2 的 N 是面向出現次數加總，不是 21,183。
- 作者層級把同一人在不同站的帳號當成不同作者。

## 重跑

```text
python pipeline/stats_tests.py
```
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"author chi2={chi_a:.2f} p={p_a:.6g} V={v_a:.3f}")
    print(f"aspect high {hi_asp[0]} OR={hi_asp[8]:.3f} low {lo_asp[0]} OR={lo_asp[8]:.3f}")


if __name__ == "__main__":
    main()
