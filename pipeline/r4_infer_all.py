"""r4 ep2 對 21,183 句售後句跑 churn 與 stance。可中斷續跑。

已完成的 jev_lora_r4_ep2_pilot.jsonl（600）與 _val.jsonl（1,096）直接沿用。
輸出 data/processed/churn_r4_all.jsonl，日誌 data/processed/r4_all_run.log。

  python pipeline/r4_infer_all.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\hf_cache")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "local_jev"))

from evaluate import binary_c  # noqa: E402
from label_jev_pilot import build_questions, format_state, to_record  # noqa: E402
from verify_churn import build_context, load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
OUT = P / "churn_r4_all.jsonl"
LOG = P / "r4_all_run.log"
SANITY = P / "r4_all_sanity.json"
MODEL = "Qwen/Qwen3-4B-Instruct-2507"
ADAPTER = Path(r"D:\hf_cache\lora\qwen3-4b-churn-r4-ep2")
SEED_FILES = [
    P / "jev_lora_r4_ep2_pilot.jsonl",
    P / "jev_lora_r4_ep2_val.jsonl",
]
PROGRESS_EVERY = 500


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def slim(rec: dict) -> dict:
    probs = {str(k): round(float(v), 6) for k, v in rec["churn_p"].items()}
    p_churn = probs.get("2", 0.0) + probs.get("3", 0.0)
    return {
        "sid": rec["sid"],
        "churn_p": probs,
        "p_churn": round(p_churn, 6),
        "c_expect": int(rec["c_expect"]),
        "c_argmax": int(rec["c_argmax"]),
        "w": rec["w"],
        "w_p": {str(k): round(float(v), 6) for k, v in rec["w_p"].items()},
        "seconds": round(float(rec.get("seconds") or 0), 3),
    }


def load_done() -> dict[str, dict]:
    done = {}
    if OUT.exists():
        for rec in load_jsonl(OUT):
            done[rec["sid"]] = rec
    return done


def append_records(records: list[dict]) -> None:
    if not records:
        return
    with open(OUT, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def seed(after_sids: set[str], done: dict[str, dict]) -> int:
    added = []
    for path in SEED_FILES:
        n = 0
        for rec in load_jsonl(path):
            sid = rec["sid"]
            if sid not in after_sids or sid in done:
                continue
            row = slim(rec)
            done[sid] = row
            added.append(row)
            n += 1
        log(f"seed {path.name} +{n}")
    append_records(added)
    return len(added)


def rewrite_canonical(order: list[str], done: dict[str, dict]) -> None:
    tmp = OUT.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for sid in order:
            f.write(json.dumps(done[sid], ensure_ascii=False) + "\n")
    tmp.replace(OUT)


def sanity(order: list[str], done: dict[str, dict]) -> dict:
    gold = {}
    for rec in load_jsonl(P / "churn_verified.jsonl"):
        gold[rec["sid"]] = rec
    pairs_expect = []
    pairs_p50 = []
    n_p50 = 0
    missing_gold = 0
    for sid in order:
        rec = done[sid]
        if rec["p_churn"] >= 0.5:
            n_p50 += 1
        g = gold.get(sid)
        if g is None:
            missing_gold += 1
            continue
        y = 1 if int(g["c"]) >= 2 else 0
        pairs_expect.append((y, 1 if int(rec["c_expect"]) >= 2 else 0))
        pairs_p50.append((y, 1 if rec["p_churn"] >= 0.5 else 0))
    expect = binary_c(pairs_expect)
    thr = binary_c(pairs_p50)
    out = {
        "n": len(order),
        "unique_sids": len(done),
        "n_p_churn_ge_0.5": n_p50,
        "missing_gold": missing_gold,
        "note": "含訓練句，只做 sanity check，不可當留出評估",
        "c_expect_ge2": {
            "agreement": expect["agreement"],
            "kappa": expect["kappa"],
            "precision": expect["prf"]["precision"],
            "recall": expect["prf"]["recall"],
            "f1": expect["prf"]["f1"],
            "confusion": expect["confusion"],
        },
        "p_churn_ge_0.5": {
            "agreement": thr["agreement"],
            "kappa": thr["kappa"],
            "precision": thr["prf"]["precision"],
            "recall": thr["prf"]["recall"],
            "f1": thr["prf"]["f1"],
            "confusion": thr["confusion"],
        },
    }
    SANITY.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    e = out["c_expect_ge2"]
    t = out["p_churn_ge_0.5"]
    log(
        "SANITY not-held-out "
        f"n={out['n']} p_churn>=0.5 {n_p50} "
        f"c_expect>=2 agreement={e['agreement']:.4f} kappa={e['kappa']:.4f} "
        f"P={e['precision']:.4f} R={e['recall']:.4f} F1={e['f1']:.4f} "
        f"thr0.5 agreement={t['agreement']:.4f} kappa={t['kappa']:.4f} "
        f"P={t['precision']:.4f} R={t['recall']:.4f} F1={t['f1']:.4f}"
    )
    return out


def load_model(batch_size: int):
    import torch
    from peft import PeftModel

    from local_jev.quant_backend import FourBitTransformersBackend

    if not ADAPTER.exists():
        raise FileNotFoundError(f"找不到 adapter：{ADAPTER}")
    log(f"loading {MODEL} adapter={ADAPTER} batch={batch_size}")
    torch.cuda.reset_peak_memory_stats()
    backend = FourBitTransformersBackend(MODEL, batch_size=batch_size, load_in_4bit=True)
    backend.model = PeftModel.from_pretrained(backend.model, str(ADAPTER))
    backend.model.eval()
    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    log(f"loaded bits={backend.bits} vram_gb={vram:.2f}")
    return backend


def infer(todo: list[str], done: dict[str, dict], batch_size: int) -> None:
    import torch
    from llm2jev import JevRequest, LLM2Jev

    ctx = build_context(todo)
    missing = [s for s in todo if s not in ctx]
    if missing:
        raise RuntimeError(f"缺少前後文 {len(missing)} 句，例如 {missing[:3]}")
    questions = build_questions()
    questions = {k: v for k, v in questions.items() if k in {"churn", "stance"}}
    backend = load_model(batch_size)
    engine = LLM2Jev(backend=backend)
    t0 = time.perf_counter()
    n = 0
    total_target = len(done) + len(todo)
    try:
        with open(OUT, "a", encoding="utf-8") as f:
            for sid in todo:
                request = JevRequest(
                    state=format_state(ctx[sid]),
                    model=backend.model_path,
                    questions=questions,
                )
                ts = time.perf_counter()
                response = engine.evaluate(request)
                seconds = time.perf_counter() - ts
                rec = slim(to_record(sid, response, backend.model_path, backend.bits, seconds))
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                done[sid] = rec
                n += 1
                if n == 1 or n % PROGRESS_EVERY == 0:
                    elapsed = time.perf_counter() - t0
                    avg = elapsed / n
                    left = (len(todo) - n) * avg
                    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
                    log(
                        f"PROGRESS total={len(done)}/{total_target} new={n}/{len(todo)} "
                        f"avg_s={avg:.2f} eta_min={left / 60:.1f} vram_gb={vram:.2f} sid={sid}"
                    )
    except Exception:
        log("infer failed\n" + traceback.format_exc())
        raise
    elapsed = time.perf_counter() - t0
    avg = elapsed / n if n else 0
    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    log(
        f"infer done new={n} elapsed_s={elapsed:.1f} avg_s={avg:.2f} "
        f"peak_vram_gb={vram:.2f} total={len(done)}"
    )
    backend.close()


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=4)
    args = ap.parse_args()

    after = load_jsonl(P / "aftersales.jsonl")
    order = [r["sid"] for r in after]
    if len(order) != len(set(order)):
        raise RuntimeError("aftersales sid 有重複")
    after_sids = set(order)
    log(f"aftersales {len(order)}")
    done = load_done()
    log(f"already {len(done)}")
    seed(after_sids, done)
    extra = [s for s in done if s not in after_sids]
    if extra:
        raise RuntimeError(f"輸出含售後集以外的 sid {len(extra)}")
    todo = [s for s in order if s not in done]
    log(f"todo {len(todo)} done {len(done)}")
    if todo:
        infer(todo, done, args.batch_size)
    missing = [s for s in order if s not in done]
    if missing:
        raise RuntimeError(f"仍缺 {len(missing)} 句")
    rewrite_canonical(order, done)
    got = [r["sid"] for r in load_jsonl(OUT)]
    if got != order:
        raise RuntimeError(f"回寫後 sid 順序或數量不符：{len(got)} vs {len(order)}")
    done = {r["sid"]: r for r in load_jsonl(OUT)}
    sanity(order, done)
    log(f"DONE unique={len(order)}")


if __name__ == "__main__":
    main()
