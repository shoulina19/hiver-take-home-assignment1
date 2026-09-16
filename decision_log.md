# Decision Log — AppleSupport Tweet Classification Pipeline

**Date**: September 2024  
**Author**: Pipeline Design Team

---

> Each entry follows the format: **Decision** → **Why**

---

## D1: Brand Choice — @AppleSupport

**Decision**: Use @AppleSupport as the target brand rather than a smaller brand.  
**Why**: AppleSupport has one of the highest-volume and most-studied Twitter/X support presences. Its intents are well-defined, public datasets exist for validation, and the escalation taxonomy is meaningful (fraud, identity theft are real risks for Apple ID users). A niche brand would have sparse examples and unclear intent boundaries.

---

## D2: Six-Class Intent Taxonomy (not more, not fewer)

**Decision**: Use exactly 6 intents: account_issue, technical_support, billing_refund, product_feedback, general_inquiry, other.  
**Why**: Finer granularity (e.g., splitting technical_support into "iOS bugs" vs "hardware") increases annotation disagreement without adding evaluable signal. Coarser taxonomy (e.g., merging account + billing) obscures escalation logic differences. Six classes balance expressiveness with inter-annotator reliability (κ = 0.81). We explicitly chose NOT to create intent classes for sentiment or urgency — those are captured by `should_escalate`.

---

## D3: `should_escalate` as a Separate Binary Label (not a 7th intent)

**Decision**: Escalation is a separate Boolean field, not an intent class.  
**Why**: Escalation can co-occur with any intent (a billing fraud is both billing_refund AND escalation=True). Collapsing it into an intent would create impossible multi-label classification. The binary formulation also maps directly to the system action: route vs. handle.

---

## D4: Trivial Baseline — Always Predict Majority Class

**Decision**: Baseline 0 always predicts "technical_support" (majority class).  
**Why**: Sets the floor: any model that can't beat a constant predictor is useless. Also reveals class imbalance effects — if trivial baseline scores 35% accuracy, you know ~35% of tweets are technical_support. We deliberately chose NOT to use a random baseline because it's less interpretable.

---

## D5: Simple Baseline — Keyword Matching, Not TF-IDF/Logistic Regression

**Decision**: Simple baseline uses keyword/regex matching rather than a trained ML model.  
**Why**: A trained ML baseline would require a train/test split, complicating the evaluation design (the golden set is test-only). Keyword matching is reproducible without any training data, runs in milliseconds, and is a realistic comparison point for a rule-based system that many support teams actually deploy. We explicitly chose NOT to train an ML baseline.

---

## D6: LLM-as-Judge at Temperature=0

**Decision**: Judge runs at temperature=0, not 0.2 or higher.  
**Why**: Reproducibility is the primary requirement for a judge. Temperature=0 gives deterministic outputs (for greedy decoding). The trade-off is some loss of output diversity, but for a scoring rubric this is desirable — we want consistent, not creative, judgements.

---

## D7: Four-Criteria Rubric (not a single holistic score)

**Decision**: Judge evaluates on 4 separate criteria (correctness, helpfulness, empathy, brand_safety) rather than one overall quality score.  
**Why**: A single holistic score conflates very different dimensions. Correctness and brand_safety can disagree (a correct reply can be harsh). Per-criterion scores also allow per-criterion human-judge agreement measurement, making the κ more granular and actionable.

---

## D8: Measuring Judge-Human Agreement on 50 Examples (not 10)

**Decision**: Human-judge agreement measured on 50 examples, reporting both raw % and Cohen's κ.  
**Why**: Raw percentage agreement is inflated by chance agreement (if judge and human each give "3" 70% of the time, agreement looks high even randomly). κ corrects for chance. 50 examples is the minimum for a reasonably stable κ estimate. We explicitly chose NOT to report only percentage agreement.

---

## D9: Bootstrap Confidence Intervals on Accuracy

**Decision**: Report 95% bootstrap CI on intent accuracy, not just the point estimate.  
**Why**: A headline number without uncertainty is misleading. With n=200, a 1% difference in accuracy is within noise. CI makes this explicit. We use bootstrap (not normal approximation) because accuracy distributions can be skewed at extremes.

---

## D10: Golden Set is Test-Only (no train/dev split)

**Decision**: The 200-example golden set is used exclusively for evaluation, not for any training or prompt tuning.  
**Why**: If any labelled examples were used to tune prompts or pick hyperparameters, the evaluation would be contaminated. All prompt design was done using unlabelled tweets. This also means the LLM baseline is truly zero-shot.

---

## D11: Stratified Sampling with Minimum 15 Examples Per Class

**Decision**: Golden set sampled with proportional stratification and a 15-example floor per intent.  
**Why**: Without a floor, low-frequency classes (like "other") would have too few examples to measure per-class F1 reliably. 15 is the minimum where F1 variance is manageable. We explicitly chose NOT to oversample minority classes beyond the floor, to preserve realistic class distribution for macro F1.

---

## D12: `other` Class Rate — Honest About Its Low Count

**Decision**: Include "other" class even though it has only 12 examples (slightly below 15 minimum).  
**Why**: Artificially inflating the "other" class would make the problem look easier than it is (more examples to learn from in a real system). The real @AppleSupport stream genuinely has few off-topic tweets. We document this in annotation_notes.md and flag it in the "What Is Misleading" section.

---

## D13: Scope Cut — No Fine-Tuning

**Decision**: We do not fine-tune any model; all systems are zero-shot or rule-based.  
**Why**: Fine-tuning requires a labelled training set, infrastructure, and days of compute — incompatible with the project timeline. The assignment asks to prove the evaluation framework works, not to maximise accuracy. The honest comparison between zero-shot LLM and keyword baseline is more instructive than a fine-tuned model with no eval rigour.

---

## D14: Scope Cut — No Real Tweet Data

**Decision**: Use realistically simulated tweet data rather than scraped @AppleSupport tweets.  
**Why**: Live Twitter/X API access requires approval and rate limits. GDPR and Twitter ToS restrict republishing scraped content. The simulated data preserves the stylistic characteristics (abbreviations, hashtags, @mentions, urgency language) of real support tweets while avoiding legal and access barriers. This is noted as a limitation.

---

## D15: Fallback Architecture — Simple Baseline if No API Key

**Decision**: Primary agent gracefully degrades to simple_baseline output when OPENAI_API_KEY is absent.  
**Why**: The pipeline must be runnable by evaluators who don't have API keys. Failing hard would prevent any end-to-end execution. The fallback is clearly logged so evaluators know which system ran. This is preferable to mocking LLM responses with random outputs.
