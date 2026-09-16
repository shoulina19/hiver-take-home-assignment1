"""
trivial_baseline.py — Always predicts the majority class intent.
Escalation: never escalates (predicts False for all).
"""
from typing import List, Dict
from src.taxonomy import MAJORITY_CLASS


class TrivialBaseline:
    """
    Baseline 0 (Trivial): Predicts the majority class for every tweet.
    - Intent: always "technical_support" (most common in AppleSupport stream)
    - should_escalate: always False
    - Reply: generic template
    """

    name = "trivial_baseline"

    def predict(self, tweet_text: str) -> Dict:
        return {
            "intent": MAJORITY_CLASS,
            "should_escalate": False,
            "reply": (
                "Hi! Thanks for reaching out to Apple Support. "
                "Please visit https://support.apple.com for help, "
                "or call 1-800-275-2273."
            ),
        }

    def predict_batch(self, tweets: List[Dict]) -> List[Dict]:
        results = []
        for t in tweets:
            pred = self.predict(t["tweet_text"])
            results.append({"id": t["id"], "tweet_text": t["tweet_text"], **pred})
        return results
