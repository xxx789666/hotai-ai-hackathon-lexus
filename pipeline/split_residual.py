"""把 t2=無明確原因 再細分為出路類型，並標出疑似誤標。

  python pipeline/split_residual.py
輸出：data/processed/churn_residual_split.jsonl（sid, t3, r3, model）
可中斷續跑：已寫入的 sid 會跳過。
"""
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_churn import CURSOR_AGENT, build_context, load_jsonl  # noqa: E402

P = Path(__file__).resolve().parent.parent / "data/processed"
OUT = P / "churn_residual_split.jsonl"
LOG = P / "split_run.log"
MODEL = "gpt-5.6-sol-high"

# 定稿後不得改。不在表內的值歸「無明確原因」。
LABELS = {
    "外廠詢問": "詢問哪裡有推薦的外廠、技師或保養廠，或問某類非原廠通路能不能修，沒講為何不回原廠。",
    "外廠推薦": "推薦具體外廠或技師；說自己在外廠或民間保養廠保養（可不點名）；或只建議改去外廠、說外面就能處理，沒講原因。",
    "自行處理": "明確以 DIY、自備料或自己修作為保養維修做法，沒講原因。一次性、看不出離開原廠的小技巧不算本類。",
    "離開品牌": "已賣掉、建議賣掉或換掉 Lexus，沒講售後原因。",
    "疑似誤標": "目標句連同前後文看不出任何離開 Lexus 原廠保養維修的意圖，例如回原廠流程、純故障描述，或「或者買烤漆筆塗一塗」這類小技巧。",
    "無明確原因": "上述都不是，真正沒有資訊。",
}

PROMPT = """你是汽車售後服務的輿情標註員。每筆資料有文章標題、前後文、用 >>> 標出的目標句，以及「替代選項提示」。
替代選項提示是既有標註，僅供參考，可以不同意。
這些目標句先前被歸為「無明確原因」。請只依目標句（前後文僅供理解指代）分成下列恰好一類：
""" + "\n".join(f"  {k}＝{v}" for k, v in LABELS.items()) + """

先看目標句連同前後文是否完全看不出「離開 Lexus 原廠保養維修」的意圖，若是則標「疑似誤標」。
否則只在外廠詢問、外廠推薦、自行處理、離開品牌、無明確原因中選一類。不要判回價格、品質、態度等其他原因。
只輸出 JSON 陣列：[{"i":編號,"t3":"類別","r3":"15字內理由"}]

"""


def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def call_llm(batch, model):
    parts = []
    for i, (sid, c) in enumerate(batch):
        s = f"#{i} 【{c['title'][:40]}】\n"
        s += "".join(f"  {t[:120]}\n" for t in c["prev"])
        s += f">>> {c['text']}\n"
        if c["next"]:
            s += f"  {c['next'][:120]}\n"
        hint = "、".join(c.get("alt") or []) or "（無）"
        s += f"替代選項提示（僅供參考，可不同意）：{hint}\n"
        parts.append(s)
    prompt = PROMPT + "\n".join(parts)
    cmd = [CURSOR_AGENT, "-p", "--model", model, "--output-format", "text", "--mode", "ask", "--trust"]
    res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                         timeout=900, shell=sys.platform == "win32")
    m = re.search(r"\[.*\]", res.stdout, re.S)
    if not m:
        raise ValueError(f"no JSON: {res.stdout[:200]} {res.stderr[:200]}")
    out = []
    for o in json.loads(m.group(0)):
        i = int(o["i"])
        if 0 <= i < len(batch):
            t3 = o.get("t3")
            if t3 not in LABELS:
                t3 = "無明確原因"
            out.append({"sid": batch[i][0], "t3": t3, "r3": o.get("r3"), "model": model})
    if not out:
        raise ValueError("empty batch")
    return out


def pending_items():
    done = {r["sid"] for r in load_jsonl(OUT)}
    alts = {r["sid"]: r.get("alt") or [] for r in load_jsonl(P / "aspect_labels.jsonl")}
    targets = [r["sid"] for r in load_jsonl(P / "churn_other_refined.jsonl")
               if r.get("t2") == "無明確原因" and r["sid"] not in done]
    ctx = build_context(targets)
    items = []
    for s in dict.fromkeys(targets):
        if s not in ctx:
            continue
        ctx[s]["alt"] = alts.get(s) or []
        items.append((s, ctx[s]))
    return items


def main():
    t0 = time.time()
    log(f"start model={MODEL} workers=4 batch=40")
    total_fail = 0
    for round_i in range(1, 4):
        items = pending_items()
        if not items:
            break
        batches = [items[i:i + 40] for i in range(0, len(items), 40)]
        log(f"round {round_i}: {len(items)} sentences in {len(batches)} batches")
        n_ok = n_fail = 0
        with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(4) as ex:
            futs = [ex.submit(call_llm, b, MODEL) for b in batches]
            for fut in as_completed(futs):
                try:
                    rows = fut.result()
                    for row in rows:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    n_ok += 1
                except Exception as e:
                    n_fail += 1
                    log(f"batch failed: {e}")
                if (n_ok + n_fail) % 5 == 0 or (n_ok + n_fail) == len(batches):
                    log(f"{n_ok + n_fail}/{len(batches)} (fail {n_fail})")
        total_fail += n_fail
        if n_fail == 0 and n_ok == len(batches):
            # 仍可能有漏列的 i，下一輪補
            pass
    left = len(pending_items())
    elapsed = time.time() - t0
    log(f"done: fail_batches {total_fail}, left {left}, seconds {elapsed:.0f}")


if __name__ == "__main__":
    main()
