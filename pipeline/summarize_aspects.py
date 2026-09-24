"""彙整 L2b–2d 標註：整體分布，以及和流失意圖（Sonnet c≥2）的交叉。"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_churn import load_jsonl  # noqa: E402

P = Path(__file__).resolve().parent.parent / "data/processed"


def main():
    sents = {r["sid"]: r for r in load_jsonl(P / "aftersales.jsonl")}
    lab = {r["sid"]: r for r in load_jsonl(P / "aspect_labels.jsonl")}
    churn = {r["sid"]: r["c"] for r in load_jsonl(P / "churn_verified.jsonl")}
    pos = {s for s, c in churn.items() if c >= 2}
    print(f"售後句 {len(sents)} / 已標 {len(lab)} / 缺 {len(sents.keys() - lab.keys())}")

    for name, rows in [("全部", lab.values()), ("流失 c≥2", [lab[s] for s in pos if s in lab])]:
        rows = list(rows)
        print(f"\n[{name}] {len(rows)} 句")
        print(" 面向", Counter(x for r in rows for x in r.get("a", [])).most_common())
        print(" 情緒", Counter(r.get("s") for r in rows).most_common())
        print(" 替代", Counter(x for r in rows for x in r.get("alt", [])).most_common())
        print(" 車型", Counter(r.get("m") for r in rows if r.get("m")).most_common())
        print(" 保固", Counter(r.get("wy") for r in rows if r.get("wy")).most_common())

    print("\n[面向 × 負面比例／流失比例]")
    for a in sorted({x for r in lab.values() for x in r.get("a", [])}):
        sids = [s for s, r in lab.items() if a in r.get("a", [])]
        neg = sum(1 for s in sids if lab[s].get("s") == -1)
        ch = sum(1 for s in sids if s in pos)
        print(f" {a:6} {len(sids):5}  負面 {neg / len(sids):.0%}  流失 {ch / len(sids):.0%}")

    print("\n[來源 × 已標]", Counter(sents[s]["source"] for s in lab).most_common())


if __name__ == "__main__":
    main()
