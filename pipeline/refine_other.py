"""把流失句 t=其他 細分成明確面向。

  python pipeline/refine_other.py
輸出：data/processed/churn_other_refined.jsonl（sid, t2, r2, model）
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_churn import CURSOR_AGENT, build_context, load_jsonl  # noqa: E402

P = Path(__file__).resolve().parent.parent / "data/processed"
OUT = P / "churn_other_refined.jsonl"

# 9 個既有面向（名稱對齊流失標的 t，避免品質/技術品質拆成兩類）＋ 3 個新類。
LABELS = {
    "價格": "保養維修費用高低，覺得原廠貴而離開或建議去外廠。",
    "報價透明": "被推銷加項、報價不清、被當盤子，重點不是單價本身。",
    "態度": "服務態度差、被敷衍、被嫌棄或不耐煩。",
    "品質": "修不好、誤判、異音查不出、施工瑕疵。",
    "等待": "預約久、現場等太久，或店家太忙。",
    "保固": "保固拒賠、過保爭議，或保固內外待遇不同。",
    "零件": "等料、缺料、零件貴或難買。",
    "便利設施": "據點遠近、沒有代步車、接送或休息室。",
    "銷售交車": "買車、交車或業務體驗，因而不再回原廠或考慮換牌。",
    "信任破裂": "整體不再信任原廠或和泰體系，沒有落到上面任何一個單一面向。",
    "非售後原因": "換車需求、配備功能或品牌形象，不是售後體驗造成的離開。",
    "無明確原因": "只說去外廠、推薦或詢問保養廠，沒有說明為什麼離開原廠。",
}

PROMPT = """你是汽車售後服務的輿情標註員。每筆資料有文章標題、前後文、用 >>> 標出的目標句，以及「面向提示」。
面向提示是既有標註，僅供參考，可以不同意。
目標句已被判定有離開 Lexus 原廠（和泰服務廠）的意圖，但原因被標成「其他」。請只依目標句（前後文僅供理解）把原因分成下列恰好一類：
""" + "\n".join(f"  {k}＝{v}" for k, v in LABELS.items()) + """

只輸出 JSON 陣列：[{"i":編號,"t2":"類別","r2":"15字內理由"}]

"""


def call_llm(batch, model):
    parts = []
    for i, (sid, c) in enumerate(batch):
        s = f"#{i} 【{c['title'][:40]}】\n"
        s += "".join(f"  {t[:120]}\n" for t in c["prev"])
        s += f">>> {c['text']}\n"
        if c["next"]:
            s += f"  {c['next'][:120]}\n"
        hint = "、".join(c.get("aspects") or []) or "（無）"
        s += f"面向提示（僅供參考）：{hint}\n"
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
            t2 = o.get("t2")
            if t2 not in LABELS:
                t2 = "無明確原因"
            out.append({"sid": batch[i][0], "t2": t2, "r2": o.get("r2"), "model": model})
    return out


def main():
    model = "gpt-5.6-sol-high"
    done = {r["sid"] for r in load_jsonl(OUT)}
    aspects = {r["sid"]: r.get("a") or [] for r in load_jsonl(P / "aspect_labels.jsonl")}
    targets = [r["sid"] for r in load_jsonl(P / "churn_positives.jsonl")
               if r.get("t") == "其他" and r["sid"] not in done]
    ctx = build_context(targets)
    items = []
    for s in dict.fromkeys(targets):
        if s not in ctx:
            continue
        ctx[s]["aspects"] = aspects.get(s) or []
        items.append((s, ctx[s]))
    batches = [items[i:i + 40] for i in range(0, len(items), 40)]
    print(f"refine {len(items)} sentences in {len(batches)} batches", flush=True)

    n_ok = n_fail = 0
    with open(OUT, "a", encoding="utf-8") as f, ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(call_llm, b, model) for b in batches]
        for fut in as_completed(futs):
            try:
                for row in fut.result():
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
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
