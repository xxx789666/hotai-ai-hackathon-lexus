"""第二階段：用較強模型（Sonnet）帶上下文複核 Haiku 的標籤。

  python pipeline/verify_churn.py                                      # 複核 Haiku c≥2
  python pipeline/verify_churn.py --min-c 0 --max-c 1 --sources mobile01,ptt   # 補標 Haiku 漏掉的

輸出：data/processed/churn_verified.jsonl（sid + Sonnet 的 c/w/t + 一句理由）
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
OUT = P / "churn_verified.jsonl"

PROMPT = """你是汽車售後服務的輿情標註員，負責複核初標結果。每筆資料有文章標題、前後文，以及用 >>> 標出的目標句。
請只判斷「目標句」（前後文僅供理解）是否透露 Lexus 車主離開 Lexus 原廠（和泰服務廠）保養維修的意圖。

c（流失意圖）：
  0 = 無：中性敘述、詢問、廣告、外廠介紹、改裝加裝配件、購車推薦他牌、談的不是 Lexus 車
  1 = 不滿：抱怨 Lexus 原廠售後或刪減保養項目，但沒有離開原廠的動作或意圖
  2 = 考慮離開：本人考慮改去外廠/自己修/不回原廠，或建議 Lexus 車主改去外廠、自備料，或因售後考慮換掉 Lexus
  3 = 已離開：明確說（自己或具體他人）已改在外廠保養維修、自己動手、不再回原廠，或因售後已賣掉 Lexus
w：s = 自身，a = 建議他人，o = 轉述/泛論
t（原因面向）：價格 / 態度 / 品質 / 等待 / 保固 / 零件 / 其他
r：15 字內理由

只輸出 JSON 陣列：[{"i":編號,"c":0-3,"w":"s|a|o","t":"面向","r":"理由"}]

"""


def load_jsonl(p):
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def build_context(targets):
    """從 sentences.jsonl 取同一文章、同一作者的前 2 句與後 1 句。"""
    need = set(targets)
    ctx = {}
    window = []  # 最近 3 行
    pending = {}  # sid -> 等待下一句
    with open(P / "sentences.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            key = (r["doc_id"], r.get("author"))
            for sid, (k, c) in list(pending.items()):
                if k == key:
                    c["next"] = r["text"]
                del pending[sid]
            if r["sid"] in need:
                prev = [w["text"] for w in window[-2:] if (w["doc_id"], w.get("author")) == key]
                ctx[r["sid"]] = {"title": r["title"], "prev": prev, "text": r["text"], "next": None}
                pending[r["sid"]] = (key, ctx[r["sid"]])
            window = (window + [r])[-3:]
    return ctx


def call_llm(batch, model):
    parts = []
    for i, (sid, c) in enumerate(batch):
        s = f"#{i} 【{c['title'][:40]}】\n"
        s += "".join(f"  {t[:120]}\n" for t in c["prev"])
        s += f">>> {c['text']}\n"
        if c["next"]:
            s += f"  {c['next'][:120]}\n"
        parts.append(s)
    res = subprocess.run(["claude", "-p", "--model", model], input=PROMPT + "\n".join(parts),
                         capture_output=True, text=True, encoding="utf-8", timeout=900,
                         shell=sys.platform == "win32")
    m = re.search(r"\[.*\]", res.stdout, re.S)
    if not m:
        raise ValueError(f"no JSON: {res.stdout[:200]} {res.stderr[:200]}")
    out = []
    for o in json.loads(m.group(0)):
        i = int(o["i"])
        if 0 <= i < len(batch):
            out.append({"sid": batch[i][0], "c": int(o.get("c", 0)), "w": o.get("w"),
                        "t": o.get("t"), "r": o.get("r"), "model": model})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--min-c", type=int, default=2)
    ap.add_argument("--max-c", type=int, default=3)
    ap.add_argument("--sources", default="", help="逗號分隔，如 mobile01,ptt；空白表示全部")
    args = ap.parse_args()
    sources = set(filter(None, args.sources.split(",")))

    done = {r["sid"] for r in load_jsonl(OUT)}
    src = {r["sid"]: r["source"] for r in load_jsonl(P / "aftersales.jsonl")}
    targets = [r["sid"] for r in load_jsonl(P / "churn_labels.jsonl")
               if args.min_c <= r["c"] <= args.max_c and r["sid"] not in done
               and (not sources or src.get(r["sid"]) in sources)]
    ctx = build_context(targets)
    items = [(s, ctx[s]) for s in dict.fromkeys(targets) if s in ctx]
    batches = [items[i:i + args.batch] for i in range(0, len(items), args.batch)]
    print(f"verify {len(items)} sentences in {len(batches)} batches", flush=True)

    n_ok = n_fail = 0
    with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(call_llm, b, args.model) for b in batches]
        for fut in as_completed(futs):
            try:
                for l in fut.result():
                    f.write(json.dumps(l, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += 1
            except Exception as e:
                n_fail += 1
                print(f"batch failed: {e}", flush=True)
            if (n_ok + n_fail) % 5 == 0:
                print(f"{n_ok + n_fail}/{len(batches)} (fail {n_fail})", flush=True)
    print(f"done: ok {n_ok}, fail {n_fail}", flush=True)


if __name__ == "__main__":
    main()
