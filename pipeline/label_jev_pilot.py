"""600 句本機 LLM2Jev 試標。全程本機 prefill，不呼叫雲端 LLM。

  python pipeline/label_jev_pilot.py
  python pipeline/label_jev_pilot.py --limit 2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

os.environ.setdefault("HF_HOME", r"D:\hf_cache")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from label_aspects import ALTS, ASPECTS, MODELS  # noqa: E402
from verify_churn import build_context, load_jsonl  # noqa: E402

P = ROOT / "data/processed"
OUT = P / "jev_pilot_local.jsonl"
LOG = P / "jev_pilot_run.log"

PRIMARY_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
FALLBACK_MODEL = "Qwen/Qwen3-1.7B"

CHURN_LEVELS = [
    "0 = 無：中性敘述、詢問、廣告、外廠介紹、改裝加裝配件、購車推薦他牌、談的不是 Lexus 車",
    "1 = 不滿：抱怨 Lexus 原廠售後或刪減保養項目，但沒有離開原廠的動作或意圖",
    "2 = 考慮離開：本人考慮改去外廠/自己修/不回原廠，或建議 Lexus 車主改去外廠、自備料，或因售後考慮換掉 Lexus",
    "3 = 已離開：明確說（自己或具體他人）已改在外廠保養維修、自己動手、不再回原廠，或因售後已賣掉 Lexus",
]
STANCE = {
    "s": "s = 自身",
    "a": "a = 建議他人",
    "o": "o = 轉述/泛論",
}
ASPECT_TEXT = {
    "價格": "價格＝保養維修費用高低",
    "報價透明": "報價透明＝被推銷加項、報價不清、被當盤子",
    "態度": "態度（面向名稱即定義；舊件被丟、被換走算態度或報價透明）",
    "技術品質": "技術品質＝修不好、誤判、異音查不出、施工瑕疵；車子故障本身和原廠怎麼處理它算技術品質或保固延保",
    "等待預約": "等待預約（面向名稱即定義）",
    "保固延保": "保固延保；車子故障本身和原廠怎麼處理它算技術品質或保固延保",
    "零件供應": "零件供應＝等料、缺料、零件貴或難買（舊件被丟、被換走算態度或報價透明）",
    "便利設施": "便利設施＝據點遠近、代步車、接送、休息室",
    "銷售交車": "銷售交車＝買車、交車、業務",
}
ALT_TEXT = {
    "一般外廠": "一般外廠",
    "技師開業": "技師開業＝原廠出身技師開的店",
    "連鎖保養": "連鎖保養＝車麗屋、旭益、輪胎連鎖等",
    "DIY": "DIY",
    "自備料": "自備料＝自己買機油零件請廠家換",
    "他牌或換車": "他牌或換車＝因售後換掉 Lexus 或轉投他牌",
}
ALT_EXCLUDE = (
    "必須是「取代 Lexus 原廠保養維修」的選項，以下都不算："
    "只提到外廠名稱、地址、廣告；購車時比較或推薦他牌車款；改裝、加裝配件、貼膜鍍膜；談的不是 Lexus 車"
)
SENTIMENT_LEVELS = ["-1 負面", "0 中性", "1 正面"]
JUDGE = "請只判斷「目標句」（前後文僅供理解）。純粹車況描述、閒聊、改裝、與售後無關則面向不成立。"


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def format_state(c: dict) -> str:
    s = f"【{c['title'][:40]}】\n"
    s += "".join(f"  {t[:120]}\n" for t in c["prev"])
    s += f">>> {c['text']}\n"
    if c["next"]:
        s += f"  {c['next'][:120]}\n"
    return s


def build_questions():
    from llm2jev import Choice, Noul, Score

    q = {
        "churn": Score(
            instructions="c（流失意圖）。" + JUDGE,
            criteria=CHURN_LEVELS,
        ),
        "stance": Choice(
            instructions="w：s = 自身，a = 建議他人，o = 轉述/泛論。" + JUDGE,
            criteria=STANCE,
        ),
        "sentiment": Score(
            instructions="s：目標句對 Lexus 原廠（和泰服務廠）售後的情緒，-1 負面 / 0 中性 / 1 正面；沒談到 Lexus 原廠就省略。" + JUDGE,
            criteria=SENTIMENT_LEVELS,
        ),
        "mentions_lexus": Noul(
            instructions="目標句有沒有談到 Lexus 原廠（和泰服務廠）。沒談到 Lexus 原廠，情緒就不適用。" + JUDGE,
        ),
    }
    for name in ASPECTS:
        q[f"asp_{name}"] = Noul(
            instructions=f"目標句是否談到售後面向「{name}」。{ASPECT_TEXT[name]}。{JUDGE}",
        )
    for name in ALTS:
        q[f"alt_{name}"] = Noul(
            instructions=(
                f"目標句是否提到車主（本人或被建議者）改用、考慮或推薦「{name}」。"
                f"{ALT_TEXT[name]}。{ALT_EXCLUDE}"
            ),
        )
    q["model"] = Choice(
        instructions="m 車型，目標句、前後文或標題有明確提到才選，不要推測；都沒有就選無。限用：" + " / ".join(MODELS),
        criteria={m: m for m in [*MODELS, "無"]},
    )
    return q


def to_record(sid: str, response, model_name: str, bits: int, seconds: float) -> dict:
    churn = response.scores["churn"]
    probs = {str(k): round(float(v), 6) for k, v in churn.probabilities.items()}
    c_argmax = max(range(4), key=lambda i: churn.probabilities[i])
    c_expect = int(min(3, max(0, round(churn.score))))
    stance = response.choices["stance"]
    sent = response.scores["sentiment"]
    mentions = float(response.nouls["mentions_lexus"].noul)
    aspects = []
    aspect_p = {}
    for name in ASPECTS:
        p = float(response.nouls[f"asp_{name}"].noul)
        aspect_p[name] = round(p, 6)
        if p >= 0.5:
            aspects.append(name)
    alts = []
    alt_p = {}
    for name in ALTS:
        p = float(response.nouls[f"alt_{name}"].noul)
        alt_p[name] = round(p, 6)
        if p >= 0.5:
            alts.append(name)
    model_choice = response.choices["model"]
    rec = {
        "sid": sid,
        "c_argmax": c_argmax,
        "c_expect": c_expect,
        "c": c_expect,
        "churn_score": round(float(churn.score), 6),
        "churn_p": probs,
        "w": stance.choice,
        "w_p": {k: round(float(v), 6) for k, v in stance.probabilities.items()},
        "a": aspects,
        "a_p": aspect_p,
        "mentions_lexus": round(mentions, 6),
        "sentiment_score": round(float(sent.score), 6),
        "sentiment_p": {str(k): round(float(v), 6) for k, v in sent.probabilities.items()},
        "alt": alts,
        "alt_p": alt_p,
        "m_choice": model_choice.choice,
        "m_p": {k: round(float(v), 6) for k, v in model_choice.probabilities.items()},
        "model": model_name,
        "bits": bits,
        "seconds": round(seconds, 3),
    }
    if mentions >= 0.5:
        rec["s"] = int(min(2, max(0, round(sent.score)))) - 1
    if model_choice.choice != "無":
        rec["m"] = model_choice.choice
    return rec


def load_backend(model_name: str, load_in_4bit: bool, batch_size: int):
    from local_jev.quant_backend import FourBitTransformersBackend

    log(f"loading {model_name} 4bit={load_in_4bit}")
    backend = FourBitTransformersBackend(
        model_name, batch_size=batch_size, load_in_4bit=load_in_4bit,
    )
    import torch
    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    log(f"loaded bits={backend.bits} vram_gb={vram:.2f}")
    return backend


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--model", default=PRIMARY_MODEL)
    args = ap.parse_args()

    from llm2jev import JevRequest, LLM2Jev

    questions = build_questions()
    pilot = load_jsonl(P / "aspect_pilot_sonnet.jsonl")
    sids = [r["sid"] for r in pilot]
    if args.limit:
        sids = sids[: args.limit]
    done = {r["sid"] for r in load_jsonl(OUT)} if not args.limit else set()
    todo = [s for s in sids if s not in done]
    ctx = build_context(todo)
    log(f"pilot {len(sids)} todo {len(todo)} context {len(ctx)}")

    import torch
    torch.cuda.reset_peak_memory_stats()
    try:
        backend = load_backend(args.model, True, args.batch_size)
    except Exception:
        log("4bit load failed, fallback to Qwen3-1.7B bf16\n" + traceback.format_exc())
        backend = load_backend(FALLBACK_MODEL, False, args.batch_size)

    engine = LLM2Jev(backend=backend)
    t0 = time.perf_counter()
    n = 0
    with open(OUT, "a", encoding="utf-8") as f:
        for sid in todo:
            if sid not in ctx:
                log(f"missing context {sid}")
                continue
            request = JevRequest(state=format_state(ctx[sid]), model=backend.model_path, questions=questions)
            ts = time.perf_counter()
            response = engine.evaluate(request)
            seconds = time.perf_counter() - ts
            rec = to_record(sid, response, backend.model_path, backend.bits, seconds)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
            if n == 1 or n % 10 == 0:
                vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
                log(f"{n}/{len(todo)} sid={sid} sec={seconds:.2f} vram_gb={vram:.2f}")
    elapsed = time.perf_counter() - t0
    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    avg = elapsed / n if n else 0
    log(f"done n={n} elapsed_s={elapsed:.1f} avg_s={avg:.2f} peak_vram_gb={vram:.2f} model={backend.model_path} bits={backend.bits}")
    backend.close()


if __name__ == "__main__":
    main()
