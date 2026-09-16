"""
run_pipeline.py — One-command pipeline entry point.

Usage:
    python run_pipeline.py --brand AppleSupport --sample
    python run_pipeline.py --brand AppleSupport --input data/sample_data.csv
"""
import argparse
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import load_sample_data, save_predictions
from src.trivial_baseline import TrivialBaseline
from src.simple_baseline import SimpleBaseline
from src.primary_agent import PrimaryAgent


def parse_args():
    p = argparse.ArgumentParser(description="AppleSupport Tweet Classification Pipeline")
    p.add_argument("--brand",  default="AppleSupport", help="Brand handle to process")
    p.add_argument("--sample", action="store_true",    help="Use sample_data.csv (quick mode)")
    p.add_argument("--input",  default="data/sample_data.csv", help="Path to input CSV")
    p.add_argument("--limit",  type=int, default=None,  help="Limit number of tweets processed")
    p.add_argument("--skip-llm", action="store_true",   help="Skip primary agent (only run baselines)")
    return p.parse_args()


def run_system(name: str, system, tweets: list, out_dir: str):
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}")
    t0 = time.time()
    predictions = system.predict_batch(tweets)
    elapsed = time.time() - t0
    out_path = os.path.join(out_dir, f"{name}_predictions.json")
    save_predictions(predictions, out_path)
    print(f"  Done in {elapsed:.1f}s → {out_path}")
    return predictions, out_path


def main():
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  AppleSupport Tweet Pipeline — brand: @{args.brand}")
    print(f"{'='*60}\n")

    # ── Load data ────────────────────────────────────────────────────────────
    data_path = args.input
    if not os.path.exists(data_path):
        print(f"[ERROR] Input file not found: {data_path}")
        print("  Run: python generate_sample_data.py  to create sample_data.csv")
        sys.exit(1)

    tweets = load_sample_data(data_path)
    if args.limit:
        tweets = tweets[:args.limit]
    print(f"Loaded {len(tweets)} tweets from {data_path}")

    out_dir = "results"
    os.makedirs(out_dir, exist_ok=True)

    # ── Baseline 0: Trivial ───────────────────────────────────────────────────
    trivial = TrivialBaseline()
    run_system("trivial_baseline", trivial, tweets, out_dir)

    # ── Baseline 1: Simple ────────────────────────────────────────────────────
    simple = SimpleBaseline()
    run_system("simple_baseline", simple, tweets, out_dir)

    # ── Primary Agent ─────────────────────────────────────────────────────────
    if not args.skip_llm:
        agent = PrimaryAgent()
        run_system("primary_agent", agent, tweets, out_dir)
    else:
        print("\n[SKIPPED] Primary agent (--skip-llm flag set)")

    print(f"\n✓ Pipeline complete. Results in ./{out_dir}/")
    print("  Next: python evaluate.py --golden_set data/golden_200.json\n")


if __name__ == "__main__":
    main()
