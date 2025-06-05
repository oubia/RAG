from __future__ import annotations

import argparse
import asyncio
import json
import re
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

from src.chat.chat import Chat
from src.models.llm_factory import LLMFactory
from src.rag_models.embedding.embedding_factory import EmbeddingFactory
from src.utils.embedder_utils.embedder_warper import EmbeddingWrapper
from src.utils.prompts.prompt import prompt_short, prompt_mc
from src.utils.prompts.prompt import _ZERO_CORE, prompt_short_zero, prompt_mc_zero
from src.evaluation.utils import letter_only, build_mc_question, SimilarityScorer, lat_stats


# # ───────────────────────────────────────────────────────────
# # Constants & helpers
# # ───────────────────────────────────────────────────────────
EVAL_DIR = Path(__file__).parent / "eval_outputs"
# EVAL_DIR.mkdir(parents=True, exist_ok=True)

# _RE_MC = re.compile(r"(?:^|[^A-D])\s*([ABCD])\s*(?:[)\.:,;!?\n]|$)")


# def _letter_only(txt: str) -> str:
#     """Return first standalone A-D (or empty)."""
#     m = _RE_MC.search(txt)
#     if m:
#         return m.group(1).upper()
#     for ch in txt:
#         if ch in "ABCD":
#             return ch
#     return ""


# ───────────────────────────────────────────────────────────
# Data classes
# ───────────────────────────────────────────────────────────
@dataclass
class Experiment:
    id: str
    collection: str
    retriever_method: str
    chunk_size: int


# # ───────────────────────────────────────────────────────────
# # Question utils
# # ───────────────────────────────────────────────────────────
# def build_mc_question(row: pd.Series) -> str:
#     base = row["question"].strip()
#     opts = [c.strip() for c in row["choices"].split(",")]
#     mc_lines = "\n".join(f"{l}) {o}" for l, o in zip("ABCD", opts))
#     return textwrap.dedent(f"{base}\n\nSCELTE\n{mc_lines}")


# # ───────────────────────────────────────────────────────────
# # Similarity scorer
# # ───────────────────────────────────────────────────────────
# class SimilarityScorer:
#     def __init__(self, model_name: str = "nomic-embed-text"):
#         emb = EmbeddingFactory.get_embedding_model(model_name)
#         self._embedder = EmbeddingWrapper(emb)
#         self._cache: Dict[str, np.ndarray] = {}

#     def _vec(self, txt: str) -> np.ndarray:
#         if txt not in self._cache:
#             self._cache[txt] = np.array(
#                 self._embedder.embed_query(txt), dtype=np.float32
#             )
#         return self._cache[txt]

#     def cosine(self, a: str, b: str) -> float:
#         va, vb = self._vec(a), self._vec(b)
#         return float((va @ vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))


# ───────────────────────────────────────────────────────────
# Track evaluation
# ───────────────────────────────────────────────────────────
def evaluate_track(exp: Experiment, df: pd.DataFrame, tau: float) -> pd.DataFrame:
    scorer = SimilarityScorer()
    llm = LLMFactory("llama").llm

    retr_map = {
        "answer_with_similarity": "Similarity-search",
        "answer_with_multiquery": "MultiQuery",
        "answer_with_hybrid": "Hybrid-fusion",
        "answer_with_contextual": "Contextual-Compression",
    }

    chat = Chat(
        model=llm,
        vectorstore_type="chroma",
        collection_name=exp.collection,
        embedding_model_name="nomic-embed-text",
        chunk_size=exp.chunk_size,
        retriever_type=retr_map[exp.retriever_method],
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    rows: List[Dict] = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc=exp.id):
        q_type = row["question_type"].strip()
        if q_type == "multiple_choice":
            chat.prompt = prompt_mc
            question = build_mc_question(row)
        else:
            chat.prompt = prompt_short
            question = row["question"].strip()

        # ── timed LLM call ──
        t0 = time.perf_counter()
        chunks: List[str] = []

        async def _ask():
            async for tok in chat.ask_stream(question):
                chunks.append(tok)

        loop.run_until_complete(_ask())
        latency = time.perf_counter() - t0
        model_ans = "".join(chunks).strip()

        # ── scoring ──
        if q_type == "multiple_choice":
