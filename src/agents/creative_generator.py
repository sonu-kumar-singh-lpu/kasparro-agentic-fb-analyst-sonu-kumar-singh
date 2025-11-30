import os
import json
import random
import re
import traceback

# =====================================================================
# 1. NORMALIZE CAMPAIGN NAMES (for clean keys in creatives.json)
# =====================================================================

def normalize_campaign_name_for_generator(name: str) -> str:
    """
    Cleans and normalizes campaign names so that creatives.json doesn't get messy.
    Fixes punctuation, double spaces, case, accidental typos, etc.
    """
    if not isinstance(name, str):
        return str(name)

    s = name.strip()

    # Remove punctuation except letters/numbers/spaces
    s = re.sub(r"[^\w\s]", " ", s)

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()

    s = s.lower()

    # Remove common noise tokens
    s = re.sub(r"\b(name|#name|offer|launch|lunch|v1|v2|test)\b", "", s)

    s = re.sub(r"\s+", " ", s).strip()

    # Title-case for readability
    return " ".join(w.capitalize() for w in s.split())


# =====================================================================
# 2. TEXT CLEANER (remove weird unicode, cleanup)
# =====================================================================

def _clean_text(s):
    if s is None:
        return ""
    s = s.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", " - ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.strip(" .,-;:\n\t")
    return s


def _dedupe_variants(variants):
    seen = set()
    out = []
    for v in variants:
        h = _clean_text(v.get("headline", "")).lower()
        b = _clean_text(v.get("body", "")).lower()
        key = (h, b)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


# =====================================================================
# 3. FALLBACK GENERATOR (if LLM unavailable)
# =====================================================================

def fallback_generate(df, campaign_name, n_variants=5):
    try:
        sample = df[df["campaign_name"] == campaign_name]["creative_message"].dropna().astype(str).tolist()[:10]
    except:
        sample = []

    variants = []
    for i in range(n_variants):
        headline = f"{campaign_name} Offer"
        body = "Premium comfort and breathable design for everyday wear."
        cta = random.choice(["Shop now", "Buy now", "Learn more", "Grab now", "Limited stock"])
        message = f"{headline} — {body} {cta}"
        variants.append({
            "variant_id": f"{campaign_name}_v{i+1}",
            "headline": headline,
            "body": body,
            "cta": cta,
            "message": message
        })
    return variants


# =====================================================================
# 4. LLM-BASED GENERATOR
# =====================================================================

def llm_generate(df, campaign_name, n_variants=5, model="gpt-4o-mini"):
    """
    Uses OpenAI to generate high-quality ad creatives.
    Attempts to recover from malformed JSON gracefully.
    """
    try:
        import openai
    except:
        return fallback_generate(df, campaign_name, n_variants)

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return fallback_generate(df, campaign_name, n_variants)

    openai.api_key = key

    try:
        prev_msgs = df[df["campaign_name"] == campaign_name]["creative_message"].dropna().astype(str).tolist()[:8]
    except:
        prev_msgs = []

    existing = "\n".join(prev_msgs) if prev_msgs else "No existing creatives found."

    # Load prompt template
    try:
        prompt_template = open("prompts/creative.md", "r", encoding="utf-8").read()
    except:
        prompt_template = "SYSTEM: return JSON only.\n"

    prompt = (
        prompt_template
        .replace("{{campaign_name}}", campaign_name)
        .replace("{{existing_creatives}}", existing)
        + f"\nGenerate {n_variants} new variants."
    )

    # Provide few-shot examples for consistency
    examples = [
        {
            "variant_id": "ex1",
            "headline": "Bold colors, unmatched comfort",
            "body": "Premium modal fabric with all day breathability.",
            "cta": "Shop now"
        },
        {
            "variant_id": "ex2",
            "headline": "Invisible under tees",
            "body": "Seamless design for everyday wear — no lines, perfect fit.",
            "cta": "Buy now"
        }
    ]

    messages = [
        {"role": "system", "content": "Return valid JSON only. You are a senior ad copywriter."},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": json.dumps([examples[0]])},
        {"role": "assistant", "content": json.dumps([examples[1]])}
    ]

    # Call LLM
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
            top_p=0.95
        )
        raw = resp["choices"][0]["message"]["content"].strip()
    except:
        return fallback_generate(df, campaign_name, n_variants)

    # Extract JSON safely
    json_text = None
    if raw.startswith("["):
        json_text = raw
    else:
        first = raw.find("[")
        last = raw.rfind("]")
        if first != -1 and last != -1:
            json_text = raw[first:last+1]

    parsed = None
    if json_text:
        try:
            parsed = json.loads(json_text)
        except:
            cleaned = re.sub(r",\s*]", "]", json_text)
            cleaned = re.sub(r",\s*}", "}", cleaned)
            try:
                parsed = json.loads(cleaned)
            except:
                parsed = None

    if not isinstance(parsed, list):
        return fallback_generate(df, campaign_name, n_variants)

    # Clean output
    variants = []
    for i, item in enumerate(parsed):
        h = _clean_text(item.get("headline", ""))
        b = _clean_text(item.get("body", ""))
        cta = item.get("cta", "Shop now")

        if cta not in ["Shop now", "Buy now", "Learn more", "Grab now", "Limited stock"]:
            cta = "Shop now"

        variants.append({
            "variant_id": f"{campaign_name}_v{i+1}",
            "headline": h,
            "body": b,
            "cta": cta,
            "message": f"{h} — {b} {cta}"
        })

    variants = _dedupe_variants(variants)
    return variants[:n_variants]


# =====================================================================
# 5. MAIN EXPORTED FUNCTION — USED BY run.py
# =====================================================================

def generate_variants_for_campaign(df, campaign_name, n_variants=5):
    """
    Wrapper that:
    1. normalizes campaign_name for JSON keys
    2. generates high-quality variants via LLM or fallback
    """
    try:
        variants = llm_generate(df, campaign_name, n_variants=n_variants)
    except:
        variants = fallback_generate(df, campaign_name, n_variants)

    # Always dedupe to protect JSON quality
    variants = _dedupe_variants(variants)

    return variants
