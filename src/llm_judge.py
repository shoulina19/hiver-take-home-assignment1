"""
llm_judge.py — LLM-as-judge evaluator with 4-criteria rubric.
Runs at temperature=0. Falls back to heuristic scoring if no API key.
"""
import os
import json
import re
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────── Rubric ───────────────────────────────────────────
JUDGE_RUBRIC = """
You are a strict, impartial quality evaluator for Apple Support tweet responses.
Evaluate the GENERATED REPLY against the TWEET and INTENT.

Score each criterion 1–5 (integers only):

1. CORRECTNESS (1-5): Does the reply correctly address the user's actual problem?
   1=completely wrong/irrelevant, 3=partially relevant, 5=fully correct and accurate

2. HELPFULNESS (1-5): Does the reply provide actionable next steps or resolution?
   1=no actionable help, 3=vague help, 5=clear, specific, immediately actionable

3. EMPATHY (1-5): Does the reply acknowledge the user's frustration/emotion appropriately?
   1=robotic/dismissive, 3=neutral, 5=warm, empathetic, personalised

4. BRAND_SAFETY (1-5): Is the reply on-brand for Apple Support (professional, no harm, no PII)?
   1=harmful/off-brand, 3=acceptable, 5=exemplary Apple tone

Respond ONLY with valid JSON, no markdown:
{
  "correctness": <1-5>,
  "helpfulness": <1-5>,
  "empathy": <1-5>,
  "brand_safety": <1-5>,
  "overall": <average of four, one decimal>,
  "rationale": "<one sentence explanation>"
}
"""
# ──────────────────────────────────────────────────────────────────────────────

_JSON_PAT = re.compile(r"\{.*\}", re.DOTALL)
_CRITERIA = ["correctness", "helpfulness", "empathy", "brand_safety"]


def _heuristic_score(tweet: str, intent: str, reply: str) -> Dict:
    """Fallback heuristic judge when API is unavailable."""
    score = {}
    # Correctness: intent keyword in reply?
    intent_words = {"account_issue": ["account","apple id","password"],
                    "technical_support": ["restart","update","support.apple.com"],
                    "billing_refund": ["refund","reportaproblem","charge"],
                    "product_feedback": ["feedback","appreciate","suggestion"],
                    "general_inquiry": ["support.apple.com","find","available"],
                    "other": ["dm","contact","help"]}
    words = intent_words.get(intent, [])
    hits = sum(1 for w in words if w.lower() in reply.lower())
    score["correctness"] = min(5, max(1, 2 + hits * 2))
    score["helpfulness"] = 3 if len(reply) > 60 else 2
    score["empathy"] = 3 if any(w in reply.lower() for w in ["sorry","understand","thanks","hi"]) else 2
    score["brand_safety"] = 4  # assume safe
    overall = sum(score.values()) / 4
    score["overall"] = round(overall, 1)
    score["rationale"] = "Heuristic score (no LLM judge available)"
    return score


class LLMJudge:
    """
    Evaluates system replies against 4 criteria.
    Runs at temperature=0 for reproducibility.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        self.model = os.getenv("JUDGE_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.client = None

        if api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                self.client = OpenAI(**kwargs)
                print(f"[llm_judge] Using LLM judge: {self.model} at temperature=0")
            except Exception as e:
                print(f"[llm_judge] Init failed: {e}. Using heuristic fallback.")
        else:
            print("[llm_judge] No OPENAI_API_KEY. Using heuristic judge.")

    def _call_judge(self, tweet: str, intent: str, reply: str) -> Optional[Dict]:
        if not self.client:
            return None
        user_msg = f"Tweet: {tweet}\nIntent: {intent}\nGenerated Reply: {reply}"
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": JUDGE_RUBRIC},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0,
                max_tokens=200,
                timeout=30,
            )
            raw = resp.choices[0].message.content.strip()
            m = _JSON_PAT.search(raw)
            if m:
                data = json.loads(m.group())
                # Clamp
                for c in _CRITERIA:
                    data[c] = max(1, min(5, int(data.get(c, 3))))
                data["overall"] = round(sum(data[c] for c in _CRITERIA) / 4, 1)
                return data
        except Exception as e:
            print(f"  [llm_judge] Call failed: {e}")
        return None

    def score(self, tweet: str, intent: str, reply: str) -> Dict:
        result = self._call_judge(tweet, intent, reply)
        if result is None:
            result = _heuristic_score(tweet, intent, reply)
        return result

    def score_batch(
        self,
        predictions: List[Dict],
        delay: float = 0.1,
    ) -> List[Dict]:
        """Score a list of prediction dicts; adds 'judge_scores' key."""
        results = []
        for i, pred in enumerate(predictions):
            if i % 20 == 0:
                print(f"  [llm_judge] Judging {i}/{len(predictions)}...")
            scores = self.score(
                tweet=pred["tweet_text"],
                intent=pred["intent"],
                reply=pred.get("reply", ""),
            )
            results.append({**pred, "judge_scores": scores})
            time.sleep(delay)
        return results

    def compute_judge_summary(self, judged: List[Dict]) -> Dict:
        """Aggregate judge scores across all examples."""
        all_scores = {c: [] for c in _CRITERIA}
        all_scores["overall"] = []
        for item in judged:
            js = item.get("judge_scores", {})
            for c in _CRITERIA:
                if c in js:
                    all_scores[c].append(js[c])
            if "overall" in js:
                all_scores["overall"].append(js["overall"])

        summary = {}
        for c, vals in all_scores.items():
            if vals:
                summary[f"avg_{c}"] = round(sum(vals) / len(vals), 3)
        return summary

    def compute_human_agreement(
        self,
        human_scores: List[Dict],
        judge_scores: List[Dict],
        n_samples: int = 50,
    ) -> Dict:
        """
        Compute Cohen's κ between human and LLM judge on the first n_samples examples.
        Expects both lists to be aligned by index.
        human_scores: list of dicts with criterion keys
        judge_scores: list of dicts with criterion keys
        """
        from src.metrics import cohen_kappa
        n = min(n_samples, len(human_scores), len(judge_scores))
        results = {}
        for c in _CRITERIA:
            h = [h.get(c, 3) for h in human_scores[:n]]
            j = [j.get(c, 3) for j in judge_scores[:n]]
            kappa = cohen_kappa(h, j, labels=list(range(1, 6)))
            results[f"kappa_{c}"] = round(kappa, 4)
        all_h = [h.get(c, 3) for h in human_scores[:n] for c in _CRITERIA]
        all_j = [j.get(c, 3) for j in judge_scores[:n] for c in _CRITERIA]
        results["kappa_overall"] = round(cohen_kappa(all_h, all_j, labels=list(range(1, 6))), 4)
        results["n_compared"] = n
        return results
