"""L4：句 → 作者風險表。作者＝(source, author)，輸出只留雜湊 ID。

  python pipeline/author_risk.py

風險分＝作者 p_churn 最大值 × 0.6 ＋（命中規則數／8）× 0.4
高 ≥ 0.6、中 ≥ 0.3 且 < 0.6、低 < 0.3
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from deidentify import hid, load_salt  # noqa: E402
from label_aspects import ALTS, ASPECTS  # noqa: E402
from verify_churn import load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
OUT = P / "authors_risk.jsonl"
TOP = P / "authors_top20.json"
SUMMARY = P / "authors_risk_summary.json"

W_MODEL = 0.6
W_RULE = 0.4
HIGH = 0.6
MID = 0.3
N_RULES = 8

RULES = [
    ("R1", "過保"),
    ("R2", "價格負面"),
    ("R3", "找出口"),
    ("R4", "自理"),
    ("R5", "零件等料"),
    ("R6", "品質失望"),
    ("R7", "已離開"),
    ("R8", "帶人走"),
]
EXIT_ALTS = {"一般外廠", "技師開業", "連鎖保養"}
SELF_ALTS = {"DIY", "自備料"}
EXIT_T2 = {"外廠詢問", "外廠推薦"}


def last_by_sid(name: str) -> dict:
    out = {}
    for rec in load_jsonl(P / name):
        out[rec["sid"]] = rec
    return out


def level_of(risk: float) -> str:
    if risk >= HIGH:
        return "高"
    if risk >= MID:
        return "中"
    return "低"


def mode_or_none(values: list[str]):
    if not values:
        return None
    counts = Counter(values)
    best = max(counts.values())
    return sorted(k for k, v in counts.items() if v == best)[0]


def main() -> None:
    salt = load_salt()
    after = load_jsonl(P / "aftersales.jsonl")
    pred = last_by_sid("churn_r4_all.jsonl")
    gold = last_by_sid("churn_verified.jsonl")
    aspects = last_by_sid("aspect_labels.jsonl")
    positives = last_by_sid("churn_positives.jsonl")
    deid = last_by_sid("aftersales_deid.jsonl")

    if len(pred) != len(after):
        raise RuntimeError(f"r4 句數 {len(pred)} != 售後 {len(after)}")

    # 確認雜湊與去識別檔的 author 欄一致，避免簡報對不到人。
    checked = 0
    for rec in after[:200]:
        d = deid.get(rec["sid"])
        if not d:
            continue
        got = hid(salt, rec["source"], rec.get("author"))
        if got != d.get("author"):
            raise RuntimeError(f"hid 與 deid author 不一致 sid={rec['sid']}")
        checked += 1
    if checked < 50:
        raise RuntimeError("deid 對照樣本不足")

    groups: dict[tuple, list] = defaultdict(list)
    for rec in after:
        groups[(rec["source"], rec.get("author"))].append(rec)

    rows = []
    for (source, author), sents in groups.items():
        author_id = hid(salt, source, author)
        sids = [s["sid"] for s in sents]
        ps, p50, p80 = [], 0, 0
        n_c2 = n_c3 = 0
        aspect_n = Counter()
        aspect_neg = Counter()
        alt_n = Counter()
        wy_in = wy_out = 0
        w_s = w_a = w_o = 0
        t2 = Counter()
        models = []
        dates = []
        neg_n = 0
        r1 = r2 = r3 = r4 = r5 = False
        quality_neg = 0
        r7_model = False
        r8 = False
        best_sid = None
        best_p = -1.0
        for sid in sids:
            pr = pred[sid]
            p = float(pr["p_churn"])
            ps.append(p)
            if p >= 0.5:
                p50 += 1
            if p >= 0.8:
                p80 += 1
                r7_model = True
            if p > best_p:
                best_p = p
                best_sid = sid
            g = gold.get(sid, {})
            c = g.get("c")
            w = g.get("w")
            if c is not None and int(c) >= 2:
                n_c2 += 1
            if c is not None and int(c) == 3:
                n_c3 += 1
            if w == "s":
                w_s += 1
            elif w == "a":
                w_a += 1
            elif w == "o":
                w_o += 1
            if w == "a" and c is not None and int(c) >= 2:
                r8 = True
            asp = aspects.get(sid, {})
            names = [a for a in (asp.get("a") or []) if a in ASPECTS]
            sent = asp.get("s")
            if sent == -1:
                neg_n += 1
            for name in names:
                aspect_n[name] += 1
                if sent == -1:
                    aspect_neg[name] += 1
            if "價格" in names and sent == -1:
                r2 = True
            if "零件供應" in names and sent == -1:
                r5 = True
            if "技術品質" in names and sent == -1:
                quality_neg += 1
            alts = {a for a in (asp.get("alt") or []) if a in ALTS}
            for name in alts:
                alt_n[name] += 1
            if alts & EXIT_ALTS:
                r3 = True
            if alts & SELF_ALTS:
                r4 = True
            wy = asp.get("wy")
            if wy == "in":
                wy_in += 1
            elif wy == "out":
                wy_out += 1
                r1 = True
            if asp.get("m"):
                models.append(asp["m"])
            pos = positives.get(sid)
            if pos and pos.get("t2"):
                t2[pos["t2"]] += 1
                if pos["t2"] in EXIT_T2:
                    r3 = True
        for s in sents:
            if s.get("date"):
                dates.append(str(s["date"]))
        r6 = quality_neg >= 2 or t2.get("品質", 0) >= 1
        r7 = n_c3 >= 1 or r7_model
        flags = {
            "R1": r1, "R2": r2, "R3": r3, "R4": r4,
            "R5": r5, "R6": r6, "R7": r7, "R8": r8,
        }
        hit = [f"{code} {name}" for code, name in RULES if flags[code]]
        p_max = max(ps) if ps else 0.0
        p_mean = sum(ps) / len(ps) if ps else 0.0
        score_rule = len(hit) / N_RULES
        risk = W_MODEL * p_max + W_RULE * score_rule
        rep = deid.get(best_sid, {})
        rows.append({
            "author_id": author_id,
            "source": source,
            "n": len(sents),
            "p_max": round(p_max, 6),
            "p_mean": round(p_mean, 6),
            "n_p50": p50,
            "n_p80": p80,
            "n_c2": n_c2,
            "n_c3": n_c3,
            "aspect_n": {name: aspect_n[name] for name in ASPECTS},
            "aspect_neg": {name: aspect_neg[name] for name in ASPECTS},
            "alt_n": {name: alt_n[name] for name in ALTS},
            "wy_in": wy_in,
            "wy_out": wy_out,
            "w_s": w_s,
            "w_a": w_a,
            "w_o": w_o,
            "neg_n": neg_n,
            "t2": dict(t2),
            "m_mode": mode_or_none(models),
            "date_min": min(dates) if dates else None,
            "date_max": max(dates) if dates else None,
            "rules": hit,
            "n_rules": len(hit),
            "score_model": round(p_max, 6),
            "score_rule": round(score_rule, 6),
            "risk": round(risk, 6),
            "level": level_of(risk),
            "rep_sid": best_sid,
            "rep_text": rep.get("text") or "",
        })

    ids = [r["author_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("作者雜湊碰撞")
    rows.sort(key=lambda r: (-r["risk"], r["source"], r["author_id"]))
    with open(OUT, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def rate(subset):
        if not subset:
            return None
        return sum(1 for r in subset if r["n_c2"] > 0) / len(subset)

    by_level = {lv: [r for r in rows if r["level"] == lv] for lv in ("高", "中", "低")}
    source_level = {
        lv: dict(Counter(r["source"] for r in by_level[lv]))
        for lv in ("高", "中", "低")
    }
    high_rate = rate(by_level["高"])
    low_rate = rate(by_level["低"])
    summary = {
        "n_authors": len(rows),
        "weights": {"model": W_MODEL, "rule": W_RULE},
        "thresholds": {"high_ge": HIGH, "mid_ge": MID, "low_lt": MID},
        "levels": {lv: len(by_level[lv]) for lv in ("高", "中", "低")},
        "source_by_level": source_level,
        "gold_c2_author_rate": {
            "高": high_rate,
            "中": rate(by_level["中"]),
            "低": low_rate,
        },
        "high_gt_low": (high_rate or 0) > (low_rate or 0),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    top = []
    for row in by_level["高"][:20]:
        text = row["rep_text"].replace("\n", " ")
        if len(text) > 160:
            text = text[:160] + "…"
        top.append({
            "author_id": row["author_id"],
            "source": row["source"],
            "n": row["n"],
            "risk": row["risk"],
            "p_max": row["p_max"],
            "n_c2": row["n_c2"],
            "rules": row["rules"],
            "rep_sid": row["rep_sid"],
            "rep_text": text,
        })
    TOP.write_text(json.dumps(top, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["high_gt_low"]:
        raise RuntimeError("高風險作者的金標流失比例沒有高於低風險")
    print(f"wrote {OUT} authors={len(rows)} top20={len(top)}")


if __name__ == "__main__":
    main()
