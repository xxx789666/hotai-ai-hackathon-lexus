"""比較 jev-local / Haiku 與 Sonnet。輸出指標 JSON 到 stdout。

  python local_jev/evaluate.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from label_aspects import ALTS, ASPECTS  # noqa: E402
from verify_churn import load_jsonl  # noqa: E402

P = ROOT / "data/processed"


def last_by_sid(path: Path) -> dict:
    last = {}
    for r in load_jsonl(path):
        last[r["sid"]] = r
    return last


def cohen_kappa(pairs, labels) -> float:
    n = len(pairs)
    if n == 0:
        return 0.0
    mat = {(a, b): 0 for a in labels for b in labels}
    for a, b in pairs:
        mat[(a, b)] += 1
    po = sum(mat[(x, x)] for x in labels) / n
    pe = 0.0
    for x in labels:
        row = sum(mat[(x, y)] for y in labels) / n
        col = sum(mat[(y, x)] for y in labels) / n
        pe += row * col
    if abs(1 - pe) < 1e-12:
        return 1.0
    return (po - pe) / (1 - pe)


def prf_counts(tp, fp, fn) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def multilabel(ref, hyp, key, labels, threshold_key=None, threshold=0.5) -> dict:
    per = {}
    tp = fp = fn = 0
    for lab in labels:
        tpi = fpi = fni = 0
        for sid in ref.keys() & hyp.keys():
            if threshold_key and threshold_key in hyp[sid]:
                hset = {k for k, v in hyp[sid][threshold_key].items() if v >= threshold}
            else:
                hset = set(hyp[sid].get(key) or [])
            rset = set(ref[sid].get(key) or [])
            if lab in rset and lab in hset:
                tpi += 1
            elif lab in hset:
                fpi += 1
            elif lab in rset:
                fni += 1
        per[lab] = prf_counts(tpi, fpi, fni)
        tp += tpi
        fp += fpi
        fn += fni
    micro = prf_counts(tp, fp, fn)
    f1s = [per[lab]["f1"] for lab in labels]
    return {
        "per_label": per,
        "micro_f1": micro["f1"],
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "micro": micro,
    }


def binary_c(pairs) -> dict:
    labels = [0, 1]
    agree = sum(a == b for a, b in pairs) / len(pairs) if pairs else 0.0
    tp = sum(a == 1 and b == 1 for a, b in pairs)
    fp = sum(a == 0 and b == 1 for a, b in pairs)
    fn = sum(a == 1 and b == 0 for a, b in pairs)
    tn = sum(a == 0 and b == 0 for a, b in pairs)
    return {
        "n": len(pairs),
        "agreement": agree,
        "kappa": cohen_kappa(pairs, labels),
        "prf": prf_counts(tp, fp, fn),
        "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def field_agreement(ref, hyp, key) -> dict:
    both = [s for s in ref.keys() & hyp.keys() if key in ref[s]]
    agree = sum(1 for s in both if ref[s].get(key) == hyp[s].get(key))
    return {"n": len(both), "agreement": agree / len(both) if both else 0.0}


def single_label_prf(ref, hyp, key, labels) -> dict:
    per = {}
    tp = fp = fn = 0
    agree_n = 0
    common = list(ref.keys() & hyp.keys())
    for sid in common:
        rv = ref[sid].get(key)
        hv = hyp[sid].get(key)
        if rv == hv:
            agree_n += 1
    for lab in labels:
        tpi = fpi = fni = 0
        for sid in common:
            rv = ref[sid].get(key)
            hv = hyp[sid].get(key)
            if rv == lab and hv == lab:
                tpi += 1
            elif hv == lab and rv != lab:
                fpi += 1
            elif rv == lab and hv != lab:
                fni += 1
        per[str(lab)] = prf_counts(tpi, fpi, fni)
        tp += tpi
        fp += fpi
        fn += fni
    micro = prf_counts(tp, fp, fn)
    return {
        "agreement": agree_n / len(common) if common else 0.0,
        "n": len(common),
        "per_label": per,
        "micro_f1": micro["f1"],
        "macro_f1": sum(v["f1"] for v in per.values()) / len(per) if per else 0.0,
    }


def churn_block(gold, hyp, c_key) -> dict:
    sids = [s for s in gold if s in hyp and c_key in hyp[s]]
    y_g = [int(gold[s]["c"]) for s in sids]
    y_h = [int(hyp[s][c_key]) for s in sids]
    pairs = list(zip(y_g, y_h))
    bin_pairs = [(int(a >= 2), int(b >= 2)) for a, b in pairs]
    cm = Counter(pairs)
    return {
        "n": len(pairs),
        "exact_agreement": sum(a == b for a, b in pairs) / len(pairs) if pairs else 0.0,
        "kappa4": cohen_kappa(pairs, [0, 1, 2, 3]),
        "binary": binary_c(bin_pairs),
        "confusion4": {f"{a}->{b}": cm[(a, b)] for a in range(4) for b in range(4) if cm[(a, b)]},
    }


def reliability(gold, hyp) -> list:
    rows = []
    for lo in (0.0, 0.2, 0.4, 0.6, 0.8):
        hi = lo + 0.2
        bucket = []
        for sid, g in gold.items():
            if sid not in hyp:
                continue
            p = hyp[sid].get("churn_p") or {}
            prob = float(p.get("2", 0)) + float(p.get("3", 0))
            if (prob >= lo and prob < hi) or (hi == 1.0 and prob == 1.0):
                bucket.append(int(g["c"]) >= 2)
        rows.append({
            "bin": f"{lo:.1f}-{hi:.1f}",
            "n": len(bucket),
            "sonnet_c_ge2_rate": (sum(bucket) / len(bucket) if bucket else None),
        })
    return rows


def disagreements(gold, hyp, sentences, k=10) -> list:
    rows = []
    for sid, g in gold.items():
        if sid not in hyp:
            continue
        gs = int(g["c"] >= 2)
        hs = int(int(hyp[sid]["c_expect"]) >= 2)
        if gs == hs:
            continue
        p = hyp[sid].get("churn_p") or {}
        text = (sentences.get(sid) or {}).get("text", "")
        rows.append({
            "sid": sid,
            "text": text[:80],
            "sonnet_c": int(g["c"]),
            "jev_c_expect": hyp[sid]["c_expect"],
            "jev_c_argmax": hyp[sid]["c_argmax"],
            "jev_p_ge2": round(float(p.get("2", 0)) + float(p.get("3", 0)), 4),
            "churn_p": p,
        })
    rows.sort(key=lambda r: abs(r["jev_p_ge2"] - (1 if r["sonnet_c"] >= 2 else 0)), reverse=True)
    return rows[:k]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--jev", default="", help="預測 jsonl；預設 jev_pilot_local.jsonl")
    ap.add_argument("--metrics", default="", help="指標 JSON 輸出路徑")
    ap.add_argument("--gold-c", default="", help="流失金標；預設 churn_verified.jsonl")
    args = ap.parse_args()
    sonnet = last_by_sid(P / "aspect_pilot_sonnet.jsonl")
    haiku = last_by_sid(P / "aspect_pilot_haiku.jsonl")
    jev = last_by_sid(Path(args.jev) if args.jev else P / "jev_pilot_local.jsonl")
    churn = last_by_sid(Path(args.gold_c) if args.gold_c else P / "churn_verified.jsonl")
    if args.gold_c:
        gold_c = {s: churn[s] for s in jev if s in churn}
        sonnet = {s: sonnet.get(s, {}) for s in jev}
    else:
        gold_c = {s: churn[s] for s in sonnet if s in churn}
    sentences = {}
    with open(P / "sentences.jsonl", encoding="utf-8") as f:
        need = set(gold_c)
        for line in f:
            r = json.loads(line)
            if r["sid"] in need:
                sentences[r["sid"]] = r
                if len(sentences) == len(need):
                    break
    thresholds = {}
    for t in (0.3, 0.5, 0.7):
        thresholds[str(t)] = multilabel(sonnet, jev, "a", ASPECTS, "a_p", t)["micro_f1"]
    out = {
        "n_sonnet": len(sonnet),
        "n_jev": len(jev),
        "n_haiku": len(haiku),
        "sid_match": set(sonnet) == set(jev),
        "model": next(iter(jev.values())).get("model") if jev else None,
        "bits": next(iter(jev.values())).get("bits") if jev else None,
        "avg_seconds": (sum(r.get("seconds", 0) for r in jev.values()) / len(jev) if jev else None),
        "churn_expect": churn_block(gold_c, jev, "c_expect"),
        "churn_argmax": churn_block(gold_c, jev, "c_argmax"),
        "reliability": reliability(gold_c, jev),
        "stance": field_agreement(gold_c, jev, "w"),
        "aspects_jev": multilabel(sonnet, jev, "a", ASPECTS),
        "aspects_haiku": multilabel(sonnet, haiku, "a", ASPECTS),
        "aspect_threshold_micro_f1": thresholds,
        "sentiment": field_agreement(sonnet, jev, "s"),
        "alt_jev": multilabel(sonnet, jev, "alt", ALTS),
        "model_jev": single_label_prf(sonnet, jev, "m", ["ES", "RX", "NX", "UX", "IS", "LS", "LM", "LX", "GX", "CT", "GS", "RC", "LBX", "TX", "其他"]),
        "examples": disagreements(gold_c, jev, sentences),
    }
    text = json.dumps(out, ensure_ascii=False, indent=2)
    dest = Path(args.metrics) if args.metrics else P / "jev_pilot_metrics.json"
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest} n_jev={out['n_jev']} sid_match={out['sid_match']}")
    print("churn binary", json.dumps(out["churn_expect"]["binary"], ensure_ascii=False))
    print("aspect micro jev", out["aspects_jev"]["micro_f1"], "haiku", out["aspects_haiku"]["micro_f1"])


if __name__ == "__main__":
    main()
