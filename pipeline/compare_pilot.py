"""比較兩個模型的試標結果（以第一個為參考），決定全量用哪個模型。

  python pipeline/compare_pilot.py aspect_pilot_sonnet.jsonl aspect_pilot_haiku.jsonl
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_churn import load_jsonl  # noqa: E402

P = Path(__file__).resolve().parent.parent / "data/processed"


def prf(ref, hyp, key):
    tp = fp = fn = 0
    for sid in ref.keys() & hyp.keys():
        r, h = set(ref[sid].get(key, [])), set(hyp[sid].get(key, []))
        tp += len(r & h)
        fp += len(h - r)
        fn += len(r - h)
    p = tp / (tp + fp) if tp + fp else 0
    rc = tp / (tp + fn) if tp + fn else 0
    return p, rc, 2 * p * rc / (p + rc) if p + rc else 0


def main():
    ref = {r["sid"]: r for r in load_jsonl(P / sys.argv[1])}
    hyp = {r["sid"]: r for r in load_jsonl(P / sys.argv[2])}
    common = ref.keys() & hyp.keys()
    print(f"ref {len(ref)} / hyp {len(hyp)} / common {len(common)}")

    for name, d in [("ref", ref), ("hyp", hyp)]:
        print(f"\n[{name}]")
        print(" 面向", Counter(x for r in d.values() for x in r.get("a", [])).most_common())
        print(" 無面向", sum(1 for r in d.values() if not r.get("a")))
        print(" 情緒", Counter(r.get("s") for r in d.values()).most_common())
        print(" 替代", Counter(x for r in d.values() for x in r.get("alt", [])).most_common())
        for k in ("m", "age", "km", "wy", "rg", "nu"):
            print(f" {k} 有值 {sum(1 for r in d.values() if k in r)}", end="")
        print()

    print("\n[hyp 對 ref]  P / R / F1")
    for k in ("a", "alt"):
        print(f" {k}: " + " / ".join(f"{x:.2f}" for x in prf(ref, hyp, k)))
    for k in ("s", "m", "wy", "nu"):
        both = [s for s in common if k in ref[s] or k in hyp[s]]
        agree = sum(1 for s in both if ref[s].get(k) == hyp[s].get(k))
        print(f" {k}: 一致 {agree}/{len(both)}")


if __name__ == "__main__":
    main()
