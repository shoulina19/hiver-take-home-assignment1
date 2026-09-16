"""
generate_sample_data.py — Generates sample_data.csv and golden_200.json.
Run once before the main pipeline.
Usage: python generate_sample_data.py
"""
import csv
import json
import random
import os

random.seed(42)

# ─────────────────────────── Tweet Templates ─────────────────────────────────
TWEET_TEMPLATES = {
    "account_issue": [
        "@AppleSupport I can't log into my Apple ID! It says my account is locked. Please help!",
        "@AppleSupport My Apple ID password reset email never arrived. What should I do?",
        "@AppleSupport Two-factor authentication is not sending a code to my phone #{n}",
        "@AppleSupport I'm locked out of my account. I've tried everything and nothing works!",
        "@AppleSupport My account was disabled without warning. I never violated any terms! #{n}",
        "@AppleSupport Can't sign in on my new iPhone. Keep getting 'Apple ID verification failed' #{n}",
        "@AppleSupport I forgot my Apple ID email address and can't recover my account #{n}",
        "@AppleSupport Verification code not coming through even after 3 attempts #{n}",
        "@AppleSupport I changed my phone number and now can't receive 2FA codes #{n}",
        "@AppleSupport My account shows 'suspicious activity' but I haven't done anything #{n}",
        "@AppleSupport How do I merge two Apple ID accounts? I accidentally created two #{n}",
        "@AppleSupport My Apple ID is linked to an old email I no longer have access to #{n}",
        "@AppleSupport Password keeps getting rejected even though I know it's correct #{n}",
        "@AppleSupport Sign-in loop: enters password, goes back to login screen #{n}",
        "@AppleSupport How long does an account recovery request take? Been 3 days #{n}",
    ],
    "technical_support": [
        "@AppleSupport My iPhone {n} keeps crashing every time I open the camera!",
        "@AppleSupport iOS {n} update broke my WiFi. I can't connect to any network now.",
        "@AppleSupport My MacBook Pro won't start after the latest macOS update #{n}",
        "@AppleSupport Bluetooth keeps disconnecting on my AirPods Pro every 5 minutes #{n}",
        "@AppleSupport My iPhone battery drains from 100% to 0% in 3 hours since iOS update #{n}",
        "@AppleSupport Siri stopped working after I updated to the latest iOS. Doesn't respond #{n}",
        "@AppleSupport App Store shows error 'Cannot connect to App Store' on my iPad #{n}",
        "@AppleSupport Touch ID stopped recognizing my fingerprint out of nowhere #{n}",
        "@AppleSupport My screen is unresponsive after the recent update. Had to hard reset #{n}",
        "@AppleSupport iCloud sync stopped working — my photos aren't backing up #{n}",
        "@AppleSupport Messages not delivering on my iPhone. Shows sent but never received #{n}",
        "@AppleSupport My Apple Watch won't pair with my new iPhone {n}",
        "@AppleSupport Face ID not working in cold weather. Is this a known bug? #{n}",
        "@AppleSupport Home button feels sticky and sometimes doesn't respond #{n}",
        "@AppleSupport My AirTag shows 'Not Reachable' even though it's right next to me #{n}",
        "@AppleSupport Podcasts app keeps crashing mid-episode. Tried reinstalling #{n}",
        "@AppleSupport My iPhone speaker has distortion at high volumes after iOS update #{n}",
        "@AppleSupport Safari crashes immediately on my Mac when visiting most websites #{n}",
        "@AppleSupport Find My network shows my Mac as offline even though it's on #{n}",
        "@AppleSupport My iPhone overheats significantly when charging and using Maps #{n}",
    ],
    "billing_refund": [
        "@AppleSupport I was charged twice for the same app purchase! Need a refund #{n}",
        "@AppleSupport My subscription was renewed even after I cancelled it last month #{n}",
        "@AppleSupport I see an Apple charge on my credit card that I don't recognize #{n}",
        "@AppleSupport Bought an app that doesn't work as described. How do I get a refund? #{n}",
        "@AppleSupport Apple One subscription charged me but I can't access Apple TV+ #{n}",
        "@AppleSupport I was double-billed for iCloud+ storage this month #{n}",
        "@AppleSupport Accidental in-app purchase made by my kid. Can you help with a refund? #{n}",
        "@AppleSupport My Apple Pay transaction failed but money left my account #{n}",
        "@AppleSupport I cancelled Apple Music 2 weeks ago but still getting charged #{n}",
        "@AppleSupport iTunes gift card balance disappeared from my account #{n}",
        "@AppleSupport iCloud storage downgraded automatically but still charged full price #{n}",
        "@AppleSupport I received a refund email but it hasn't appeared in my bank account #{n}",
        "@AppleSupport Purchased wrong app — can I get a refund within 24 hours? #{n}",
        "@AppleSupport Family sharing isn't working but each member is being charged separately #{n}",
        "@AppleSupport App purchase failed but my card was charged. No receipt received #{n}",
    ],
    "product_feedback": [
        "@AppleSupport I wish the iPhone had a USB-C port. Why stick with Lightning? #{n}",
        "@AppleSupport Love the new iOS update! Dark mode looks incredible 🖤 #{n}",
        "@AppleSupport The new Dynamic Island is so cool! Great design choice #{n}",
        "@AppleSupport Stage Manager on iPad is confusing. Really needs a tutorial #{n}",
        "@AppleSupport Please bring back the headphone jack! Missing it so much #{n}",
        "@AppleSupport The Control Centre needs a major redesign. Too cluttered #{n}",
        "@AppleSupport Absolutely love how fast Face ID is on iPhone {n} 🔥 #{n}",
        "@AppleSupport Would love multi-window support on iPhone like iPad has #{n}",
        "@AppleSupport Night Mode camera is absolutely stunning. Best phone camera ever #{n}",
        "@AppleSupport AirDrop speed is incredible. Transferred 4GB in seconds #{n}",
        "@AppleSupport Notification grouping is still messy. Needs work Apple #{n}",
        "@AppleSupport Apple Pencil latency is imperceptible now. Artists will love this #{n}",
        "@AppleSupport Please add calculator to iPad. Can't believe it's still missing #{n}",
        "@AppleSupport Battery life on M2 MacBook Air is unreal. Full day easily #{n}",
        "@AppleSupport Wish Siri was smarter at context. Loses track after 2 questions #{n}",
    ],
    "general_inquiry": [
        "@AppleSupport Is the iPhone {n} compatible with iOS {n}?",
        "@AppleSupport Does Apple Watch Series 8 work without an iPhone nearby? #{n}",
        "@AppleSupport How do I transfer data from my Android to my new iPhone {n}?",
        "@AppleSupport When will the next macOS update be released? #{n}",
        "@AppleSupport Is Apple Care+ worth it for iPhone {n}? #{n}",
        "@AppleSupport Can I use my AirPods with a non-Apple device? #{n}",
        "@AppleSupport What's the maximum iCloud storage plan available? #{n}",
        "@AppleSupport Does the new iPad Pro support the Apple Pencil 2nd gen? #{n}",
        "@AppleSupport How many devices can share one Apple Music family plan? #{n}",
        "@AppleSupport Is the M2 chip compatible with Rosetta 2 apps? #{n}",
        "@AppleSupport Can I use Apple Pay in stores internationally? #{n}",
        "@AppleSupport What countries support eSIM for iPhone {n}?",
        "@AppleSupport How do I enable Screen Time for my child's device? #{n}",
        "@AppleSupport Is the iPhone {n} waterproof? What rating?",
        "@AppleSupport Does Apple offer student discounts on MacBooks? #{n}",
    ],
    "other": [
        "@AppleSupport You guys are amazing! Best tech support in the industry! #{n}",
        "@AppleSupport Just wanted to say thank you for the quick help yesterday! #{n}",
        "@AppleSupport Hi Apple! Can you sponsor my YouTube channel? #{n}",
        "@AppleSupport Your hold music is actually pretty good lol #{n}",
        "@AppleSupport Shoutout to the genius bar staff at NYC 5th Ave #{n}",
        "@AppleSupport Does Tim Cook read these tweets? #{n}",
        "@AppleSupport Can I get a job at Apple? #{n}",
        "@AppleSupport How do I apply to be an Apple beta tester? #{n}",
        "@AppleSupport What charities does Apple support? #{n}",
        "@AppleSupport Is the Apple Store on 5th Ave open on Christmas? #{n}",
    ],
}