<<<<<<< HEAD
            pred = _letter_only(model_ans)
=======
            pred = letter_only(model_ans)
>>>>>>> recovered-enhance-eval
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
        else:
            gold = pred = None
            sim = scorer.cosine(model_ans, row["answer"].strip())
            correct = sim >= tau

        rows.append(
            {
                "id": exp.id,
                "question": row["question"],
                "question_type": q_type,
                "gold_choice": gold,
                "pred_choice": pred,
                "model_answer": model_ans,
                "gold_answer": row["correct_answer"],
                "similarity": sim,
                "correct": int(correct),
                "latency": latency,
            }
        )

    loop.close()
    return pd.DataFrame(rows)


# ───────────────────────────────────────────────────────────
# Config loader
# ───────────────────────────────────────────────────────────
def load_config(path: Path) -> Tuple[Dict[str, Experiment], float]:
    cfg = (
        json.loads(path.read_text())
        if path.suffix == ".json"
        else yaml.safe_load(path.read_text())
    )
    tau = float(cfg.get("tau", 0.85))
    exps = {
        k: Experiment(
            id=k,
            collection=v["collection"],
            retriever_method=v["method"],
            chunk_size=int(v["chunk_size"]),
        )
        for k, v in cfg["experiments"].items()
    }
    return exps, tau


# ───────────────────────────────────────────────────────────
# Latency stats helper
# ───────────────────────────────────────────────────────────
def _lat_stats(series: pd.Series) -> Tuple[float, float, float]:
    if series.empty:
        return np.nan, np.nan, np.nan
    return float(series.mean()), float(series.quantile(0.95)), float(series.max())

# ───────────────────────────────────────────────────────────
# Zero-shot evaluation
# ───────────────────────────────────────────────────────────
def evaluate_zero_shot(df: pd.DataFrame, tau: float) -> pd.DataFrame:
    scorer = SimilarityScorer()
    llm = LLMFactory("llama", system_prompt=_ZERO_CORE).get_llm()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    rows: List[Dict] = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="baseline-zero"):
        q_type = row["question_type"].strip()

        if q_type == "multiple_choice":
            prompt = prompt_mc_zero
            question = build_mc_question(row)
        else:
            prompt = prompt_short_zero
            question = row["question"].strip()

        full_prompt = prompt.format(context="", question=question)
        t0 = time.perf_counter()
        chunks: List[str] = []
        print(full_prompt)
        async def _ask():
            async for tok in llm.astream(full_prompt):
                chunks.append(tok)

        loop.run_until_complete(_ask())
        latency = time.perf_counter() - t0
        model_ans = "".join(chunks).strip()
        print(f"Model answer: {model_ans}")
        if q_type == "multiple_choice":
            pred = _letter_only(model_ans)
            opts = [c.strip() for c in row["choices"].split(",")]
            letters = "ABCD"[: len(opts)]
            gold = (
                letters[opts.index(row["correct_answer"].strip())]
                if row["correct_answer"].strip() in opts
                else ""
            )
            if not gold or not pred:
                continue
            sim = float(pred == gold)
            correct = pred == gold
        else:
            gold = pred = None
            sim = scorer.cosine(model_ans, row["answer"].strip())
            correct = sim >= tau

        rows.append(
            {
                "id": "baseline-zero",
                "question": row["question"],
                "question_type": q_type,
                "gold_choice": gold,
                "pred_choice": pred,
                "model_answer": model_ans,
                "gold_answer": row["correct_answer"],
                "similarity": sim,
                "correct": int(correct),
                "latency": latency,
            }
        )

    loop.close()
    df_result = pd.DataFrame(rows)

    # Save summary just for zero-shot
    mc_mask = df_result.question_type == "multiple_choice"
    sh_mask = ~mc_mask

    summary = {
        "id": "baseline-zero",
        "accuracy_mc": df_result.loc[mc_mask, "correct"].mean() if mc_mask.any() else np.nan,
        "accuracy_short": df_result.loc[sh_mask, "correct"].mean() if sh_mask.any() else np.nan,
        "mean_similarity_short": df_result.loc[sh_mask, "similarity"].mean() if sh_mask.any() else np.nan,
        "lat_mean_mc": df_result.loc[mc_mask, "latency"].mean() if mc_mask.any() else np.nan,
        "lat_p95_mc": df_result.loc[mc_mask, "latency"].quantile(0.95) if mc_mask.any() else np.nan,
        "lat_max_mc": df_result.loc[mc_mask, "latency"].max() if mc_mask.any() else np.nan,
        "lat_mean_short": df_result.loc[sh_mask, "latency"].mean() if sh_mask.any() else np.nan,
        "lat_p95_short": df_result.loc[sh_mask, "latency"].quantile(0.95) if sh_mask.any() else np.nan,
        "lat_max_short": df_result.loc[sh_mask, "latency"].max() if sh_mask.any() else np.nan,
    }

    pd.DataFrame([summary]).set_index("id").to_csv(EVAL_DIR / "summary_baseline-zero.csv")

    return df_result

