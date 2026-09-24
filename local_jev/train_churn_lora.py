"""用已複核流失標籤做 QLoRA。訓練樣本與 LLM2Jev prefill prompt 對齊。

  python local_jev/train_churn_lora.py --prepare-only
  python local_jev/train_churn_lora.py --round 1
  python local_jev/train_churn_lora.py --round 2
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

os.environ.setdefault("HF_HOME", r"D:\hf_cache")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from label_jev_pilot import format_state, build_questions  # noqa: E402
from verify_churn import build_context, load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
LOG = P / "jev_lora_train.log"
LORA_ROOT = Path(r"D:\hf_cache\lora")

ROUND = {
    1: {
        "model": "Qwen/Qwen3-1.7B",
        "out": LORA_ROOT / "qwen3-1.7b-churn-r1",
        "batch": 2,
        "accum": 8,
        "max_seq": 768,
    },
    2: {
        "model": "Qwen/Qwen3-4B-Instruct-2507",
        "out": LORA_ROOT / "qwen3-4b-churn-r2",
        "batch": 1,
        "accum": 16,
        "max_seq": 640,
    },
}


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def last_by_sid(rows: list[dict]) -> dict:
    last = {}
    for r in rows:
        last[r["sid"]] = r
    return last


def c_dist(sids, labels) -> dict:
    c = Counter(int(labels[s]["c"]) for s in sids if s in labels)
    return {str(k): c.get(k, 0) for k in range(4)} | {"n": sum(c.values())}


def make_split(seed: int = 42) -> dict:
    labels = last_by_sid(load_jsonl(P / "churn_verified.jsonl"))
    docs = {}
    for r in load_jsonl(P / "aftersales.jsonl"):
        docs[r["sid"]] = r["doc_id"]
    test_sids = []
    seen = set()
    for r in load_jsonl(P / "aspect_pilot_sonnet.jsonl"):
        if r["sid"] not in seen:
            seen.add(r["sid"])
            test_sids.append(r["sid"])
    test_docs = {docs[s] for s in test_sids if s in docs}
    missing_doc = [s for s in test_sids if s not in docs]
    pool = []
    for sid, lab in labels.items():
        doc = docs.get(sid)
        if doc is None or doc in test_docs:
            continue
        pool.append(sid)
    by_doc: dict[str, list[str]] = {}
    for sid in pool:
        by_doc.setdefault(docs[sid], []).append(sid)
    doc_ids = sorted(by_doc)
    rng = random.Random(seed)
    rng.shuffle(doc_ids)
    n_val_docs = max(1, int(round(len(doc_ids) * 0.10)))
    val_docs = set(doc_ids[:n_val_docs])
    train, val = [], []
    for doc, sids in by_doc.items():
        (val if doc in val_docs else train).append(sids)
    train_sids = [s for group in train for s in group]
    val_sids = [s for group in val for s in group]
    leaked = (set(train_sids) | set(val_sids)) & set(test_sids)
    leaked_docs = {docs[s] for s in train_sids + val_sids} & test_docs
    if leaked or leaked_docs:
        raise RuntimeError(f"test leak sids={len(leaked)} docs={len(leaked_docs)}")
    return {
        "labels": labels,
        "docs": docs,
        "test_sids": test_sids,
        "test_docs": test_docs,
        "train_sids": train_sids,
        "val_sids": val_sids,
        "missing_test_doc": missing_doc,
        "n_docs_train": len(doc_ids) - len(val_docs),
        "n_docs_val": len(val_docs),
        "n_docs_test": len(test_docs),
    }


def subsample_round1(train_sids, labels, seed: int = 42) -> list[str]:
    """第一輪驗證食譜：保留全部 c>=2，負例抽到正例的 3 倍。"""
    pos = [s for s in train_sids if int(labels[s]["c"]) >= 2]
    neg = [s for s in train_sids if int(labels[s]["c"]) < 2]
    rng = random.Random(seed)
    keep_neg = min(len(neg), 3 * len(pos))
    picked = rng.sample(neg, keep_neg) if keep_neg else []
    out = pos + picked
    rng.shuffle(out)
    return out


def oversample(train_sids, labels, seed: int = 42) -> list[str]:
    pos = [s for s in train_sids if int(labels[s]["c"]) >= 2]
    neg = [s for s in train_sids if int(labels[s]["c"]) < 2]
    if not pos:
        return list(train_sids)
    target_pos = int(round(0.30 / 0.70 * len(neg)))
    rng = random.Random(seed)
    extra = max(0, target_pos - len(pos))
    copies = list(pos)
    if extra:
        copies.extend(rng.choices(pos, k=extra))
    out = neg + copies
    rng.shuffle(out)
    return out


def candidate_label(question_id: str, candidate, gold: dict) -> str:
    if question_id == "churn":
        return "yes" if int(candidate) == int(gold["c"]) else "no"
    if question_id == "stance":
        return "yes" if str(candidate) == str(gold["w"]) else "no"
    raise ValueError(question_id)


def build_examples(sids, labels, tokenizer, max_seq: int, questions) -> tuple[list[dict], str]:
    from llm2jev import JevRequest
    from llm2jev.backend.tokenization import _apply_chat_template, _single_token_id
    from llm2jev.inference.binary import compile_binary_questions
    from llm2jev.inference.prompt import DefaultPromptRenderer

    yes_id = _single_token_id(tokenizer, "yes", "yes_label")
    no_id = _single_token_id(tokenizer, "no", "no_label")
    renderer = DefaultPromptRenderer()
    ctx = build_context(sids)
    rows = []
    sample_prompt = ""
    n_trunc = 0
    for sid in sids:
        if sid not in ctx or sid not in labels:
            continue
        gold = labels[sid]
        request = JevRequest(
            state=format_state(ctx[sid]),
            model="local",
            questions=questions,
        )
        for bq in compile_binary_questions(request):
            if bq.question_id not in ("churn", "stance"):
                continue
            prompt = _apply_chat_template(
                tokenizer, renderer.render(bq), enable_thinking=False,
            )
            if not sample_prompt and bq.question_id == "churn" and int(bq.candidate) == 2:
                sample_prompt = prompt
            ids = tokenizer.encode(prompt, add_special_tokens=False)
            target = yes_id if candidate_label(bq.question_id, bq.candidate, gold) == "yes" else no_id
            if len(ids) > max_seq - 1:
                ids = ids[-(max_seq - 1):]
                n_trunc += 1
            rows.append({
                "input_ids": ids + [target],
                "labels": [-100] * len(ids) + [target],
                "yes": int(target == yes_id),
                "c": int(gold["c"]),
                "sid": sid,
            })
    log(f"examples {len(rows)} truncated {n_trunc} missing_ctx {len(sids) - len(ctx)}")
    return rows, sample_prompt


def load_tokenizer(model_name: str):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    return tok


def load_model(model_name: str, max_seq: int):
    import torch
    stack = "peft"
    try:
        from unsloth import FastLanguageModel
        model, tok = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq,
            dtype=torch.bfloat16,
            load_in_4bit=True,
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            lora_alpha=32,
            lora_dropout=0,
            bias="none",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
        stack = "unsloth"
        return model, tok, stack
    except Exception as exc:
        log(f"unsloth unavailable ({type(exc).__name__}: {exc}); using PEFT + bitsandbytes")
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb,
        device_map={"": 0},
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    ))
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    tok = load_tokenizer(model_name)
    return model, tok, stack


def collate(batch, pad_id: int):
    import torch
    width = max(len(x["input_ids"]) for x in batch)
    input_ids, labels, attn = [], [], []
    for x in batch:
        pad = width - len(x["input_ids"])
        input_ids.append(x["input_ids"] + [pad_id] * pad)
        labels.append(x["labels"] + [-100] * pad)
        attn.append([1] * len(x["input_ids"]) + [0] * pad)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "attention_mask": torch.tensor(attn, dtype=torch.long),
    }


def batch_loss(model, batch, device):
    batch = {k: v.to(device) for k, v in batch.items()}
    return model(**batch).loss


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1, choices=(1, 2))
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--max-steps", type=int, default=0)
    ap.add_argument("--max-seq", type=int, default=0)
    ap.add_argument("--batch", type=int, default=0)
    args = ap.parse_args()
    cfg = dict(ROUND[args.round])
    if args.max_seq:
        cfg["max_seq"] = args.max_seq
    if args.batch:
        cfg["batch"] = args.batch

    split = make_split(42)
    labels = split["labels"]
    log(
        "split "
        f"train={len(split['train_sids'])} val={len(split['val_sids'])} "
        f"test={len(split['test_sids'])} "
        f"docs train/val/test={split['n_docs_train']}/{split['n_docs_val']}/{split['n_docs_test']} "
        f"missing_test_doc={len(split['missing_test_doc'])}"
    )
    log(f"dist train {c_dist(split['train_sids'], labels)}")
    log(f"dist val {c_dist(split['val_sids'], labels)}")
    log(f"dist test {c_dist(split['test_sids'], labels)}")
    epochs = 1 if args.round == 1 else 2
    if args.round == 1:
        sampled = subsample_round1(split["train_sids"], labels, 42)
        recipe = "round1 keep all c>=2, neg=3x pos, epochs=1"
    else:
        sampled = oversample(split["train_sids"], labels, 42)
        recipe = "round2 oversample c>=2 to 30%, epochs=2"
    pos = sum(int(labels[s]["c"]) >= 2 for s in sampled)
    log(f"recipe {recipe}")
    log(f"train_used sentences {len(sampled)} c>=2 {pos} rate {pos / len(sampled):.4f} dist {c_dist(sampled, labels)}")
    manifest = cfg["out"] / "split_sids.json"
    if args.prepare_only:
        tok = load_tokenizer(cfg["model"])
        questions = {k: v for k, v in build_questions().items() if k in ("churn", "stance")}
        train_rows, sample = build_examples(sampled[:2], labels, tok, cfg["max_seq"], questions)
        yes = sum(r["yes"] for r in train_rows)
        log(f"prepare sample_rows {len(train_rows)} yes {yes}")
        log("PROMPT_SAMPLE_BEGIN")
        log(sample)
        log("PROMPT_SAMPLE_END")
        return

    import torch
    from torch.utils.data import DataLoader
    torch.backends.cuda.matmul.allow_tf32 = True
    model, tok, stack = load_model(cfg["model"], cfg["max_seq"])
    log(f"stack={stack} model={cfg['model']} max_seq={cfg['max_seq']} batch={cfg['batch']} accum={cfg['accum']}")
    questions = {k: v for k, v in build_questions().items() if k in ("churn", "stance")}
    train_rows, sample = build_examples(sampled, labels, tok, cfg["max_seq"], questions)
    val_rows, _ = build_examples(split["val_sids"], labels, tok, cfg["max_seq"], questions)
    yes = sum(r["yes"] for r in train_rows)
    log(f"train candidates {len(train_rows)} yes {yes} yes_rate {yes / max(1, len(train_rows)):.4f}")
    log(f"val candidates {len(val_rows)}")
    log("PROMPT_SAMPLE_BEGIN")
    log(sample)
    log("PROMPT_SAMPLE_END")
    cfg["out"].mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "train": split["train_sids"],
        "val": split["val_sids"],
        "test": split["test_sids"],
    }), encoding="utf-8")

    pad_id = tok.pad_token_id
    loader = DataLoader(
        train_rows,
        batch_size=cfg["batch"],
        shuffle=True,
        collate_fn=lambda b: collate(b, pad_id),
    )
    steps_per_epoch = (len(loader) + cfg["accum"] - 1) // cfg["accum"]
    total_steps = steps_per_epoch * epochs
    if args.max_steps:
        total_steps = min(total_steps, args.max_steps)
    warmup = max(1, int(total_steps * 0.03))
    import bitsandbytes as bnb
    from transformers import get_linear_schedule_with_warmup
    opt = bnb.optim.AdamW8bit((p for p in model.parameters() if p.requires_grad), lr=2e-4)
    sched = get_linear_schedule_with_warmup(opt, warmup, total_steps)
    model.train()
    device = "cuda"
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    opt_step = 0
    micro = 0
    window = []
    opt.zero_grad(set_to_none=True)
    log(f"train start epochs={epochs} steps={total_steps} warmup={warmup} steps_per_epoch={steps_per_epoch}")
    done = False
    for epoch in range(1, epochs + 1):
        for batch in loader:
            loss = batch_loss(model, batch, device) / cfg["accum"]
            loss.backward()
            micro += 1
            window.append(float(loss.detach()) * cfg["accum"])
            if micro % cfg["accum"] != 0:
                continue
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            opt_step += 1
            if opt_step <= 3 or opt_step % 20 == 0:
                vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
                log(f"progress step={opt_step}/{total_steps} elapsed_s={time.perf_counter() - t0:.0f} vram_gb={vram:.2f}")
            if opt_step % 1000 == 0:
                ckpt = cfg["out"] / f"ckpt-{opt_step}"
                model.save_pretrained(ckpt)
                log(f"checkpoint {ckpt}")
            if opt_step % 200 == 0 or opt_step == total_steps:
                model.eval()
                rng = random.Random(42 + opt_step)
                pick = rng.sample(val_rows, k=min(500, len(val_rows)))
                vloss = 0.0
                with torch.no_grad():
                    for i in range(0, len(pick), cfg["batch"]):
                        vb = collate(pick[i:i + cfg["batch"]], pad_id)
                        vloss += float(batch_loss(model, vb, device)) * len(vb["input_ids"])
                vloss /= max(1, len(pick))
                train_loss = sum(window) / max(1, len(window))
                window.clear()
                vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
                elapsed = time.perf_counter() - t0
                log(
                    f"step={opt_step} epoch={epoch} train_loss={train_loss:.4f} "
                    f"val_loss={vloss:.4f} lr={sched.get_last_lr()[0]:.6g} "
                    f"vram_gb={vram:.2f} elapsed_s={elapsed:.0f}"
                )
                model.train()
            if opt_step >= total_steps:
                done = True
                break
        if done:
            break
    cfg["out"].mkdir(parents=True, exist_ok=True)
    model.save_pretrained(cfg["out"])
    tok.save_pretrained(cfg["out"])
    vram = torch.cuda.max_memory_allocated() / (1024 ** 3)
    log(f"saved {cfg['out']} steps={opt_step} elapsed_s={time.perf_counter() - t0:.0f} peak_vram_gb={vram:.2f} stack={stack}")


if __name__ == "__main__":
    main()
