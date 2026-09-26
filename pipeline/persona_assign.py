"""高／中風險作者的 Persona 規則指派，並用 K-means 做驗證。

  python pipeline/persona_assign.py

母體是 authors_risk.jsonl 裡等級為高或中的作者。低風險作者在
authors_persona.jsonl 標成「低風險」，不參與指派與分群。
不改風險分數。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from deidentify import hid, load_salt  # noqa: E402
from label_aspects import ALTS, ASPECTS  # noqa: E402
from verify_churn import load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
OUT = P / "authors_persona.jsonl"
SUMMARY = P / "persona_assign_summary.json"
QUOTES = P / "persona_assign_quotes.json"

# 初版權重。平手時依 TIE_ORDER 取先出現的名稱。
W_SWITCH = 2
SILENT_HALVE_AFTER_ASPECT_NEG_SENTENCES = 1
TIE_ORDER = ("口碑建議者", "品質失望派", "過保精算派", "靜默出走者")
SILENT_T2 = {"外廠詢問", "外廠推薦", "自行處理"}
SILENT_ALTS = {"一般外廠", "DIY", "技師開業", "連鎖保養"}
T2_FEATS = ["價格", "品質", "外廠詢問", "外廠推薦", "自行處理", "保固", "零件", "態度"]


def last_by_sid(name: str) -> dict:
    out = {}
    for rec in load_jsonl(P / name):
        out[rec["sid"]] = rec
    return out


def blank_parts() -> dict:
    return {
        "口碑_advise": 0,
        "品質_neg": 0,
        "品質_t2": 0,
        "品質_switch": 0,
        "過保_price_neg": 0,
        "過保_wy": 0,
        "過保_t2": 0,
        "過保_parts": 0,
        "靜默_t2": 0,
        "靜默_alt": 0,
        "靜默_neg": 0,
        "靜默_aspect_neg_sent": 0,
        "靜默_halved": False,
    }


def scores_from(parts: dict) -> dict:
    silent = parts["靜默_t2"] + parts["靜默_alt"] - parts["靜默_neg"]
    if parts["靜默_aspect_neg_sent"] > SILENT_HALVE_AFTER_ASPECT_NEG_SENTENCES:
        silent *= 0.5
        parts["靜默_halved"] = True
    return {
        "口碑建議者": float(parts["口碑_advise"]),
        "品質失望派": float(
            parts["品質_neg"] + parts["品質_t2"] + W_SWITCH * parts["品質_switch"]
        ),
        "過保精算派": float(
            parts["過保_price_neg"] + parts["過保_wy"] + parts["過保_t2"] + parts["過保_parts"]
        ),
        "靜默出走者": float(silent),
    }


def assign(scores: dict) -> str:
    best_name = "未分類"
    best = 0.0
    for name in TIE_ORDER:
        value = scores[name]
        if value > best:
            best = value
            best_name = name
    return best_name


def sentence_matches(persona: str, rec: dict) -> bool:
    """代表句要在句子層就符合該 Persona，不只是作者總分高。"""
    aspects = set(rec.get("a") or [])
    alts = set(rec.get("alt") or [])
    sent = rec.get("s")
    t2 = rec.get("t2")
    w = rec.get("w")
    c = rec.get("c")
    p = rec.get("p_churn") or 0
    if persona == "口碑建議者":
        return w == "a" and ((c is not None and int(c) >= 2) or p >= 0.5)
    if persona == "品質失望派":
        return ( "技術品質" in aspects and sent == -1) or t2 == "品質" or "他牌或換車" in alts
    if persona == "過保精算派":
        return (
            ("價格" in aspects and sent == -1)
            or rec.get("wy") == "out"
            or t2 == "價格"
            or "自備料" in alts
        )
    if persona == "靜默出走者":
        return sent != -1 and (t2 in SILENT_T2 or bool(alts & SILENT_ALTS))
    return True


def feature_row(author: dict) -> list[float]:
    n = author["n"]
    vals = [author["aspect_n"][name] / n for name in ASPECTS]
    vals += [author["alt_n"][name] / n for name in ALTS]
    vals += [
        author["neg_n"] / n,
        author["w_a"] / n,
        author["wy_out"] / n,
        author["p_mean"],
        math.log(n),
    ]
    t2 = author.get("t2") or {}
    vals += [t2.get(name, 0) / n for name in T2_FEATS]
    return vals


def feature_names() -> list[str]:
    return (
        [f"asp_{name}" for name in ASPECTS]
        + [f"alt_{name}" for name in ALTS]
        + ["neg", "stance_a", "wy_out", "p_mean", "log_n"]
        + [f"t2_{name}" for name in T2_FEATS]
    )


def main() -> None:
    salt = load_salt()
    authors = []
    by_id = {}
    for rec in load_jsonl(P / "authors_risk.jsonl"):
        authors.append(rec)
        by_id[rec["author_id"]] = rec
    if len(authors) != 6394:
        raise RuntimeError(f"作者數 {len(authors)}，預期 6394")
    focus = [r for r in authors if r["level"] in ("高", "中")]
    focus_ids = {r["author_id"] for r in focus}

    pred = last_by_sid("churn_r4_all.jsonl")
    gold = last_by_sid("churn_verified.jsonl")
    aspects = last_by_sid("aspect_labels.jsonl")
    positives = last_by_sid("churn_positives.jsonl")
    deid_pos = {r["sid"]: r for r in load_jsonl(P / "churn_positives_deid.jsonl")}
    deid_all = {r["sid"]: r for r in load_jsonl(P / "aftersales_deid.jsonl")}

    parts = {aid: blank_parts() for aid in focus_ids}
    seen = set()
    for rec in load_jsonl(P / "aftersales.jsonl"):
        aid = hid(salt, rec["source"], rec.get("author"))
        if aid not in focus_ids:
            continue
        seen.add(aid)
        sid = rec["sid"]
        g = gold.get(sid, {})
        pr = pred[sid]
        asp = aspects.get(sid, {})
        pos = positives.get(sid, {})
        p = float(pr["p_churn"])
        c = g.get("c")
        w = g.get("w")
        names = [a for a in (asp.get("a") or []) if a in ASPECTS]
        alts = {a for a in (asp.get("alt") or []) if a in ALTS}
        sent = asp.get("s")
        t2 = pos.get("t2")
        box = parts[aid]
        if w == "a" and ((c is not None and int(c) >= 2) or p >= 0.5):
            box["口碑_advise"] += 1
        if "技術品質" in names and sent == -1:
            box["品質_neg"] += 1
        if t2 == "品質":
            box["品質_t2"] += 1
        if "他牌或換車" in alts:
            box["品質_switch"] += 1
        if "價格" in names and sent == -1:
            box["過保_price_neg"] += 1
        if asp.get("wy") == "out":
            box["過保_wy"] += 1
        if t2 == "價格":
            box["過保_t2"] += 1
        if "自備料" in alts:
            box["過保_parts"] += 1
        if t2 in SILENT_T2:
            box["靜默_t2"] += 1
        if alts & SILENT_ALTS:
            box["靜默_alt"] += 1
        if sent == -1:
            box["靜默_neg"] += 1
        if sent == -1 and names:
            box["靜默_aspect_neg_sent"] += 1
    missing = focus_ids - seen
    if missing:
        raise RuntimeError(f"高中風險作者對不到句子 {len(missing)}")

    assigned = {}
    for aid in focus_ids:
        sc = scores_from(parts[aid])
        assigned[aid] = {"scores": sc, "persona": assign(sc), "parts": parts[aid]}

    labels_rule = [assigned[r["author_id"]]["persona"] for r in focus]
    x = np.array([feature_row(r) for r in focus], dtype=float)
    xs = StandardScaler().fit_transform(x)
    k_table = []
    labels_k4 = None
    for k in range(3, 7):
        lab = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(xs)
        sil = float(silhouette_score(xs, lab))
        k_table.append({"k": k, "silhouette": round(sil, 4)})
        if k == 4:
            labels_k4 = lab
    ari = float(adjusted_rand_score(labels_rule, labels_k4))
    cluster_of = {r["author_id"]: int(lab) for r, lab in zip(focus, labels_k4)}

    cross = []
    support = {}
    for persona in list(TIE_ORDER) + ["未分類"]:
        members = [aid for aid, row in assigned.items() if row["persona"] == persona]
        counts = Counter(cluster_of[aid] for aid in members)
        row = {"persona": persona, "n": len(members), "clusters": {str(k): counts.get(k, 0) for k in range(4)}}
        if members:
            top_c, top_n = counts.most_common(1)[0]
            share = top_n / len(members)
            row["top_cluster"] = top_c
            row["top_share"] = round(share, 4)
            row["supported"] = share >= 0.60
        else:
            row["top_cluster"] = None
            row["top_share"] = None
            row["supported"] = False
        support[persona] = row["supported"]
        cross.append(row)

    hit = Counter()
    for aid, row in assigned.items():
        pt = row["parts"]
        if pt["口碑_advise"] > 0:
            hit["口碑建議者"] += 1
        if pt["品質_neg"] or pt["品質_t2"] or pt["品質_switch"]:
            hit["品質失望派"] += 1
        if pt["過保_price_neg"] or pt["過保_wy"] or pt["過保_t2"] or pt["過保_parts"]:
            hit["過保精算派"] += 1
        if pt["靜默_t2"] or pt["靜默_alt"]:
            hit["靜默出走者"] += 1

    def mean_rate(members, fn):
        return sum(fn(m) for m in members) / len(members) if members else None

    profiles = []
    for persona in list(TIE_ORDER) + ["未分類"]:
        members = [by_id[aid] for aid, row in assigned.items() if row["persona"] == persona]
        n_auth = len(members)
        if n_auth == 0:
            profiles.append({"persona": persona, "n": 0})
            continue
        aspect_mean = {
            name: mean_rate(members, lambda m, name=name: m["aspect_n"][name] / m["n"])
            for name in ASPECTS
        }
        alt_mean = {
            name: mean_rate(members, lambda m, name=name: m["alt_n"][name] / m["n"])
            for name in ALTS
        }
        t2_mean = Counter()
        for m in members:
            t2_mean.update(m.get("t2") or {})
        profiles.append({
            "persona": persona,
            "n": n_auth,
            "share": n_auth / len(focus),
            "source": dict(Counter(m["source"] for m in members)),
            "level": dict(Counter(m["level"] for m in members)),
            "risk_mean": mean_rate(members, lambda m: m["risk"]),
            "p_mean": mean_rate(members, lambda m: m["p_mean"]),
            "stance_a": mean_rate(members, lambda m: m["w_a"] / m["n"]),
            "wy_out_author": sum(1 for m in members if m["wy_out"] > 0) / n_auth,
            "top_aspects": sorted(aspect_mean.items(), key=lambda kv: (-kv[1], kv[0]))[:3],
            "top_alts": sorted(alt_mean.items(), key=lambda kv: (-kv[1], kv[0]))[:3],
            "top_t2": t2_mean.most_common(3),
            "aspect_mean": aspect_mean,
        })

    # 代表句候選：句子層符合定義、不同作者、p_churn 由高到低。
    buckets = {name: [] for name in list(TIE_ORDER) + ["未分類"]}
    seen_author = {name: set() for name in buckets}
    candidates = []
    for rec in load_jsonl(P / "aftersales.jsonl"):
        aid = hid(salt, rec["source"], rec.get("author"))
        if aid not in assigned:
            continue
        sid = rec["sid"]
        pr = pred[sid]
        g = gold.get(sid, {})
        asp = aspects.get(sid, {})
        pos = positives.get(sid, {})
        deid = deid_pos.get(sid) or deid_all.get(sid) or {}
        candidates.append({
            "author_id": aid,
            "persona": assigned[aid]["persona"],
            "p_churn": float(pr["p_churn"]),
            "c": g.get("c"),
            "w": g.get("w"),
            "s": asp.get("s"),
            "a": asp.get("a") or [],
            "alt": asp.get("alt") or [],
            "wy": asp.get("wy"),
            "t2": pos.get("t2"),
            "source": rec["source"],
            "sid": sid,
            "text": (deid.get("text") or "").replace("\n", " "),
        })
    candidates.sort(key=lambda r: -r["p_churn"])
    for rec in candidates:
        persona = rec["persona"]
        if rec["author_id"] in seen_author[persona] or len(buckets[persona]) >= 12:
            continue
        if persona != "未分類" and not sentence_matches(persona, rec):
            continue
        if not rec["text"]:
            continue
        seen_author[persona].add(rec["author_id"])
        text = rec["text"]
        if len(text) > 180:
            text = text[:180] + "…"
        rec = dict(rec)
        rec["text"] = text
        rec["p_churn"] = round(rec["p_churn"], 4)
        buckets[persona].append(rec)

    with open(OUT, "w", encoding="utf-8") as f:
        for rec in authors:
            aid = rec["author_id"]
            if rec["level"] == "低":
                row = {"author_id": aid, "persona": "低風險", "cluster": None, "level": "低"}
            else:
                row = {
                    "author_id": aid,
                    "persona": assigned[aid]["persona"],
                    "cluster": cluster_of[aid],
                    "level": rec["level"],
                    "scores": {k: round(v, 4) for k, v in assigned[aid]["scores"].items()},
                    "parts": assigned[aid]["parts"],
                }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "n_authors": len(authors),
        "n_focus": len(focus),
        "weights": {
            "switch_x": W_SWITCH,
            "silent_halve_if_aspect_neg_sentences_gt": SILENT_HALVE_AFTER_ASPECT_NEG_SENTENCES,
            "tie_order": list(TIE_ORDER),
        },
        "rule_hit_authors": dict(hit),
        "persona_counts": dict(Counter(labels_rule)),
        "k_table": k_table,
        "ari_k4": round(ari, 4),
        "cross": cross,
        "supported": support,
        "features": feature_names(),
        "profiles": profiles,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    QUOTES.write_text(json.dumps(buckets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "n_focus": len(focus),
        "counts": summary["persona_counts"],
        "hit": summary["rule_hit_authors"],
        "k": k_table,
        "ari": summary["ari_k4"],
        "cross": cross,
    }, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
