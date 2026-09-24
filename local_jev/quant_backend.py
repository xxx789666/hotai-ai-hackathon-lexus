"""4-bit Transformers backend for LLM2Jev.

The upstream TransformersBackend loads bf16 and calls model.to(device).
A 4B model does not fit in 8 GB that way, so this subclass loads NF4
with bitsandbytes and keeps the same prefill-only yes/no scorer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from llm2jev.backend.tokenization import _single_token_id
from llm2jev.backend.transformers.backend import TransformersBackend


class FourBitTransformersBackend(TransformersBackend):
    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str | None = None,
        yes_label: str = "yes",
        no_label: str = "no",
        batch_size: int = 4,
        enable_thinking: bool = False,
        load_in_4bit: bool = True,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        self._torch = torch
        self.model_path = str(model_path)
        self.batch_size = batch_size
        self.enable_thinking = enable_thinking
        self.processor = None
        self.load_in_4bit = load_in_4bit
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if self.tokenizer.pad_token_id is None:
            if self.tokenizer.eos_token_id is None:
                raise ValueError("tokenizer must define a pad token or an EOS token")
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.yes_token_id = _single_token_id(self.tokenizer, yes_label, "yes_label")
        self.no_token_id = _single_token_id(self.tokenizer, no_label, "no_label")
        if self.yes_token_id == self.no_token_id:
            raise ValueError("yes_label and no_label must encode to different tokens")

        selected_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model_kwargs: dict[str, Any] = {}
        if load_in_4bit:
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
            model_kwargs["device_map"] = {"": 0} if selected_device == "cuda" else "cpu"
        else:
            model_kwargs["dtype"] = torch.bfloat16
            model_kwargs["device_map"] = {"": 0} if selected_device == "cuda" else "cpu"

        self.model = AutoModelForCausalLM.from_pretrained(self.model_path, **model_kwargs)
        self.model.eval()
        self.device = selected_device
        self.bits = 4 if load_in_4bit else 16
