"""
evaluate.py — Evaluation harness.

Usage:
    python evaluate.py --golden_set data/golden_200.json
    python evaluate.py --golden_set data/golden_200.json --judge
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import load_golden_set
from src.metrics import compute_all_metrics
from src.llm_judge import LLMJudge
from src.taxonomy import INTENTS


def load_predictions(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def print_results_table(results: list):
    headers = ["System", "Intent Acc", "95% CI", "Macro F1", "Esc Prec", "Esc Rec", "Cohen κ"]
    rows = []
    for r in results:
        ci = r["intent_accuracy_95ci"]
        rows.append([
            r["system"],
            f"{r['intent_accuracy']:.3f}",
            f"[{ci[0]:.3f}, {ci[1]:.3f}]",
            f"{r['macro_f1']:.3f}",
            f"{r['escalation']['precision']:.3f}",
            f"{r['escalation']['recall']:.3f}",
            f"{r['cohen_kappa_intent']:.3f}",
        ])
    # Format table
    col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    def fmt_row(row):
        return "| " + " | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + " |"
    print("\n" + sep)
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(sep + "\n")


def parse_args():
    p = argparse.ArgumentParser(description="Evaluation Harness for AppleSupport Pipeline")
    p.add_argument("--golden_set", default="data/golden_200.json", help="Path to golden set JSON")
    p.add_argument("--results_dir", default="results", help="Directory with *_predictions.json files")
    p.add_argument("--judge",  action="store_true", help="Run LLM judge on primary_agent predictions")
    p.add_argument("--output", default="results/eval_report.json", help="Output eval report path")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Evaluation Harness — golden set: {args.golden_set}")
    print(f"{'='*60}\n")

    # ── Load golden set ───────────────────────────────────────────────────────
    if not os.path.exists(args.golden_set):
        print(f"[ERROR] Golden set not found: {args.golden_set}")
        sys.exit(1)

    golden = load_golden_set(args.golden_set)
    print(f"Loaded {len(golden)} golden examples")

    # ── Find prediction files ─────────────────────────────────────────────────
    systems = ["trivial_baseline", "simple_baseline", "primary_agent"]
    all_metrics = []
    found_preds = {}

    for sys_name in systems:
        pred_path = os.path.join(args.results_dir, f"{sys_name}_predictions.json")
        if os.path.exists(pred_path):
            preds = load_predictions(pred_path)
            m = compute_all_metrics(golden, preds, INTENTS, system_name=sys_name)
            all_metrics.append(m)
            found_preds[sys_name] = preds
            print(f"✓ {sys_name}: {len(preds)} predictions loaded")
        else:
            print(f"✗ {sys_name}: No predictions found at {pred_path} — skipping")

    if not all_metrics:
        print("[ERROR] No prediction files found. Run run_pipeline.py first.")
        sys.exit(1)

    # ── Print results table ───────────────────────────────────────────────────
    print("\n━━━  Automatic Metrics  ━━━")
    print_results_table(all_metrics)

    # Per-class F1 for primary agent
    if "primary_agent" in found_preds:
        pa_metrics = next(m for m in all_metrics if m["system"] == "primary_agent")
        print("Per-class F1 (primary_agent):")
        for cls, f1 in pa_metrics["per_class_f1"].items():
            print(f"  {cls:<22} {f1:.3f}")
        print()

    # ── Honest analysis: metrics that lose to simple baseline ─────────────────
    if len(all_metrics) >= 3:
        simple_m = next((m for m in all_metrics if m["system"] == "simple_baseline"), None)
        primary_m = next((m for m in all_metrics if m["system"] == "primary_agent"), None)
        if simple_m and primary_m:
            print("━━━  Honest Comparison: Primary Agent vs Simple Baseline  ━━━")
            for metric_key, label in [
                ("intent_accuracy", "Intent Accuracy"),
                ("macro_f1", "Macro F1"),
            ]:
                diff = primary_m[metric_key] - simple_m[metric_key]
                sign = "+" if diff >= 0 else ""
                note = "✓ Primary wins" if diff >= 0 else "⚠  Simple baseline wins — see report for analysis"
                print(f"  {label}: {sign}{diff:.3f}  ({note})")
            print()

    # ── LLM Judge ─────────────────────────────────────────────────────────────
    judge_summary = {}
    if args.judge and "primary_agent" in found_preds:
        print("━━━  LLM Judge (temperature=0)  ━━━")
        judge = LLMJudge()
        judged = judge.score_batch(found_preds["primary_agent"][:50])  # first 50 for speed
        judge_summary = judge.compute_judge_summary(judged)
        print("Judge score averages (primary_agent, n=50):")
        for k, v in judge_summary.items():
            print(f"  {k:<30} {v}")

        # Save judged predictions
        judged_path = os.path.join(args.results_dir, "primary_agent_judged.json")
        with open(judged_path, "w") as f:
            json.dump(judged, f, indent=2)
        print(f"\nJudged predictions saved → {judged_path}")

        # Human-judge agreement note
        haj_path = os.path.join(args.results_dir, "human_judge_agreement.json")
        if os.path.exists(haj_path):
            with open(haj_path) as f:
                haj = json.load(f)
            print("\nHuman-Judge Agreement (Cohen's κ):")
            for k, v in haj.items():
                flag = ""
                if "kappa" in k and isinstance(v, float) and v < 0.6:
                    flag = "  ⚠ κ < 0.6 — see rubric revision history"
                print(f"  {k:<30} {v}{flag}")
        else:
            print(f"\n[NOTE] Human-judge agreement file not found at {haj_path}")
            print("  To measure agreement: annotate 50 examples manually, then:")
            print("  python scripts/compute_human_agreement.py")
    elif args.judge:
        print("[WARN] --judge flag set but primary_agent predictions not found.")

    # ── Save full eval report ─────────────────────────────────────────────────
    report = {
        "evaluation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "golden_set_size": len(golden),
        "metrics": all_metrics,
        "judge_summary": judge_summary,
    }
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Full eval report saved → {args.output}\n")


if __name__ == "__main__":
    main()
