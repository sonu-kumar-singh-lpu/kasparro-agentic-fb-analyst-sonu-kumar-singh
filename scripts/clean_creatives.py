import json
import re
import difflib
from collections import defaultdict

# Aggressive threshold — merges heavy spelling variations
SIMILARITY_THRESHOLD = 0.65


def normalize_campaign_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name)

    s = name.lower()

    # Remove punctuation, digits, underscores
    s = re.sub(r"[^a-z\s]", " ", s)

    # Fix common OCR-like spelling variations for ComfortMax campaigns
    comfort_variants = [
        "omfortmax", "cofortmax", "comfotmax", "comformax", "comfortma",
        "comfortmaxx", "comfortnax", "comfortmzx", "confortmax",
        "cmfortmax", "comfor max"
    ]
    for v in comfort_variants:
        s = s.replace(v, "comfortmax")

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()

    # Remove noisy tokens
    remove_tokens = {
        "launch", "lunch", "offer", "promo", "spring", "summer", "drop",
        "v1", "v2", "v3", "v4", "test", "new", "copy", "set", "day",
        "name", "ver", "img", "creative"
    }
    s = " ".join([w for w in s.split() if w not in remove_tokens])

    # Reduce repeated characters
    s = re.sub(r"(.)\1+", r"\1", s)

    # Fix partial tokens ("mn", "en", "men", etc.)
    if s.startswith("mn "):
        s = "men " + s[3:]
    if s.startswith("en "):
        s = "men " + s[3:]

    # Title-case everything
    return " ".join(w.capitalize() for w in s.split())


def find_best_canonical(name, canon_map):
    """
    Choose the best canonical key using difflib sequence similarity.
    """
    best_match = None
    best_score = 0.0

    for canon in canon_map:
        score = difflib.SequenceMatcher(None, name, canon).ratio()
        if score > best_score:
            best_score = score
            best_match = canon

    if best_score >= SIMILARITY_THRESHOLD:
        return best_match
    return None


def clean_creatives():
    with open("reports/creatives.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    canonical_map = {}  # normalized → canonical key
    groups = defaultdict(list)

    print("\n🔍 Aggressive creative cleaning started...\n")

    for original_key, variants in data.items():

        normalized = normalize_campaign_name(original_key)

        # Try to find closest existing canonical
        existing = find_best_canonical(normalized, canonical_map)

        if existing:
            canonical = existing
        else:
            canonical = normalized
            canonical_map[normalized] = normalized

        # Add all variants under the canonical key
        groups[canonical].extend(variants)

    # Deduplicate variants inside each canonical group
    final_output = {}
    for key, items in groups.items():
        unique = []
        seen = set()

        for item in items:
            text = json.dumps(item, sort_keys=True)
            if text not in seen:
                seen.add(text)
                unique.append(item)

        final_output[key] = unique

    # Save cleaned file
    output_path = "reports/creatives_clean.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("✨ Cleaned creatives written to:", output_path)
    print("📊 Original keys:", len(data))
    print("📉 Canonical keys:", len(final_output))


if __name__ == "__main__":
    clean_creatives()
