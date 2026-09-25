"""載入 LoRA，對測試集或驗證集跑 churn／stance，並呼叫 evaluate.py 的同一套指標。

  python local_jev/eval_lora.py --round 1 --split test
  python local_jev/eval_lora.py --round 1 --split val
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
LORA = {
    1: (
        "Qwen/Qwen3-1.7B",
        Path(r"D:\hf_cache\lora\qwen3-1.7b-churn-r1b"),
        "r1b",
    ),
    2: (
        "Qwen/Qwen3-4B-Instruct-2507",
        Path(r"D:\hf_cache\lora\qwen3-4b-churn-r2"),
        "r2",
    ),
    3: (
        "Qwen/Qwen3-1.7B",
        Path(r"D:\hf_cache\lora\qwen3-1.7b-churn-r3"),
        "r3",
    ),
}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=1, choices=(1, 2, 3))
    ap.add_argument("--split", choices=("test", "val"), default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=4)
    args = ap.parse_args()
    model, adapter, tag = LORA[args.round]
    if args.split == "test":
        out = ROOT / "data" / "processed" / f"jev_lora_{tag}_pilot.jsonl"
        sids_file = ""
    else:
        manifest = adapter / "split_sids.json"
        sids = json.loads(manifest.read_text(encoding="utf-8"))["val"]
        sids_file = ROOT / "data" / "processed" / f"jev_lora_{tag}_val_sids.txt"
        sids_file.write_text("\n".join(sids), encoding="utf-8")
        out = ROOT / "data" / "processed" / f"jev_lora_{tag}_val.jsonl"
    cmd = [
        str(PY if PY.exists() else sys.executable),
        str(ROOT / "pipeline" / "label_jev_pilot.py"),
        "--model", model,
        "--adapter", str(adapter),
        "--out", str(out),
        "--questions", "churn,stance",
        "--batch-size", str(args.batch_size),
    ]
    if sids_file:
        cmd.extend(["--sids-file", str(sids_file)])
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)
    metrics = ROOT / "data" / "processed" / f"jev_lora_{tag}_{args.split}_metrics.json"
    ev = [
        str(PY if PY.exists() else sys.executable),
        str(ROOT / "local_jev" / "evaluate.py"),
        "--jev", str(out),
        "--metrics", str(metrics),
    ]
    if args.split == "val":
        ev.extend(["--gold-c", str(ROOT / "data" / "processed" / "churn_verified.jsonl")])
    subprocess.run(ev, check=True, cwd=ROOT)
    print(metrics.read_text(encoding="utf-8")[:2000])


if __name__ == "__main__":
    main()
