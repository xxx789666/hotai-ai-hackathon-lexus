"""L2b–2d：對售後句標面向＋情緒、替代選項、車主特徵（帶前後文）。

  python pipeline/label_aspects.py --sample 600 --model sonnet --out aspect_pilot_sonnet.jsonl
  python pipeline/label_aspects.py --sample 600 --model haiku  --out aspect_pilot_haiku.jsonl
  python pipeline/label_aspects.py                                    # 全量（可中斷續跑）

輸出：data/processed/aspect_labels.jsonl（預設）
  a   面向（多選）      s  對 Lexus 原廠的情緒 -1/0/1，無關則省略
  alt 替代選項（多選）  m  車型  age 車齡(年)  km 里程  wy 保固 in/out  rg 地區  nu 新/二手 n/u
"""
import argparse
import json
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_churn import build_context, load_jsonl  # noqa: E402

P = Path(__file__).resolve().parent.parent / "data/processed"

ASPECTS = ["價格", "報價透明", "態度", "技術品質", "等待預約", "保固延保", "零件供應", "便利設施", "銷售交車"]
ALTS = ["一般外廠", "技師開業", "連鎖保養", "DIY", "自備料", "他牌或換車"]
MODELS = ["ES", "RX", "NX", "UX", "IS", "LS", "LM", "LX", "GX", "CT", "GS", "RC", "LBX", "TX", "其他"]

PROMPT = f"""你是汽車售後服務的輿情標註員。每筆資料有文章標題、前後文，以及用 >>> 標出的目標句（台灣論壇 PTT/Mobile01/Dcard）。
只標「目標句」，前後文與標題僅用來理解語境和補足車主資訊。

欄位（沒有就省略該欄位，不要輸出 null）：
- a：目標句談到的售後面向，可多選，限用：{" / ".join(ASPECTS)}
    價格＝保養維修費用高低；報價透明＝被推銷加項、報價不清、被當盤子；技術品質＝修不好、誤判、異音查不出、施工瑕疵；
    便利設施＝據點遠近、代步車、接送、休息室；零件供應＝等料、缺料、零件貴或難買（舊件被丟、被換走算態度或報價透明）；
    銷售交車＝買車、交車、業務；車子故障本身和原廠怎麼處理它算技術品質或保固延保
    純粹車況描述、閒聊、改裝、與售後無關 → a 省略
- s：目標句對 Lexus 原廠（和泰服務廠）售後的情緒，-1 負面 / 0 中性 / 1 正面；沒談到 Lexus 原廠就省略
- alt：目標句提到車主（本人或被建議者）改用、考慮或推薦的替代選項，可多選，限用：{" / ".join(ALTS)}
    技師開業＝原廠出身技師開的店；連鎖保養＝車麗屋、旭益、輪胎連鎖等；自備料＝自己買機油零件請廠家換；
    他牌或換車＝因售後換掉 Lexus 或轉投他牌
    必須是「取代 Lexus 原廠保養維修」的選項，以下都不算：
      只提到外廠名稱、地址、廣告；購車時比較或推薦他牌車款；改裝、加裝配件、貼膜鍍膜；談的不是 Lexus 車
- 車主特徵（目標句、前後文或標題有明確提到才填，不要推測）：
    m 車型，限用：{" / ".join(MODELS)}
    age 車齡（年，整數）；km 里程（公里，整數，「12 萬」→120000）
    wy 保固狀態 in（保固內）/ out（已過保）
    rg 地區（縣市，如 台北、台中、高雄）
    nu 新車 n / 二手 u

只輸出一個 JSON 陣列，每筆一個物件，例如：
[{{"i":0,"a":["價格"],"s":-1,"alt":["一般外廠"],"m":"ES","age":7,"wy":"out"}},{{"i":1}}]

"""


def clean(o):
    out = {}
    a = [x for x in (o.get("a") or []) if x in ASPECTS]
    if a:
        out["a"] = a
    if o.get("s") in (-1, 0, 1):
        out["s"] = o["s"]
    alt = [x for x in (o.get("alt") or []) if x in ALTS]
    if alt:
        out["alt"] = alt
    if o.get("m") in MODELS:
        out["m"] = o["m"]
    for k in ("age", "km"):
        try:
            if o.get(k) is not None:
                out[k] = int(o[k])
        except (TypeError, ValueError):
            pass
    if o.get("wy") in ("in", "out"):
        out["wy"] = o["wy"]
    if isinstance(o.get("rg"), str) and o["rg"]:
        out["rg"] = o["rg"][:6]
    if o.get("nu") in ("n", "u"):
        out["nu"] = o["nu"]
    return out


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
                         capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
                         shell=sys.platform == "win32")
    m = re.search(r"\[.*\]", res.stdout, re.S)
    if not m:
        raise ValueError(f"no JSON: {res.stdout[:200]} {res.stderr[:200]}")
    out = []
    for o in json.loads(m.group(0)):
        i = int(o["i"])
        if 0 <= i < len(batch):
            out.append({"sid": batch[i][0], **clean(o), "model": model})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--out", default="aspect_labels.jsonl")
    args = ap.parse_args()
    out_path = P / args.out

    sids = [r["sid"] for r in load_jsonl(P / "aftersales.jsonl")]
    if args.sample:
        random.seed(42)
        sids = random.sample(sids, args.sample)
    done = {r["sid"] for r in load_jsonl(out_path)}
    todo = [s for s in sids if s not in done]
    ctx = build_context(todo)
    items = [(s, ctx[s]) for s in todo if s in ctx]
    batches = [items[i:i + args.batch] for i in range(0, len(items), args.batch)]
    print(f"todo {len(items)} sentences in {len(batches)} batches", flush=True)

    n_ok = n_fail = 0
    with open(out_path, "a", encoding="utf-8") as f, ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(call_llm, b, args.model) for b in batches]
        for fut in as_completed(futs):
            try:
                for l in fut.result():
                    f.write(json.dumps(l, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += 1
            except Exception as e:  # 失敗的批次留待下次續跑
                n_fail += 1
                print(f"batch failed: {e}", flush=True)
                if "session limit" in str(e):  # 額度用完：取消其餘批次，重置後再續跑
                    for x in futs:
                        x.cancel()
                    print("hit session limit, stopping", flush=True)
                    break
            if (n_ok + n_fail) % 5 == 0:
                print(f"{n_ok + n_fail}/{len(batches)} (fail {n_fail})", flush=True)
    print(f"done: ok {n_ok}, fail {n_fail}", flush=True)


if __name__ == "__main__":
    main()
