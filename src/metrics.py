"""
metrics.py — Evaluation metrics: accuracy, macro F1, escalation precision/recall, Cohen's κ.
"""
import json
from typing import List, Dict, Tuple
from collections import defaultdict
import math


def _confusion(y_true: List, y_pred: List, labels: List) -> Dict:
    """Return per-class TP, FP, FN counts."""
    label_set = labels
    counts = {l: {"tp": 0, "fp": 0, "fn": 0} for l in label_set}
    for t, p in zip(y_true, y_pred):
        if t == p:
            if t in counts:
                counts[t]["tp"] += 1
        else:
            if p in counts:
                counts[p]["fp"] += 1
            if t in counts:
                counts[t]["fn"] += 1
    return counts


def intent_accuracy(y_true: List[str], y_pred: List[str]) -> float:
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true) if y_true else 0.0


def macro_f1(y_true: List[str], y_pred: List[str], labels: List[str]) -> Tuple[float, Dict]:
    counts = _confusion(y_true, y_pred, labels)
    f1s = {}
    for l in labels:
        tp = counts[l]["tp"]
        fp = counts[l]["fp"]
        fn = counts[l]["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1s[l] = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    macro = sum(f1s.values()) / len(labels)
    return macro, f1s


def escalation_metrics(y_true: List[bool], y_pred: List[bool]) -> Dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def cohen_kappa(rater1: List, rater2: List, labels: List = None) -> float:
    """
    Compute Cohen's κ for two raters on the same items.
    Works for both categorical and binary ratings.
    """
    if labels is None:
        labels = list(set(rater1) | set(rater2))
    n = len(rater1)
    if n == 0:
        return 0.0

    # Observed agreement
    p_o = sum(1 for a, b in zip(rater1, rater2) if a == b) / n

    # Expected agreement
    p_e = 0.0
    for label in labels:
        freq1 = rater1.count(label) / n
        freq2 = rater2.count(label) / n
        p_e += freq1 * freq2

    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def bootstrap_ci(values: List[float], n_boot: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """Return (lower, upper) 95% bootstrap confidence interval."""
    import random
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    boot_means = []
    for _i in range(n_boot):
        sample = [values[random.randint(0, n - 1)] for _j in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo = boot_means[int(alpha / 2 * n_boot)]
    hi = boot_means[int((1 - alpha / 2) * n_boot)]
    return lo, hi


def compute_all_metrics(
    golden: List[Dict],
    predictions: List[Dict],
    labels: List[str],
    system_name: str = "system",
) -> Dict:
    """
    Compare predictions against the golden set.
    Both lists must align on 'id'.
    """
    gold_map = {g["id"]: g for g in golden}
    y_true_intent, y_pred_intent = [], []
    y_true_esc, y_pred_esc = [], []

    for pred in predictions:
        gid = pred["id"]
        if gid not in gold_map:
            continue
        gold = gold_map[gid]
        y_true_intent.append(gold["intent"])
        y_pred_intent.append(pred["intent"])
        y_true_esc.append(bool(gold["should_escalate"]))
        y_pred_esc.append(bool(pred["should_escalate"]))

    acc = intent_accuracy(y_true_intent, y_pred_intent)
    mf1, per_class_f1 = macro_f1(y_true_intent, y_pred_intent, labels)
    esc = escalation_metrics(y_true_esc, y_pred_esc)
    kappa = cohen_kappa(y_true_intent, y_pred_intent, labels)

    # Bootstrap CI on accuracy
    correct_flags = [1.0 if t == p else 0.0 for t, p in zip(y_true_intent, y_pred_intent)]
    ci_lo, ci_hi = bootstrap_ci(correct_flags)

    return {
        "system": system_name,
        "n_evaluated": len(y_true_intent),
        "intent_accuracy": round(acc, 4),
        "intent_accuracy_95ci": [round(ci_lo, 4), round(ci_hi, 4)],
        "macro_f1": round(mf1, 4),
        "per_class_f1": {k: round(v, 4) for k, v in per_class_f1.items()},
        "escalation": {k: round(v, 4) if isinstance(v, float) else v for k, v in esc.items()},
        "cohen_kappa_intent": round(kappa, 4),
    }
