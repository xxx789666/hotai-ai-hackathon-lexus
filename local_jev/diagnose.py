"""T6：檢查 T5 adapter 是否忽略 Context，以及訓練 batch 的 label 位置。

  python local_jev/diagnose.py
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("HF_HOME", r"D:\hf_cache")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from label_jev_pilot import build_questions, format_state  # noqa: E402
from local_jev.train_churn_lora import (  # noqa: E402
    build_examples,
    collate,
    load_model,
    load_tokenizer,
    make_split,
    subsample_round1,
)
from verify_churn import build_context, load_jsonl  # noqa: E402

P = ROOT / "data" / "processed"
MODEL = "Qwen/Qwen3-1.7B"
ADAPTER = Path(r"D:\hf_cache\lora\qwen3-1.7b-churn-r1")


def banner(title: str) -> None:
    print(f"\n===== {title} =====", flush=True)


def churn_questions():
    return {k: v for k, v in build_questions().items() if k in ("churn", "stance")}


def score_sids(backend, sids, ctx, questions, states=None):
    from llm2jev import JevRequest, LLM2Jev

    engine = LLM2Jev(backend=backend)
    rows = []
    for sid in sids:
        state = states[sid] if states and sid in states else format_state(ctx[sid])
        request = JevRequest(state=state, model=backend.model_path, questions=questions)
        response = engine.evaluate(request)
        churn = response.scores["churn"]
        probs = {str(k): round(float(v), 4) for k, v in churn.probabilities.items()}
        prompt = state.replace("\n", " ")[:200]
        print(f"sid={sid} prompt={prompt}", flush=True)
        print(f"  churn_p={probs} w={response.choices['stance'].choice}", flush=True)
        rows.append(probs)
    return rows


def load_backend(adapter: str | None):
    from local_jev.quant_backend import FourBitTransformersBackend

    backend = FourBitTransformersBackend(MODEL, batch_size=1, load_in_4bit=True)
    if adapter:
        from peft import PeftModel
        backend.model = PeftModel.from_pretrained(backend.model, adapter)
        backend.model.eval()
    return backend


def pick_sids(labels, test_sids):
    chosen = {3: [], 0: [], 1: []}
    for sid in test_sids:
        c = int(labels[sid]["c"]) if sid in labels else None
        if c in chosen and len(chosen[c]) < (2 if c != 1 else 1):
            chosen[c].append(sid)
        if len(chosen[3]) == 2 and len(chosen[0]) == 2 and len(chosen[1]) == 1:
            break
    return chosen[3] + chosen[0] + chosen[1]


def step_infer(labels, test_sids):
    sids = pick_sids(labels, test_sids)
    ctx = build_context(sids)
    questions = churn_questions()
    banner("STEP1 adapter")
    print("sids", sids, {s: int(labels[s]["c"]) for s in sids}, flush=True)
    backend = load_backend(str(ADAPTER))
    score_sids(backend, sids, ctx, questions)
    banner("STEP1 weather swap")
    weather = {sids[0]: "今天天氣很好"}
    score_sids(backend, [sids[0]], ctx, questions, states=weather)
    backend.close()
    del backend
    import torch
    torch.cuda.empty_cache()
    banner("STEP2 base")
    backend = load_backend(None)
    score_sids(backend, sids, ctx, questions)
    backend.close()
    del backend
    torch.cuda.empty_cache()


def step_batch(labels):
    banner("STEP3 train batch")
    split = make_split(42)
    sampled = subsample_round1(split["train_sids"], labels, 42)
    tok = load_tokenizer(MODEL)
    questions = churn_questions()
    rows, _ = build_examples(sampled[:8], labels, tok, 768, questions)
    yes_id = tok.encode("yes", add_special_tokens=False)
    no_id = tok.encode("no", add_special_tokens=False)
    print(f"yes_token_ids={yes_id} no_token_ids={no_id} pad={tok.pad_token_id} padding_side={tok.padding_side}", flush=True)
    for row in rows[:3]:
        text = tok.decode(row["input_ids"])
        lab_pos = [i for i, x in enumerate(row["labels"]) if x != -100]
        print("--- example ---", flush=True)
        print(text, flush=True)
        print(f"len={len(row['input_ids'])} label_pos={lab_pos} label_tok={tok.decode([row['labels'][lab_pos[0]]])!r} prev={tok.decode([row['input_ids'][lab_pos[0]-1]])!r}", flush=True)
        print(f"tail={text[-180:]!r}", flush=True)
    batch = collate(rows[:2], tok.pad_token_id)
    print(f"batch_shape={tuple(batch['input_ids'].shape)} attn_row_sums={batch['attention_mask'].sum(1).tolist()}", flush=True)
    for i in range(batch["input_ids"].shape[0]):
        labs = batch["labels"][i].tolist()
        ids = batch["input_ids"][i].tolist()
        pos = [j for j, x in enumerate(labs) if x != -100]
        p = pos[0]
        print(
            f"row{i} label_pos={p} last_index={len(ids)-1} "
            f"token={tok.decode([ids[p]])!r} prev={tok.decode([ids[p-1]])!r} "
            f"attn_at_label={int(batch['attention_mask'][i, p])} "
            f"n_masked_labels={sum(x == -100 for x in labs)}",
            flush=True,
        )
    from llm2jev import JevRequest
    from llm2jev.backend.tokenization import _apply_chat_template
    from llm2jev.inference.binary import compile_binary_questions
    from llm2jev.inference.prompt import DefaultPromptRenderer
    ctx = build_context([rows[0]["sid"]])
    request = JevRequest(state=format_state(ctx[rows[0]["sid"]]), model="local", questions=questions)
    bq = next(q for q in compile_binary_questions(request) if q.question_id == "churn" and int(q.candidate) == 2)
    infer_prompt = _apply_chat_template(tok, DefaultPromptRenderer().render(bq), enable_thinking=False)
    train_prompt = tok.decode(rows[0]["input_ids"][:-1], skip_special_tokens=False)
    print("PROMPT_TAIL_MATCH", infer_prompt[-80:] == train_prompt[-80:], flush=True)
    print("INFER_TAIL", repr(infer_prompt[-120:]), flush=True)
    print("TRAIN_TAIL", repr(train_prompt[-120:]), flush=True)


def p_yes(model, tok, prompt_ids):
    import torch
    yes_id = tok.encode("yes", add_special_tokens=False)[0]
    no_id = tok.encode("no", add_special_tokens=False)[0]
    ids = torch.tensor([prompt_ids], device="cuda")
    attn = torch.ones_like(ids)
    with torch.no_grad():
        logits = model(input_ids=ids, attention_mask=attn).logits[0, -1]
    pair = torch.softmax(logits[[no_id, yes_id]].float(), dim=0)
    return float(pair[1])


def step_overfit(labels):
    import torch
    banner("STEP4 overfit-32")
    split = make_split(42)
    sampled = subsample_round1(split["train_sids"], labels, 42)
    model, tok, stack = load_model(MODEL, 768)
    n_train = sum(p.requires_grad for p in model.parameters())
    print(f"stack={stack} trainable_tensors={n_train}", flush=True)
    questions = churn_questions()
    rows, _ = build_examples(sampled[:40], labels, tok, 768, questions)
    yes = [r for r in rows if r["yes"] == 1]
    no = [r for r in rows if r["yes"] == 0]
    rng = random.Random(42)
    pick = rng.sample(yes, 16) + rng.sample(no, 16)
    rng.shuffle(pick)
    batch = collate(pick[:2], tok.pad_token_id)
    model.train()
    loss = model(**{k: v.cuda() for k, v in batch.items()}).loss
    loss.backward()
    grad = 0.0
    for p in model.parameters():
        if p.requires_grad and p.grad is not None:
            grad += float(p.grad.detach().float().pow(2).sum())
    print(f"one_batch_loss={float(loss):.4f} grad_sq={grad:.6f}", flush=True)
    model.zero_grad(set_to_none=True)
    import bitsandbytes as bnb
    opt = bnb.optim.AdamW8bit((p for p in model.parameters() if p.requires_grad), lr=2e-4)
    for step in range(1, 121):
        batch = collate(pick[(step * 2) % 32:(step * 2) % 32 + 2] if False else pick[((step - 1) * 2) % 32:((step - 1) * 2) % 32 + 2], tok.pad_token_id)
        # wrap around if the slice hits the boundary
        start = ((step - 1) * 2) % 32
        chunk = pick[start:start + 2]
        if len(chunk) < 2:
            chunk = [pick[start], pick[0]]
        batch = collate(chunk, tok.pad_token_id)
        loss = model(**{k: v.cuda() for k, v in batch.items()}).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad), 1.0)
        opt.step()
        opt.zero_grad(set_to_none=True)
        if step in (1, 60, 90, 120):
            print(f"overfit step={step} loss={float(loss):.4f}", flush=True)
    model.eval()
    yes_ps, no_ps = [], []
    for row in pick:
        py = p_yes(model, tok, row["input_ids"][:-1])
        (yes_ps if row["yes"] else no_ps).append(py)
        if (row["yes"] and py <= 0.9) or (not row["yes"] and py >= 0.1):
            tail = tok.decode(row["input_ids"][-40:])
            print(f"MISS yes={row['yes']} p={py:.3f} tail={tail[-80:]!r}", flush=True)
    print(f"yes_p_yes min={min(yes_ps):.3f} mean={sum(yes_ps)/len(yes_ps):.3f}", flush=True)
    print(f"no_p_yes max={max(no_ps):.3f} mean={sum(no_ps)/len(no_ps):.3f}", flush=True)
    ok = min(yes_ps) > 0.9 and max(no_ps) < 0.1
    print(f"OVERFIT_PASS={ok}", flush=True)


def main() -> None:
    labels = {}
    for r in load_jsonl(P / "churn_verified.jsonl"):
        labels[r["sid"]] = r
    test_sids = []
    seen = set()
    for r in load_jsonl(P / "aspect_pilot_sonnet.jsonl"):
        if r["sid"] not in seen:
            seen.add(r["sid"])
            test_sids.append(r["sid"])
    step_infer(labels, test_sids)
    step_batch(labels)
    step_overfit(labels)


if __name__ == "__main__":
    main()
