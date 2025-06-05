# eval_hybrid_topk.py
# ───────────────────────────────────────────────────────────
# Evaluate Hybrid-Fusion (chunksize 750) with similarity_top_k ∈ {6,8,12,14}.
# Writes a detailed CSV and a summary CSV into eval_outputs/.

from __future__ import annotations
import os

import argparse
import asyncio
import re
import textwrap
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from src.chat.chat import Chat        
from src.models.llm_factory import LLMFactory
from src.rag_models.embedding.embedding_factory import EmbeddingFactory
from src.utils.embedder_utils.embedder_warper import EmbeddingWrapper
from src.utils.prompts.prompt import prompt_short, prompt_mc
from src.evaluation.utils import letter_only, build_mc_question, SimilarityScorer, lat_stats

# Constants & helpers
EVAL_DIR = Path(__file__).parent / "eval_outputs"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

# Evaluate one top-k setting
def run_one_topk(
    df: pd.DataFrame,
    collection: str,
    tau: float,
    top_k: int,
    chunk_size: int = 750,
) -> pd.DataFrame:
    chat = Chat(
        model=LLMFactory("llama").llm,
        vectorstore_type="chroma",
        collection_name="turismo_native_chunk_750",
        embedding_model_name="nomic-embed-text",
        chunk_size=750,
        retriever_type="Answer-With-Multiquery",
        max_retrievals= top_k,
    )

    scorer = SimilarityScorer()
    rows: List[Dict] = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"top-k={top_k}"):
        if row["question_type"].strip() != "multiple_choice":
            continue

        chat.prompt = prompt_mc
        question = build_mc_question(row)
        t0 = time.perf_counter()
        chunks: List[str] = []

        async def _ask():
            async for tok in chat.ask_stream(question):
                chunks.append(tok)

        loop.run_until_complete(_ask())
        latency = time.perf_counter() - t0
        model_ans = "".join(chunks).strip()

        pred = letter_only(model_ans)
        opts = [c.strip() for c in row["choices"].split(",")]
        letters = "ABCD"[: len(opts)]
        gold = (
            letters[opts.index(row["correct_answer"].strip())]
            if row["correct_answer"].strip() in opts
            else ""
        )
        if not gold or not pred:
            continue  # skip unusable MC row
        sim = float(pred == gold)
        correct = pred == gold

        rows.append(
            {
                "id": f"MQ_k{top_k}",
                "k": top_k,
                "question_type": "multiple_choice",
                "question": row["question"],
                "gold_choice": gold,
                "pred_choice": pred,
                "model_answer": model_ans,
                "gold_answer": row["correct_answer"],
                "similarity": None,
                "correct": int(correct),
                "latency": latency,
            }
        )

    loop.close()
    return pd.DataFrame(rows)

# ───────────────────────────────────────────────────────────
# Load YAML or JSON config
# ───────────────────────────────────────────────────────────
def load_config(path: Path):
    cfg = yaml.safe_load(path.read_text()) if path.suffix != ".json" else json.loads(path.read_text())
    tau = float(cfg.get("tau", 0.85))
    collection = next(iter(cfg["experiments"].values()))["collection"]
    return collection, tau

# ───────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────


def main():
    p = argparse.ArgumentParser(description="MQ top-k sweep (MC only)")
    p.add_argument("--csv", required=True, help="Questions CSV file")
    p.add_argument("--config", default="eval_config.yaml", help="YAML/JSON with collection & tau")
    p.add_argument("--limit", type=int, default=0, help="Limit #questions (debug)")
    p.add_argument("--klist", default="6,8,10,12,14,20", help="Comma-separated list of K values")
    args = p.parse_args()

    collection, tau = load_config(Path(args.config))
    df_all = pd.read_csv(args.csv)
    df_all = df_all[df_all["question_type"].str.strip() == "multiple_choice"]

    if args.limit:
        df_all = df_all.head(args.limit)
        print(f"[INFO] Limiting to {len(df_all)} short-answer rows …")

    k_values = [int(x) for x in args.klist.split(",")]
    all_frames = []

    output_dir = EVAL_DIR / "MQ-top-k"
    output_dir.mkdir(parents=True, exist_ok=True)

    for k in k_values:
        df_k = run_one_topk(df_all, collection, tau, k)
        all_frames.append(df_k)
        (output_dir / f"results_MQ_k{k}.csv").write_text(df_k.to_csv(index=False))

    full_df = pd.concat(all_frames, ignore_index=True)

    # ─ summary ─
    summ_rows = []
    for k, grp in full_df.groupby("k"):
        acc_mc = grp["correct"].mean() 
        lat_mean, lat_p95, lat_max = lat_stats(grp["latency"])

        summ_rows.append(
            dict(
                k=k,
                accuracy_mc=acc,
                lat_mean_short=lat_mean,
                lat_p95_short=lat_p95,
                lat_max_short=lat_max,
            )
        )

    pd.DataFrame(summ_rows).set_index("k").to_csv(output_dir / "summary_MQMC_topk.csv")
    print("✓ MC evaluation complete. Results saved to", output_dir.resolve())

if __name__ == "__main__":
    main()