# Escalation-worthy tweet templates
ESCALATION_TEMPLATES = [
    "@AppleSupport FRAUD! Someone made unauthorized purchases on my account! This is identity theft!",
    "@AppleSupport My Apple ID was hacked and I cannot regain access. I'm reporting this to the police #{n}",
    "@AppleSupport URGENT: Someone has full access to my email and Apple account. Emergency! #{n}",
    "@AppleSupport I'm considering legal action against Apple for this unauthorized charge of $500 #{n}",
    "@AppleSupport Data breach! My personal photos are being shared without my consent! #{n}",
    "@AppleSupport Identity theft via Apple ID. Someone opened credit cards in my name #{n}",
    "@AppleSupport I cannot access my account and my medical emergency contacts are all stored there! #{n}",
    "@AppleSupport Fraudulent charges of $800 on my Apple account. Will dispute with my bank and attorney #{n}",
    "@AppleSupport My account was permanently locked and I'm locked out of my business data. CRITICAL #{n}",
    "@AppleSupport I've been locked out for 30 days, I'm losing my small business over this #{n}",
]

def generate_tweets(n_total=700, random_seed=42):
    random.seed(random_seed)
    tweets = []
    tweet_id = 1001

    # Intent distribution (roughly realistic for AppleSupport):
    # technical_support ~35%, account_issue ~25%, billing_refund ~15%,
    # general_inquiry ~10%, product_feedback ~8%, other ~5%, escalation ~2%
    distribution = {
        "technical_support": 0.33,
        "account_issue":     0.25,
        "billing_refund":    0.15,
        "general_inquiry":   0.10,
        "product_feedback":  0.10,
        "other":             0.05,
    }
    n_escalation = max(10, int(n_total * 0.02))
    n_normal = n_total - n_escalation

    # Generate normal tweets
    for intent, frac in distribution.items():
        count = int(n_normal * frac)
        templates = TWEET_TEMPLATES[intent]
        for i in range(count):
            tmpl = templates[i % len(templates)]
            text = tmpl.replace("{n}", str(random.choice([14, 15, 16, 17]))).replace("#{n}", "")
            text = text.strip()
            tweets.append({"id": str(tweet_id), "tweet_text": text, "_intent": intent, "_escalate": False})
            tweet_id += 1

    # Generate escalation tweets (intent = account_issue or billing_refund)
    for i in range(n_escalation):
        tmpl = ESCALATION_TEMPLATES[i % len(ESCALATION_TEMPLATES)]
        text = tmpl.replace("#{n}", "").strip()
        intent = random.choice(["account_issue", "billing_refund", "technical_support"])
        tweets.append({"id": str(tweet_id), "tweet_text": text, "_intent": intent, "_escalate": True})
        tweet_id += 1

    random.shuffle(tweets)
    # Re-number after shuffle
    for i, t in enumerate(tweets):
        t["id"] = str(1001 + i)

    return tweets


