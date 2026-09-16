"""
data_loader.py — Loads sample_data.csv and golden_200.json.
"""
import csv
import json
import os
from typing import List, Dict


def load_sample_data(path: str = "data/sample_data.csv") -> List[Dict]:
    """Return list of dicts with keys: id, tweet_text."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({"id": row["id"], "tweet_text": row["tweet_text"]})
    return rows


def load_golden_set(path: str = "data/golden_200.json") -> List[Dict]:
    """
    Return list of dicts with keys:
        id, tweet_text, intent, should_escalate
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_predictions(predictions: List[Dict], path: str) -> None:
    """Save list of prediction dicts to JSON."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)
    print(f"[data_loader] Saved {len(predictions)} predictions → {path}")
