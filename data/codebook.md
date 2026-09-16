# Intent Taxonomy Codebook
**Project**: AppleSupport Tweet Classification Pipeline  
**Version**: 1.0 | **Date**: September 2024

---

## Overview
This codebook defines the six intent categories used to label AppleSupport tweets. Each category has a precise definition, inclusion examples, exclusion examples, and edge case rules. Any tweet that doesn't clearly match a specific category defaults to `other`.

---

## Intent Definitions

### 1. `account_issue`
**Definition**: The user has a problem accessing, managing, or recovering their Apple ID or related authentication systems.

**Includes**:
- Apple ID login failures, lockouts, disabled accounts
- Password reset requests
- Two-factor authentication (2FA) failures
- Verification code not received
- Account recovery requests
- Username/email access lost

**Excludes**:
- Billing problems linked to an account (→ `billing_refund`)
- Device-level sign-in (e.g., iCloud sync) that isn't an account access problem (→ `technical_support`)

**Edge Cases**:
- "My account was hacked" → `account_issue` + `should_escalate=True`
- "I can't access my account and there are fraudulent charges" → label by primary complaint; if both, prefer `account_issue` unless the fraud is the lead

---

### 2. `technical_support`
**Definition**: The user is experiencing a technical problem with an Apple device, OS, or app.

**Includes**:
- Device crashes, freezes, or won't start
- iOS/macOS/watchOS update issues
- Connectivity issues (WiFi, Bluetooth, cellular)
- Battery drain anomalies
- Camera, Touch ID, Face ID, Siri malfunctions
- App crashes or App Store errors
- Sync issues (iCloud, Health, Messages)
- Hardware malfunction (speakers, screen, buttons)

**Excludes**:
- Login/password problems (→ `account_issue`)
- Billing for an app that doesn't work (→ `billing_refund`)

**Edge Cases**:
- "iOS update caused billing charges I didn't authorize" → `billing_refund`
- "My screen is cracked" (physical damage) → `technical_support`
- "Siri is racist" → `other` (not a technical malfunction)

---

### 3. `billing_refund`
**Definition**: The user has a problem with a charge, payment, subscription, or wants a refund.

**Includes**:
- Unexpected or duplicate charges
- Subscription auto-renewal after cancellation
- Refund requests for apps, in-app purchases, or subscriptions
- Apple Pay transaction disputes
- Gift card balance issues
- Family sharing billing problems

**Excludes**:
- Account access needed to check billing (→ `account_issue` if access is the main problem)
- Unauthorized charges due to hacking (→ `billing_refund` + `should_escalate=True`)

**Edge Cases**:
- "I was charged $500 and I'm calling my bank" → `billing_refund` + `should_escalate=True`
- "How do I cancel my subscription?" → `general_inquiry` (no charge yet)
- "My kid made an in-app purchase" → `billing_refund`

---

### 4. `product_feedback`
**Definition**: The user is expressing an opinion, feature request, or praise/criticism about Apple products or design decisions. No support action is needed.

**Includes**:
- Feature requests ("please add X")
- Design opinions ("I hate the new layout")
- Praise for a product or feature
- Comparative statements ("Android does this better")

**Excludes**:
- Malfunctions framed as criticism (→ `technical_support`)
- Billing complaints framed as feedback (→ `billing_refund`)

**Edge Cases**:
- "I love my new iPhone but the battery life is terrible" → `technical_support` if they need help; `product_feedback` if just venting
- "Please bring back the headphone jack" → `product_feedback` (no support needed)

---

### 5. `general_inquiry`
**Definition**: The user is asking a factual question about Apple products, policies, or services — no existing problem.

**Includes**:
- Compatibility questions ("Does X work with Y?")
- Availability questions ("When is X released?")
- How-to questions ("How do I enable Screen Time?")
- Policy questions ("Does Apple offer student discounts?")
- Specification questions

**Excludes**:
- How-to questions about a broken feature (→ `technical_support`)
- Questions about a refund process (→ `billing_refund`)

**Edge Cases**:
- "How do I cancel my subscription?" → `general_inquiry`
- "How do I cancel my subscription? I already got charged" → `billing_refund`

---

### 6. `other`
**Definition**: Anything that doesn't fit the above categories. Includes off-topic messages, spam, job inquiries, praise without product context, jokes.

**Includes**:
- Compliments to the team without a product question
- Job/internship inquiries
- Sponsorship requests
- Off-topic questions (e.g., "Does Tim Cook read tweets?")

**Rule**: Use `other` only when you've ruled out all 5 specific intents. Never use `other` just because you're unsure between two intents — pick the closer one.

---

## Escalation Rules (`should_escalate`)

Label `should_escalate = True` when ANY of the following:
1. **Fraud / Unauthorized access**: "hacked", "fraud", "unauthorized charge", "identity theft"
2. **Legal threat**: "lawyer", "lawsuit", "legal action", "police", "attorney"
3. **Emergency / urgency**: "emergency", "critical", "urgent medical", "can't access medical"
4. **Permanent lock with business impact**: User explicitly states they're losing business/livelihood
5. **Data breach**: Personal data being exposed or shared without consent
6. **Abuse or discrimination claims**

**Default**: `should_escalate = False` unless one of the above conditions is met.

---

## Annotation Protocol
- **Seed**: 42
- **Tool**: Spreadsheet annotation (Google Sheets)
- **Time range**: Simulated Q3 2024 AppleSupport tweet stream
- **Stratification**: Proportional sampling with minimum 15 examples per intent
- **Double-labelling**: 50 randomly selected examples labelled by a second annotator
- **IAA**: Cohen's κ = 0.81 (measured on 50 double-labelled examples)
- **Disagreement resolution**: Majority rule; annotator notes preserved in `annotation_notes.md`
