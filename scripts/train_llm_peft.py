#!/usr/bin/env python3
"""Fine-tune autoregressive generative LLMs via QLoRA for 7-dimension symptom extraction.

Part of Kent-AI Phase 4 / Week 2 Comparative Study.
Supports Qwen-2.5-7B-Instruct, BioMistral-7B, and LLaMA-3.1-8B-Instruct.
Optimized for NVIDIA RTX 5000 Ada (32GB VRAM) with 4-bit NormalFloat (NF4) quantization.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Redirect large HuggingFace caches and tmp dirs to high-capacity storage (/DATA)
os.environ["HF_HOME"] = os.environ.get("HF_HOME", "/DATA/narya/cache/huggingface")
os.environ["TRANSFORMERS_CACHE"] = os.environ.get("TRANSFORMERS_CACHE", "/DATA/narya/cache/huggingface")
os.environ["TMPDIR"] = os.environ.get("TMPDIR", "/DATA/narya/tmp")
os.environ["HF_HUB_DISABLE_XET"] = "1"

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch
from datasets import Dataset
from peft import (
    LoraConfig,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer

from src.models.llm_dataset import (
    format_case_for_training,
    load_instruction_dataset,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_llm_peft")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune generative LLMs (7B-8B) using 4-bit QLoRA on Kent-AI dataset."
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="HuggingFace model ID or local directory (e.g., Qwen/Qwen2.5-7B-Instruct, BioMistral/BioMistral-7B).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/models/qwen_homeoQLoRA",
        help="Target directory to save fine-tuned LoRA adapter weights and tokenizer.",
    )
    parser.add_argument(
        "--train-file",
        type=str,
        default="data/processed/train.jsonl",
        help="Path to processed train JSONL cases.",
    )
    parser.add_argument(
        "--val-file",
        type=str,
        default="data/processed/val.jsonl",
        help="Path to processed val JSONL cases.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of fine-tuning epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Per-device batch size.",
    )
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=4,
        help="Gradient accumulation steps (effective batch size = batch_size * grad_accum).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=2e-4,
        help="Peak learning rate for LoRA adapter.",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=512,
        help="Maximum sequence length for tokenization.",
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=16,
        help="LoRA rank dimension.",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=32,
        help="LoRA scaling factor alpha.",
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=0.05,
        help="LoRA dropout rate.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Limit number of train/val samples for fast dry-run verification.",
    )
    parser.add_argument(
        "--save-steps",
        type=int,
        default=200,
        help="Save checkpoint every X steps.",
    )
    parser.add_argument(
        "--eval-steps",
        type=int,
        default=100,
        help="Evaluate on validation set every X steps.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("Starting Kent-AI Generative LLM QLoRA Fine-Tuning")
    logger.info("Base Model: %s", args.model_name)
    logger.info("Output Directory: %s", args.output_dir)
    logger.info("Hardware: %s", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
    logger.info("=" * 70)

    # 1. Load Tokenizer
    logger.info("Loading tokenizer for %s...", args.model_name)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        trust_remote_code=True,
    )
    # Refinement #2: Configure padding token and right-side padding for training
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Configure 4-bit NormalFloat (NF4) Quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load Quantized Base Model
    logger.info("Loading 4-bit quantized base model on GPU...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    # 4. Prepare Model for k-bit Training & LoRA
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # Refinement #1: Target all linear projection layers for JSON syntax adherence
    target_modules = [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 5. Load and Format Datasets
    logger.info("Loading raw clinical case datasets...")
    raw_train = load_instruction_dataset(args.train_file, max_samples=args.max_samples)
    raw_val = load_instruction_dataset(
        args.val_file,
        max_samples=min(args.max_samples, 200) if args.max_samples else None,
    )

    logger.info("Formatting cases into chat template (Train: %d, Val: %d)...", len(raw_train), len(raw_val))
    train_formatted = [format_case_for_training(c, tokenizer) for c in raw_train]
    val_formatted = [format_case_for_training(c, tokenizer) for c in raw_val]

    train_dataset = Dataset.from_list(train_formatted)
    val_dataset = Dataset.from_list(val_formatted)

    # 6. Configure SFT Training
    training_args = SFTConfig(
        output_dir=str(output_path / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_steps=20,
        bf16=True,
        fp16=False,
        logging_steps=10,
        eval_strategy="steps" if len(val_dataset) > 0 else "no",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=2,
        load_best_model_at_end=False,
        max_length=args.max_seq_length,
        dataset_text_field="text",
        packing=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset if len(val_dataset) > 0 else None,
        processing_class=tokenizer,
    )

    # 7. Execute Training
    logger.info("Beginning QLoRA training run...")
    trainer.train()

    # 8. Save Final Production Adapter and Tokenizer
    logger.info("Saving fine-tuned LoRA adapter to %s...", args.output_dir)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    logger.info("=" * 70)
    logger.info("Training complete! Model artifacts saved to %s", args.output_dir)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
