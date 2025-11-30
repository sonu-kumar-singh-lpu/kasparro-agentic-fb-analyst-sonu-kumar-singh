import pandas as pd
import numpy as np

def find_hypotheses(df, summaries):
    """
    Generates high-level hypotheses about ROAS drop, CTR issues,
    or creative fatigue using summary metrics and campaign-level patterns.
    """

    output = []

    avg_ctr = summaries["prompt_summary"]["avg_ctr"]
    avg_roas = summaries["prompt_summary"]["avg_roas"]

    # Campaign-level summary
    camp = df.groupby("campaign_name").agg(
        mean_ctr=("ctr", "mean"),
        mean_roas=("roas", "mean"),
        total_spend=("spend", "sum")
    ).reset_index()

    low_ctr = camp[camp["mean_ctr"] < avg_ctr]
    low_roas = camp[camp["mean_roas"] < avg_roas]

    # Hypothesis 1 — Creative Fatigue
    if len(low_ctr) > 0:
        output.append({
            "hypothesis": "Creative fatigue or weak messaging",
            "reason": f"{len(low_ctr)} campaigns show below-average CTR.",
            "affected_campaigns": low_ctr["campaign_name"].tolist(),
            "suggested_test": "Test new hooks, refresh dominant creatives, run A/B on primary text."
        })

    # Hypothesis 2 — Product Resonance but Weak Attention Hook
    medium_ctr = camp[(camp["mean_ctr"] < avg_ctr * 1.1)]
    if len(medium_ctr) > 2:
        output.append({
            "hypothesis": "Strong product resonance but weak attention-grabbing creatives",
            "reason": "High ROAS but CTR close to or just below average for multiple campaigns.",
            "affected_campaigns": medium_ctr["campaign_name"].tolist(),
            "suggested_test": "Try curiosity-based headlines, reduce text density, test contrast visuals."
        })

    # Hypothesis 3 — Overspending on Low-ROAS Segments
    if len(low_roas) > 0:
        output.append({
            "hypothesis": "Spend allocation inefficiency",
            "reason": f"{len(low_roas)} campaigns have lower-than-average ROAS with significant spend.",
            "affected_campaigns": low_roas["campaign_name"].tolist(),
            "suggested_test": "Shift budget to high-ROAS sets, check audience overlap or frequency."
        })

    # Default hypothesis if none found
    if len(output) == 0:
        output.append({
            "hypothesis": "Performance stable",
            "reason": "No major CTR/ROAS deviations detected.",
            "affected_campaigns": [],
            "suggested_test": "Continue monitoring; explore new creative angles proactively."
        })

    return output
