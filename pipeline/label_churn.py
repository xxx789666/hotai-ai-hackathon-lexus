"""用 LLM（claude -p，Haiku）對售後相關句子粗標流失意圖。

用法：
  python pipeline/label_churn.py --sample 600       # 隨機試標
  python pipeline/label_churn.py                    # 全量（可中斷續跑）
輸出：data/processed/churn_labels.jsonl（每句一行：sid + 標籤）
"""
import argparse
import json
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data/processed/aftersales.jsonl"
OUT = ROOT / "data/processed/churn_labels.jsonl"

PROMPT = """你是汽車售後服務的輿情標註員。以下是台灣論壇（PTT、Mobile01、Dcard）中含售後關鍵詞的句子，每句附上所在文章標題作為語境。
請判斷每句是否透露「Lexus 車主離開 Lexus 原廠（和泰服務廠）保養維修」的意圖。標準要嚴：句子本身沒有明確訊號就標 0。

欄位定義：
- c（流失意圖）：
  0 = 無：中性敘述、詢問資訊、稱讚原廠、新聞廣告、車況描述、改裝或加裝配件、購車比較推薦他牌、與 Lexus 原廠售後無關
  1 = 不滿：抱怨 Lexus 原廠售後（價格貴、態度差、修不好、等太久、保固拒賠），或刪減原廠保養項目，但沒表示要離開原廠
  2 = 考慮離開：本人考慮改去外廠/自己修/不回原廠，或建議別人 Lexus 保養維修改去外廠、自備料，或因售後考慮換掉 Lexus
  3 = 已離開：明確說已改在外廠保養維修、自己動手、不再回原廠，或因售後已賣掉 Lexus 換車
- w（說話立場）：s = 自身經驗或打算，a = 建議他人，o = 轉述或泛論
- b（品牌）：L = 談 Lexus/和泰，X = 談其他品牌，U = 無法判斷
- t（面向，限用這幾個詞）：價格 / 態度 / 品質 / 等待 / 保固 / 零件 / 銷售 / 其他 / 無

判斷原則：
- 只提到外廠、副廠、師傅或費用數字，沒有離開原廠的動作或意圖 → 0
- 談其他品牌車的保養（b=X）→ c 最多 1
- 買車時推薦別的車款、中古車比價 → 0
- 例：「過保就去外廠了，便宜一半」→ c=3,w=s；「原廠處理不好就去外廠」→ c=2,w=a；「保養一次一萬多真的貴」→ c=1；「高雄市 賓豐保養廠」→ 0；「原廠技師開業」→ 0

只輸出一個 JSON 陣列，不要其他文字，每句一個物件：{"i":編號,"c":0-3,"w":"s|a|o","b":"L|X|U","t":"面向"}

句子：
"""


def load_jsonl(p):
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def call_llm(batch, model):
    lines = [f'{i}. 【{r["title"][:40]}】{r["text"]}' for i, r in enumerate(batch)]
    prompt = PROMPT + "\n".join(lines)
    res = subprocess.run(["claude", "-p", "--model", model], input=prompt, capture_output=True,
                         text=True, encoding="utf-8", timeout=600, shell=sys.platform == "win32")
    m = re.search(r"\[.*\]", res.stdout, re.S)
    if not m:
        raise ValueError(f"no JSON in output: {res.stdout[:200]} {res.stderr[:200]}")
    out = []
    for o in json.loads(m.group(0)):
        i = int(o["i"])
        if 0 <= i < len(batch):
            out.append({"sid": batch[i]["sid"], "c": int(o.get("c", 0)), "w": o.get("w"),
                        "b": o.get("b"), "t": o.get("t"), "model": model})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--batch", type=int, default=60)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default="haiku")
    args = ap.parse_args()

    rows = load_jsonl(IN)
    done = {r["sid"] for r in load_jsonl(OUT)}
    if args.sample:
        random.seed(42)
        rows = random.sample(rows, args.sample)
    todo = [r for r in rows if r["sid"] not in done]
    batches = [todo[i:i + args.batch] for i in range(0, len(todo), args.batch)]
    print(f"todo {len(todo)} sentences in {len(batches)} batches", flush=True)

    n_ok = n_fail = 0
    with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(call_llm, b, args.model): b for b in batches}
        for fut in as_completed(futs):
            try:
                labels = fut.result()
                for l in labels:
                    f.write(json.dumps(l, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += 1
            except Exception as e:  # 失敗的批次留待下次續跑
                n_fail += 1
                print(f"batch failed: {e}", flush=True)
            if (n_ok + n_fail) % 10 == 0:
                print(f"{n_ok + n_fail}/{len(batches)} batches (fail {n_fail})", flush=True)
    print(f"done: ok {n_ok}, fail {n_fail}", flush=True)


if __name__ == "__main__":
    main()
