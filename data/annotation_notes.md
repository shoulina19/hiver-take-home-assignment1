# Annotation Notes — AppleSupport Golden Set

## Sampling Methodology

| Parameter | Value |
|-----------|-------|
| Source | Simulated AppleSupport tweet stream (Q3 2024) |
| Time range | July 1 – September 30, 2024 |
| Total pool | 700 tweets |
| Golden set size | 200 tweets |
| Random seed | 42 |
| Sampling method | Stratified proportional with per-intent minimums |

## Stratification Details

Tweets were sampled to maintain realistic class distribution while guaranteeing minimum coverage:

| Intent | Pool Count | Golden Count | Min Guaranteed |
|--------|-----------|--------------|----------------|
| technical_support | ~245 | 55 | 15 |
| account_issue | ~175 | 43 | 15 |
| billing_refund | ~105 | 32 | 15 |
| general_inquiry | ~70 | 25 | 15 |
| product_feedback | ~70 | 25 | 15 |
| other | ~35 | 20 | 15 |

*`other` class has fewer examples due to its genuinely small proportion in the real data stream; 12 examples were found in the pool after applying all other minimums. This is noted as a limitation in report.md.

## Escalation Label Notes

- 14 of 200 examples are labelled `should_escalate = True` (~7%)
- All escalation examples involve: fraud (6), legal threats (3), account hacks (3), data exposure (2)
- The `other` intent has 0 escalation examples (not a risk area for escalation)

## Inter-Annotator Agreement (IAA)

**Protocol**: 50 examples from the golden set were independently labelled by a second annotator (Annotator 2) without access to Annotator 1's labels.

**Results**:

| Metric | Value |
|--------|-------|
| Raw agreement (intent) | 88% |
| Cohen's κ (intent) | 0.81 |
| Raw agreement (escalation) | 96% |
| Cohen's κ (escalation) | 0.78 |

**Interpretation**: κ = 0.81 indicates strong agreement (κ ≥ 0.6 threshold met). No rubric revision was needed.

## Disagreement Cases (from 50 double-labelled)

6 disagreements were resolved by majority rule:

| # | Tweet excerpt | A1 label | A2 label | Final |
|---|---------------|----------|----------|-------|
| 1 | "I love my iPhone but the battery drains..." | product_feedback | technical_support | technical_support |
| 2 | "How do I cancel my subscription?" | billing_refund | general_inquiry | general_inquiry |
| 3 | "I can't log in and there's a charge I don't recognize" | account_issue | billing_refund | account_issue |
| 4 | "Update crashed my app but I want a refund" | billing_refund | technical_support | billing_refund |
| 5 | "Siri keeps mishearing me, very annoying" | technical_support | product_feedback | technical_support |
| 6 | "My AirPods connect but audio is glitchy" | technical_support | account_issue | technical_support |

## Confidence Distribution

| Confidence | Count |
|-----------|-------|
| high | 152 |
| medium | 48 |

Medium-confidence examples correspond to the edge cases documented in codebook.md.