def save_sample_csv(tweets, path="data/sample_data.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "tweet_text"])
        writer.writeheader()
        for t in tweets:
            writer.writerow({"id": t["id"], "tweet_text": t["tweet_text"]})
    print(f"✓ Saved {len(tweets)} tweets → {path}")


def save_golden_json(tweets, path="data/golden_200.json", n=200, random_seed=42):
    """
    Sample 200 tweets stratified by intent for the golden set.
    Sampling notes:
    - Time range: Simulated Q3 2024 AppleSupport tweet stream
    - Stratification: Proportional to intent distribution, minimum 15 per intent
    - Random seed: 42
    - Inter-annotator agreement: Simulated κ = 0.81 on 50 double-labelled examples
    """
    random.seed(random_seed)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Group by intent
    by_intent = {}
    for t in tweets:
        intent = t["_intent"]
        by_intent.setdefault(intent, []).append(t)

    # Minimum 15 per intent, then fill proportionally
    intents = list(by_intent.keys())
    per_intent_min = 15
    reserved = {i: per_intent_min for i in intents}
    remaining = n - sum(reserved.values())
    # Add remaining proportionally
    total = sum(len(v) for v in by_intent.values())
    for intent in intents:
        extra = int(remaining * len(by_intent[intent]) / total)
        reserved[intent] += extra
    # Ensure total = 200
    diff = n - sum(reserved.values())
    reserved[intents[0]] += diff

    golden = []
    for intent, count in reserved.items():
        pool = by_intent.get(intent, [])
        random.shuffle(pool)
        for t in pool[:count]:
            golden.append({
                "id": t["id"],   # same ID as in sample_data.csv
                "tweet_text": t["tweet_text"],
                "intent": intent,
                "should_escalate": t["_escalate"],
                "annotator": "annotator_1",
                "confidence": random.choice(["high", "high", "high", "medium"]),
            })

    random.shuffle(golden)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(golden, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(golden)} golden examples → {path}")
    # Print distribution
    from collections import Counter
    counts = Counter(g["intent"] for g in golden)
    esc_count = sum(1 for g in golden if g["should_escalate"])
    print(f"\nGolden set distribution:")
    for intent, cnt in sorted(counts.items()):
        print(f"  {intent:<22} {cnt:>3} examples")
    print(f"  {'should_escalate=True':<22} {esc_count:>3} examples")
    print()
    return golden


if __name__ == "__main__":
    print("Generating sample data and golden set...\n")
    tweets = generate_tweets(n_total=700, random_seed=42)
    save_sample_csv(tweets, "data/sample_data.csv")
    save_golden_json(tweets, "data/golden_200.json", n=200, random_seed=42)
    print("Done! Ready to run: python run_pipeline.py --brand AppleSupport --sample")
