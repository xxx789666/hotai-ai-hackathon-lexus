"""把 Sonnet 判定 c≥2 的句子匯出成 churn_positives.jsonl，並印出分布。"""
import json
from collections import Counter
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "data/processed"


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    sents = {r["sid"]: r for r in load_jsonl(P / "aftersales.jsonl")}
    haiku = {r["sid"]: r["c"] for r in load_jsonl(P / "churn_labels.jsonl")}
    verified = {r["sid"]: r for r in load_jsonl(P / "churn_verified.jsonl")}  # 後寫的覆蓋先寫的

    refined = {}
    refined_path = P / "churn_other_refined.jsonl"
    if refined_path.exists():
        refined = {r["sid"]: r["t2"] for r in load_jsonl(refined_path)}

    residual = {}
    residual_path = P / "churn_residual_split.jsonl"
    if residual_path.exists():
        residual = {r["sid"]: r["t3"] for r in load_jsonl(residual_path)}

    pos = []
    for sid, v in verified.items():
        if v["c"] >= 2:
            t = v["t"]
            if t != "其他":
                t2 = t
            else:
                t2 = refined.get(sid, "其他")
            row = {**sents[sid], "c": v["c"], "w": v["w"], "t": t, "r": v["r"],
                   "haiku_c": haiku.get(sid), "t2": t2}
            if t2 == "無明確原因" and sid in residual:
                row["t2_prev"] = t2
                row["t2"] = residual[sid]
            pos.append(row)
    pos.sort(key=lambda p: (p["source"], p["doc_id"], p["pos"]))
    with open(P / "churn_positives.jsonl", "w", encoding="utf-8") as f:
        for p in pos:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"verified {len(verified)} / positives {len(pos)} / docs {len({p['doc_id'] for p in pos})}")
    for name, key in [("來源", "source"), ("Haiku 原標", "haiku_c"), ("c", "c"), ("立場", "w"),
                      ("面向", "t"), ("細分", "t2"), ("位置", "role")]:
        print(name, Counter(p[key] for p in pos).most_common())
    print("年份", sorted(Counter((p["date"] or "????")[:4] for p in pos).items()))


if __name__ == "__main__":
    main()
