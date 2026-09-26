"""L5：售後句數 ≥ 2 的作者做 K-means，並對應四個 Persona。

  python pipeline/persona_cluster.py

MANUAL 是判讀結果。空的時候用群心分數自動指派，方便先看剖面再覆寫。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from deidentify import hid, load_salt  # noqa: E402
from label_aspects import ALTS, ASPECTS  # noqa: E402
from verify_churn import load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
OUT = P / "authors_persona.jsonl"
PROFILE = P / "persona_profile.json"
QUOTES = P / "persona_quotes.json"

PERSONAS = ("過保精算派", "品質失望派", "靜默出走者", "口碑建議者")

# 群心判讀（k=4，silhouette 0.210）。分數指派會把四個假設各塞一群，
# 但群 2 只有 2 人、群 3 是低訊號多數，不能當成獨立 Persona。
MANUAL: dict[int, str] = {
    0: "過保精算派",  # 價格、一般外廠、自備料、過保都最高，平均風險 0.70
    1: "其他",  # 態度約 45%、負面約 54%，替代選項與流失分都很低
    2: "其他",  # 2 人，連鎖保養離群，不是口碑建議者
    3: "其他",  # 約四分之三，外廠比例約 1%、平均流失分 0.05
}


def load_rows():
    rows = []
    with open(P / "authors_risk.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def feature_names():
    return (
        [f"asp_{name}" for name in ASPECTS]
        + [f"alt_{name}" for name in ALTS]
        + ["neg", "stance_a", "wy_out", "p_mean", "log_n"]
    )


def vector(row: dict) -> list[float]:
    n = row["n"]
    vals = [row["aspect_n"][name] / n for name in ASPECTS]
    vals += [row["alt_n"][name] / n for name in ALTS]
    vals += [
        row["neg_n"] / n,
        row["w_a"] / n,
        row["wy_out"] / n,
        row["p_mean"],
        math.log(n),
    ]
    return vals


def zscore_columns(mat: np.ndarray) -> np.ndarray:
    mu = mat.mean(axis=0)
    sd = mat.std(axis=0)
    sd[sd < 1e-9] = 1.0
    return (mat - mu) / sd


def persona_scores(profiles: list[dict]) -> np.ndarray:
    """列＝群，欄＝四個 Persona 的相對分數。"""
    keys = [
        "price", "price_neg", "wy_out", "alt_shop", "alt_diy_parts",
        "quality", "quality_neg", "alt_switch", "neg", "stance_a", "alt_diy",
    ]
    mat = np.array([[p[k] for k in keys] for p in profiles], dtype=float)
    z = zscore_columns(mat)
    col = {name: i for i, name in enumerate(keys)}
    scores = np.zeros((len(profiles), len(PERSONAS)))
    for i in range(len(profiles)):
        scores[i, 0] = (
            z[i, col["price"]] + z[i, col["price_neg"]] + z[i, col["wy_out"]]
            + z[i, col["alt_shop"]] + z[i, col["alt_diy_parts"]]
        )
        scores[i, 1] = (
            z[i, col["quality"]] + z[i, col["quality_neg"]]
            + z[i, col["alt_switch"]] + 0.5 * z[i, col["neg"]]
        )
        scores[i, 2] = (
            z[i, col["alt_shop"]] + z[i, col["alt_diy"]] + z[i, col["alt_diy_parts"]]
            - z[i, col["neg"]] - z[i, col["price_neg"]] - z[i, col["quality_neg"]]
        )
        scores[i, 3] = 2 * z[i, col["stance_a"]]
    return scores


def assign(profiles: list[dict]) -> dict[int, str]:
    if MANUAL:
        missing = [p["cluster"] for p in profiles if p["cluster"] not in MANUAL]
        if missing:
            raise RuntimeError(f"MANUAL 缺群號 {missing}")
        return dict(MANUAL)
    from scipy.optimize import linear_sum_assignment

    scores = persona_scores(profiles)
    # 群數可能多於 4：每個 Persona 最多配一群，其餘為其他。
    n_c, n_p = scores.shape
    if n_c <= n_p:
        cost = np.zeros((n_p, n_p))
        cost[:n_c, :] = -scores
        cost[n_c:, :] = 0
        rows, cols = linear_sum_assignment(cost)
        mapping = {}
        for r, c in zip(rows, cols):
            if r < n_c:
                mapping[profiles[r]["cluster"]] = PERSONAS[c]
        return mapping
    row_ind, col_ind = linear_sum_assignment(-scores)
    mapping = {profiles[i]["cluster"]: "其他" for i in range(n_c)}
    for r, c in zip(row_ind, col_ind):
        mapping[profiles[r]["cluster"]] = PERSONAS[c]
    return mapping


def top_keys(counter_mean: dict, k: int = 3):
    return sorted(counter_mean.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def main() -> None:
    rows = load_rows()
    eligible = [r for r in rows if r["n"] >= 2]
    names = feature_names()
    x = np.array([vector(r) for r in eligible], dtype=float)
    scaler = StandardScaler()
    xs = scaler.fit_transform(x)

    k_table = []
    best_k, best_s, best_labels = None, -1.0, None
    for k in range(3, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(xs)
        score = float(silhouette_score(xs, labels))
        k_table.append({"k": k, "silhouette": round(score, 4)})
        if score > best_s:
            best_k, best_s, best_labels = k, score, labels
    print("silhouette", json.dumps(k_table, ensure_ascii=False))
    print(f"best_k={best_k} silhouette={best_s:.4f}")

    hdb_tries = []
    for min_size in (15, 30, 50):
        labels_h = HDBSCAN(min_cluster_size=min_size, min_samples=5, copy=True).fit_predict(xs)
        n_noise = int(np.sum(labels_h == -1))
        clusters = sorted({int(v) for v in labels_h if v >= 0})
        sil = None
        if len(clusters) >= 2 and n_noise < len(labels_h):
            mask = labels_h >= 0
            if len(set(labels_h[mask])) >= 2 and mask.sum() > len(clusters):
                sil = float(silhouette_score(xs[mask], labels_h[mask]))
        hdb_tries.append({
            "min_cluster_size": min_size,
            "n_clusters": len(clusters),
            "n_noise": n_noise,
            "silhouette_non_noise": None if sil is None else round(sil, 4),
        })
    print("hdbscan", json.dumps(hdb_tries, ensure_ascii=False))

    by_cluster = defaultdict(list)
    for row, lab in zip(eligible, best_labels):
        by_cluster[int(lab)].append(row)

    profiles = []
    for lab, members in sorted(by_cluster.items()):
        n_auth = len(members)
        n_sent = sum(m["n"] for m in members)

        def mean_rate(fn):
            return sum(fn(m) for m in members) / n_auth

        aspect_mean = {
            name: mean_rate(lambda m, name=name: m["aspect_n"][name] / m["n"])
            for name in ASPECTS
        }
        alt_mean = {
            name: mean_rate(lambda m, name=name: m["alt_n"][name] / m["n"])
            for name in ALTS
        }
        profiles.append({
            "cluster": lab,
            "n_authors": n_auth,
            "n_sentences": n_sent,
            "share_of_clustered": n_auth / len(eligible),
            "source": dict(Counter(m["source"] for m in members)),
            "risk_mean": mean_rate(lambda m: m["risk"]),
            "p_mean": mean_rate(lambda m: m["p_mean"]),
            "neg": mean_rate(lambda m: m["neg_n"] / m["n"]),
            "stance_a": mean_rate(lambda m: m["w_a"] / m["n"]),
            "wy_out": mean_rate(lambda m: m["wy_out"] / m["n"]),
            "wy_out_author": sum(1 for m in members if m["wy_out"] > 0) / n_auth,
            "price": aspect_mean["價格"],
            "price_neg": mean_rate(lambda m: m["aspect_neg"]["價格"] / m["n"]),
            "quality": aspect_mean["技術品質"],
            "quality_neg": mean_rate(lambda m: m["aspect_neg"]["技術品質"] / m["n"]),
            "alt_shop": alt_mean["一般外廠"],
            "alt_diy": alt_mean["DIY"],
            "alt_diy_parts": alt_mean["自備料"],
            "alt_switch": alt_mean["他牌或換車"],
            "aspect_mean": aspect_mean,
            "alt_mean": alt_mean,
            "top_aspects": top_keys(aspect_mean),
            "top_alts": top_keys(alt_mean),
        })

    mapping = assign(profiles)
    for p in profiles:
        p["persona"] = mapping[p["cluster"]]
    scores = persona_scores(profiles)
    score_table = []
    for i, p in enumerate(profiles):
        score_table.append({
            "cluster": p["cluster"],
            "persona": p["persona"],
            "scores": {PERSONAS[j]: round(float(scores[i, j]), 3) for j in range(4)},
        })

    salt = load_salt()
    sid_author = {}
    for rec in load_jsonl(P / "aftersales.jsonl"):
        sid_author[rec["sid"]] = hid(salt, rec["source"], rec.get("author"))
    pred = {}
    for rec in load_jsonl(P / "churn_r4_all.jsonl"):
        pred[rec["sid"]] = rec
    author_persona = {}
    for row, lab in zip(eligible, best_labels):
        author_persona[row["author_id"]] = (int(lab), mapping[int(lab)])

    def clip_quote(p_churn, aid, rec, cluster=None):
        text = (rec.get("text") or "").replace("\n", " ")
        if len(text) > 180:
            text = text[:180] + "…"
        item = {
            "author_id": aid,
            "source": rec.get("source"),
            "sid": rec["sid"],
            "p_churn": round(p_churn, 4),
            "c": rec.get("c"),
            "t2": rec.get("t2"),
            "text": text,
        }
        if cluster is not None:
            item["cluster"] = cluster
        return item

    by_author = {r["author_id"]: r for r in rows}
    quotes = {f"cluster_{lab}": [] for lab in sorted(by_cluster)}
    seen = defaultdict(set)
    candidates = []
    deid_pos = list(load_jsonl(P / "churn_positives_deid.jsonl"))
    for rec in deid_pos:
        aid = sid_author.get(rec["sid"])
        if aid not in author_persona:
            continue
        pr = pred.get(rec["sid"])
        if not pr:
            continue
        cluster, persona = author_persona[aid]
        candidates.append((float(pr["p_churn"]), aid, persona, cluster, rec))
    candidates.sort(key=lambda t: -t[0])
    for p_churn, aid, persona, cluster, rec in candidates:
        key = f"cluster_{cluster}"
        if aid in seen[key] or len(quotes[key]) >= 5:
            continue
        seen[key].add(aid)
        quotes[key].append(clip_quote(p_churn, aid, rec, cluster))

    # 三個沒有獨立成群的假設：用規則從去識別流失句挑例句，不當成分群標籤。
    hypotheses = {
        "品質失望派": [],
        "靜默出走者": [],
        "口碑建議者": [],
    }
    hyp_n = {name: 0 for name in hypotheses}
    for row in rows:
        if row["n"] < 2:
            continue
        rules = set(row["rules"])
        if "R6 品質失望" in rules and (
            row["alt_n"]["他牌或換車"] > 0 or row["t2"].get("品質", 0) > 0
        ):
            hyp_n["品質失望派"] += 1
        if (
            ("R3 找出口" in rules or "R4 自理" in rules)
            and row["neg_n"] == 0
            and "R2 價格負面" not in rules
            and "R6 品質失望" not in rules
        ):
            hyp_n["靜默出走者"] += 1
        if "R8 帶人走" in rules:
            hyp_n["口碑建議者"] += 1

    def hyp_ok(name, row):
        rules = set(row["rules"])
        if name == "品質失望派":
            return "R6 品質失望" in rules and (
                row["alt_n"]["他牌或換車"] > 0 or row["t2"].get("品質", 0) > 0
            )
        if name == "靜默出走者":
            return (
                ("R3 找出口" in rules or "R4 自理" in rules)
                and row["neg_n"] == 0
                and "R2 價格負面" not in rules
                and "R6 品質失望" not in rules
            )
        return "R8 帶人走" in rules

    hyp_seen = {name: set() for name in hypotheses}
    for p_churn, aid, persona, cluster, rec in candidates:
        row = by_author.get(aid)
        if not row:
            continue
        for name in hypotheses:
            if aid in hyp_seen[name] or len(hypotheses[name]) >= 5:
                continue
            if hyp_ok(name, row):
                hyp_seen[name].add(aid)
                hypotheses[name].append(clip_quote(p_churn, aid, rec, cluster))
    quotes["rule_hypotheses"] = hypotheses

    payload = {
        "n_authors": len(rows),
        "n_clustered": len(eligible),
        "clustered_share": len(eligible) / len(rows) if rows else 0,
        "min_sentences": 2,
        "features": names,
        "k_table": k_table,
        "best_k": best_k,
        "best_silhouette": best_s,
        "hdbscan": hdb_tries,
        "manual": bool(MANUAL),
        "mapping_note": "只有群 0 對得上過保精算派；其餘三個假設沒有獨立成群",
        "hypothesis_n_ge2": hyp_n,
        "score_table": score_table,
        "profiles": profiles,
    }
    PROFILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    QUOTES.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(OUT, "w", encoding="utf-8") as f:
        for row, lab in zip(eligible, best_labels):
            rec = {
                "author_id": row["author_id"],
                "cluster": int(lab),
                "persona": mapping[int(lab)],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    counts = Counter(mapping[int(lab)] for lab in best_labels)
    print("persona_counts", json.dumps(counts, ensure_ascii=False))
    print(f"wrote {OUT} clustered={len(eligible)}/{len(rows)}")


if __name__ == "__main__":
    main()
