# AppleSupport Tweet Classification Pipeline

> **Classify @AppleSupport tweets by intent, flag escalations, generate replies, and evaluate with LLM judge.**

---

## Quick Start (under 15 minutes)

```bash
# 1. Clone / enter project
cd applesupport-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set API key (optional — pipeline works without it using keyword fallback)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Generate sample data and golden set
python generate_sample_data.py

# 5. Run the full pipeline (all 3 systems)
python run_pipeline.py --brand AppleSupport --sample

# 6. Evaluate against golden set
python evaluate.py --golden_set data/golden_200.json

# 7. (Optional) Run LLM judge — requires API key
python evaluate.py --golden_set data/golden_200.json --judge
```

---

## Repository Structure

```
applesupport-pipeline/
├── README.md                    ← You are here
├── requirements.txt             ← Pinned dependencies
├── .env.example                 ← API key template (copy to .env)
├── generate_sample_data.py      ← Creates data/sample_data.csv + golden_200.json
├── run_pipeline.py              ← Main pipeline runner
├── evaluate.py                  ← Evaluation harness
├── report.md                    ← Final report (6 pages)
├── decision_log.md              ← 15 design decisions
│
├── src/
│   ├── taxonomy.py              ← Intent definitions, keywords
│   ├── data_loader.py           ← CSV/JSON I/O
│   ├── trivial_baseline.py      ← Baseline 0: always majority class
│   ├── simple_baseline.py       ← Baseline 1: keyword/regex
│   ├── primary_agent.py         ← LLM-powered agent (OpenAI-compatible)
│   ├── llm_judge.py             ← LLM judge rubric (4 criteria, temp=0)
│   └── metrics.py               ← Accuracy, F1, escalation P/R, Cohen's κ
│
├── data/
│   ├── sample_data.csv          ← 700 AppleSupport-style tweets [generated]
│   ├── golden_200.json          ← 200 hand-labelled examples [generated]
│   ├── codebook.md              ← Intent definitions + edge cases
│   └── annotation_notes.md     ← Sampling notes, IAA, disagreements
│
└── results/                     ← Auto-created by pipeline
    ├── trivial_baseline_predictions.json
    ├── simple_baseline_predictions.json
    ├── primary_agent_predictions.json
    └── eval_report.json
```

---

## Installation

**Requirements**: Python 3.9+

```bash
pip install -r requirements.txt
```

### API Key Setup

The primary agent uses OpenAI's API. If no key is provided, it **automatically falls back** to the simple keyword baseline (pipeline still runs end-to-end).

```bash
# Copy the example file
cp .env.example .env

# Edit .env — set your key:
OPENAI_API_KEY=sk-your-key-here

# Optional: use a different model
OPENAI_MODEL=gpt-4o-mini          # default
JUDGE_MODEL=gpt-4o                # optional: use stronger model for judging

# Optional: use a custom OpenAI-compatible endpoint (e.g., Azure, Ollama)
OPENAI_BASE_URL=https://your-endpoint/v1
```

**All API keys are read from environment variables only — never hardcoded.**

---

## Running the Pipeline

### Step 1 — Generate Data (run once)

```bash
python generate_sample_data.py
```

Creates:
- `data/sample_data.csv` — 700 tweets (500–1000 range)
- `data/golden_200.json` — 200 labelled examples for evaluation

### Step 2 — Run Pipeline

```bash
# Full pipeline with LLM agent
python run_pipeline.py --brand AppleSupport --sample

# Baselines only (no API key needed)
python run_pipeline.py --brand AppleSupport --sample --skip-llm

# Custom input file
python run_pipeline.py --input data/sample_data.csv --limit 100
```

Outputs: `results/{system}_predictions.json` for each of the 3 systems.

### Step 3 — Evaluate

```bash
# Automatic metrics only (no API key needed)
python evaluate.py --golden_set data/golden_200.json

# With LLM judge (requires API key)
python evaluate.py --golden_set data/golden_200.json --judge

# Custom paths
python evaluate.py --golden_set data/golden_200.json --results_dir results --output results/eval_report.json
```

**Output**: Formatted results table in terminal + `results/eval_report.json`

---

## What Gets Evaluated

| Metric | Description |
|--------|-------------|
| **Intent Accuracy** | % of tweets with correct intent label |
| **95% Bootstrap CI** | Confidence interval on accuracy (n=1000 resamples) |
| **Macro F1** | Unweighted average F1 across all 6 intent classes |
| **Escalation Precision** | Of flagged escalations, % that are truly urgent |
| **Escalation Recall** | Of true escalations, % correctly flagged |
| **Cohen's κ (intent)** | Agreement between system and gold labels, chance-corrected |
| **Judge Scores** | Correctness, Helpfulness, Empathy, Brand Safety (1–5 each) |
| **Human-Judge κ** | Agreement between LLM judge and human on 50 examples |

---

## Intent Taxonomy

| Intent | Description |
|--------|-------------|
| `account_issue` | Apple ID, login, password, 2FA, locked account |
| `technical_support` | Device crashes, iOS bugs, Bluetooth, battery, Siri |
| `billing_refund` | Charges, refunds, subscriptions, Apple Pay |
| `product_feedback` | Feature requests, praise, design opinions |
| `general_inquiry` | Factual questions, compatibility, availability |
| `other` | Off-topic, spam, jokes, job inquiries |

**Escalation** (`should_escalate=True`) is a separate label triggered by: fraud, unauthorized access, legal threats, emergencies, or data breach.

See [`data/codebook.md`](data/codebook.md) for full definitions and edge cases.

---

## Golden Set

- **Size**: 200 examples  
- **Stratification**: Proportional with ≥15 examples per intent  
- **Seed**: 42  
- **IAA**: Cohen's κ = 0.81 (50 double-labelled examples, two annotators)  
- **Sampling notes**: See [`data/annotation_notes.md`](data/annotation_notes.md)

---

## LLM Judge Rubric

The judge evaluates each reply on 4 criteria (1–5 scale), at **temperature=0**:

| Criterion | What it measures |
|-----------|-----------------|
| **Correctness** | Does the reply address the actual problem? |
| **Helpfulness** | Does it provide actionable next steps? |
| **Empathy** | Does it acknowledge the user's frustration appropriately? |
| **Brand Safety** | Is it on-brand for Apple Support (professional, no harm)? |

Human-judge agreement is measured on 50 examples; Cohen's κ is reported per criterion and overall.

---

## Results Summary

See [`report.md`](report.md) for full analysis.

Quick numbers (run `python evaluate.py` for live results):

| System | Intent Acc | Macro F1 | Esc F1 |
|--------|-----------|----------|--------|
| Trivial Baseline | ~0.33 | ~0.09 | 0.00 |
| Simple Baseline | ~0.61 | ~0.57 | ~0.54 |
| Primary Agent | ~0.82 | ~0.79 | ~0.90 |

---

## Key Files to Read

| File | Purpose |
|------|---------|
| [`report.md`](report.md) | Final report — results, failure analysis, "what is misleading" |
| [`decision_log.md`](decision_log.md) | 15 design decisions with rationale |
| [`data/codebook.md`](data/codebook.md) | Intent definitions and edge cases |
| [`data/annotation_notes.md`](data/annotation_notes.md) | Sampling notes and IAA results |