# ───────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Evaluate RAG tracks with latency")
    p.add_argument("--csv", required=True)
    p.add_argument("--config", default="eval_config.yaml")
    p.add_argument("--tau", type=float)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--zero-shot", action="store_true",
                   help="Run a zero-shot LLM baseline (no retrieval)")

    args = p.parse_args()

    exps, tau_cfg = load_config(Path(args.config))
    tau = args.tau if args.tau is not None else tau_cfg

    df_all = pd.read_csv(args.csv)
    if args.limit:
        df_all = df_all.head(args.limit)
        print(f"[INFO] Limiting to {len(df_all)} rows …")

    tracks: List[pd.DataFrame] = []

    # ─────────────────────────────────────────────────────────────
    # Run zero-shot baseline (optional)
    # ─────────────────────────────────────────────────────────────
    if args.zero_shot:
        df_zero = evaluate_zero_shot(df_all, tau)
        tracks.append(df_zero)
        (EVAL_DIR / "resultstest_baseline-zero.csv").write_text(
            df_zero.to_csv(index=False)
        )

    # ─────────────────────────────────────────────────────────────
    # Evaluate RAG experiment tracks
    # ─────────────────────────────────────────────────────────────
    else:
        for exp in exps.values():
            df_track = evaluate_track(exp, df_all, tau)
            tracks.append(df_track)
            (EVAL_DIR / f"results_{exp.id}111.csv").write_text(
                df_track.to_csv(index=False)
            )

        # ─────────────────────────────────────────────────────────────
        # Combine and summarize
        # ─────────────────────────────────────────────────────────────
        full_df = pd.concat(tracks, ignore_index=True)

        summary_rows = []
        for exp_id, grp in full_df.groupby("id"):
            mc_mask = grp.question_type == "multiple_choice"
            sh_mask = ~mc_mask

            acc_mc = grp.loc[mc_mask, "correct"].mean() if mc_mask.any() else np.nan
            acc_sh = grp.loc[sh_mask, "correct"].mean() if sh_mask.any() else np.nan
            sim_sh = grp.loc[sh_mask, "similarity"].mean() if sh_mask.any() else np.nan

            lat_mean_mc, lat_p95_mc, lat_max_mc = _lat_stats(grp.loc[mc_mask, "latency"])
            lat_mean_sh, lat_p95_sh, lat_max_sh = _lat_stats(grp.loc[sh_mask, "latency"])

            summary_rows.append(
                {
                    "id": exp_id,
                    "accuracy_mc": acc_mc,
                    "accuracy_short": acc_sh,
                    "mean_similarity_short": sim_sh,
                    "lat_mean_mc": lat_mean_mc,
                    "lat_p95_mc": lat_p95_mc,
                    "lat_max_mc": lat_max_mc,
                    "lat_mean_short": lat_mean_sh,
                    "lat_p95_short": lat_p95_sh,
                    "lat_max_short": lat_max_sh,
                }
            )

        summary_df = pd.DataFrame(summary_rows).set_index("id")
        (EVAL_DIR / "results_summarytest1111.csv").write_text(summary_df.to_csv())


if __name__ == "__main__":
    import sys, os
    print("CWD:", os.getcwd())
    print("PYTHONPATH:", sys.path)

    main()
