"""
simple_baseline.py — Keyword/regex-based intent classifier.
Escalation: triggered by presence of escalation keywords.
"""
import re
from typing import List, Dict
from src.taxonomy import INTENT_KEYWORDS, ESCALATION_KEYWORDS, INTENTS

# Pre-compile escalation pattern
_ESC_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in ESCALATION_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Pre-compile per-intent patterns and count weights
_INTENT_PATTERNS = {
    intent: re.compile(
        r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b",
        re.IGNORECASE,
    )
    for intent, keywords in INTENT_KEYWORDS.items()
}

_REPLY_TEMPLATES = {
    "account_issue": (
        "We're sorry you're having trouble with your Apple ID. "
        "Please visit https://iforgot.apple.com to reset your credentials. "
        "DM us if you need further help!"
    ),
    "technical_support": (
        "Thanks for reaching out! Please try restarting your device and checking "
        "for software updates at Settings > General > Software Update. "
        "Still stuck? Visit https://support.apple.com."
    ),
    "billing_refund": (
        "We understand billing concerns are urgent. Please visit "
        "https://reportaproblem.apple.com to request a refund or review your charges. "
        "DM us with your order number for faster help."
    ),
    "product_feedback": (
        "Thank you for your feedback! We pass all suggestions to our product teams. "
        "You can also submit feedback at https://www.apple.com/feedback/."
    ),
    "general_inquiry": (
        "Great question! You can find detailed information at https://support.apple.com. "
        "Let us know if you need anything else."
    ),
    "other": (
        "Thanks for contacting Apple Support. Please DM us with more details "
        "so we can assist you properly."
    ),
}


class SimpleBaseline:
    """
    Baseline 1 (Simple): Keyword/regex classifier.
    - Intent: highest-match-count keyword category wins; ties → 'other'
    - should_escalate: True if any escalation keyword found
    - Reply: template per intent
    """

    name = "simple_baseline"

    def predict(self, tweet_text: str) -> Dict:
        # Count keyword hits per intent
        scores = {}
        for intent, pattern in _INTENT_PATTERNS.items():
            matches = pattern.findall(tweet_text)
            scores[intent] = len(matches)

        best_intent = max(scores, key=lambda i: scores[i])
        if scores[best_intent] == 0:
            best_intent = "other"

        should_escalate = bool(_ESC_PATTERN.search(tweet_text))

        return {
            "intent": best_intent,
            "should_escalate": should_escalate,
            "reply": _REPLY_TEMPLATES[best_intent],
        }

    def predict_batch(self, tweets: List[Dict]) -> List[Dict]:
        results = []
        for t in tweets:
            pred = self.predict(t["tweet_text"])
            results.append({"id": t["id"], "tweet_text": t["tweet_text"], **pred})
        return results
