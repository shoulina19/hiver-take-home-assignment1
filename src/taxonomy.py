"""
Intent taxonomy for AppleSupport tweet classification.
"""

# Ordered list of valid intents
INTENTS = [
    "account_issue",
    "technical_support",
    "billing_refund",
    "product_feedback",
    "general_inquiry",
    "other",
]

# Human-readable labels
INTENT_LABELS = {
    "account_issue":     "Account Issue",
    "technical_support": "Technical Support",
    "billing_refund":    "Billing / Refund",
    "product_feedback":  "Product Feedback",
    "general_inquiry":   "General Inquiry",
    "other":             "Other",
}

# Keyword sets used by the simple baseline
INTENT_KEYWORDS = {
    "account_issue": [
        "account", "login", "sign in", "signin", "password", "locked",
        "apple id", "appleid", "two-factor", "2fa", "verification",
        "authentication", "reset", "username", "disabled account",
    ],
    "technical_support": [
        "crash", "frozen", "not working", "bug", "error", "glitch",
        "update", "ios", "macos", "iphone", "ipad", "mac", "watch",
        "battery", "wifi", "bluetooth", "sync", "restore", "backup",
        "itunes", "app", "install", "uninstall", "screen", "touch",
        "face id", "touch id", "siri", "slow", "performance",
    ],
    "billing_refund": [
        "charge", "charged", "refund", "refunded", "payment", "invoice",
        "receipt", "subscription", "renew", "cancel", "apple pay",
        "applepay", "itunes store", "app store", "purchase", "billing",
        "credit card", "unauthorized", "debit",
    ],
    "product_feedback": [
        "love", "hate", "wish", "feature", "suggest", "suggestion",
        "please add", "would be nice", "feedback", "improve", "request",
        "should have", "missing feature",
    ],
    "general_inquiry": [
        "when", "how do i", "how to", "what is", "which", "can you",
        "does apple", "is there", "where", "available", "compatible",
        "support", "help me understand",
    ],
}

# Escalation triggers: conditions that make should_escalate = True
ESCALATION_KEYWORDS = [
    "fraud", "fraudulent", "scam", "hacked", "unauthorized",
    "data breach", "legal", "lawsuit", "police", "discrimination",
    "harassment", "threatening", "urgent", "emergency", "critical",
    "cannot access", "locked out permanently", "identity theft",
]

MAJORITY_CLASS = "technical_support"   # used by trivial baseline
