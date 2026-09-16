"""
primary_agent.py — LLM-powered intent classifier and reply generator.
Uses OpenAI-compatible API (set OPENAI_API_KEY in environment).
Falls back gracefully to simple_baseline if API is unavailable.
"""
import os
import json
import re
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

from src.taxonomy import INTENTS, ESCALATION_KEYWORDS
from src.simple_baseline import SimpleBaseline

_FALLBACK = SimpleBaseline()

SYSTEM_PROMPT = """You are an expert Apple Support social media agent.
Your job is to classify a customer tweet and draft a helpful, empathetic reply.

You MUST respond with ONLY valid JSON matching this schema (no markdown, no explanation):
{
  "intent": "<one of: account_issue | technical_support | billing_refund | product_feedback | general_inquiry | other>",
  "should_escalate": <true | false>,
  "reply": "<your reply tweet, max 280 chars>"
}

Intent definitions:
- account_issue: Apple ID, password, login, 2FA, locked account
- technical_support: device crash, bug, iOS/macOS problem, hardware, Siri, battery
- billing_refund: charges, refunds, subscriptions, Apple Pay, App Store purchases
- product_feedback: feature requests, praise, complaints about design/UX
- general_inquiry: factual questions about products, compatibility, availability
- other: anything that doesn't fit the above

Escalate (should_escalate=true) when ANY of the following apply:
- Fraud, unauthorized charges, or suspected account hack
- User reports data breach or identity theft
- Legal threats or mention of law enforcement
- User is in urgent/emergency distress
- Abusive situation or discrimination claim
- Issue is permanently unresolvable via standard channels

Rules:
- Be concise, warm, and professional
- Never share personal data
- Keep reply under 280 characters
"""

_OUTPUT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _call_llm(tweet_text: str, model: str, client) -> Optional[Dict]:
    """Call LLM and parse JSON response. Returns None on failure."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Tweet: {tweet_text}"},
            ],
            temperature=0.2,
            max_tokens=300,
            timeout=30,
        )
        raw = response.choices[0].message.content.strip()
        # Extract JSON if wrapped in markdown
        m = _OUTPUT_PATTERN.search(raw)
        if m:
            data = json.loads(m.group())
            # Validate
            if data.get("intent") not in INTENTS:
                data["intent"] = "other"
            data["should_escalate"] = bool(data.get("should_escalate", False))
            data["reply"] = str(data.get("reply", ""))[:280]
            return data
    except Exception as e:
        print(f"  [primary_agent] LLM call failed: {e}")
    return None


class PrimaryAgent:
    """
    LLM-powered support agent.
    Requires OPENAI_API_KEY env var (or OPENAI_BASE_URL for custom endpoints).
    Falls back to simple_baseline if API unavailable.
    """

    name = "primary_agent"

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None

        if api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                self.client = OpenAI(**kwargs)
                print(f"[primary_agent] Using LLM: {self.model}")
            except Exception as e:
                print(f"[primary_agent] OpenAI init failed: {e}. Using fallback.")
        else:
            print("[primary_agent] No OPENAI_API_KEY found. Using simple_baseline as fallback.")

    def predict(self, tweet_text: str) -> Dict:
        if self.client:
            result = _call_llm(tweet_text, self.model, self.client)
            if result:
                return result
            # Retry once
            time.sleep(1)
            result = _call_llm(tweet_text, self.model, self.client)
            if result:
                return result
        # Fallback
        return _FALLBACK.predict(tweet_text)

    def predict_batch(self, tweets: List[Dict], delay: float = 0.1) -> List[Dict]:
        results = []
        for i, t in enumerate(tweets):
            if i % 50 == 0:
                print(f"  [primary_agent] Processing {i}/{len(tweets)}...")
            pred = self.predict(t["tweet_text"])
            results.append({"id": t["id"], "tweet_text": t["tweet_text"], **pred})
            time.sleep(delay)
        return results
