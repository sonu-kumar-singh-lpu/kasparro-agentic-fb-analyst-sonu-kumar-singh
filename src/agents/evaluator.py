import numpy as np
import pandas as pd
from scipy.stats import kruskal

def score_hypotheses(df, hypotheses):
    """
    Adds confidence scores and evidence to hypotheses.
    Ensures hypotheses list contains valid dictionaries.
    """

    output = []

    for h in hypotheses:
        # Safety: convert string → dictionary if needed
        if isinstance(h, str):
            h = {"hypothesis": h, "reason": "", "affected_campaigns": []}

        hyp_text = h.get("hypothesis", "").lower()

        evidence = []

        # ------------------------------------------
        # Evidence block 1: CTR differences by creative_type
        # ------------------------------------------
        try:
            grp = df.groupby("creative_type")["ctr"].agg(["mean", "std", "count"]).reset_index()
            evidence.append({
                "creative_ctr_summary": grp.to_dict(orient="records")
            })

            # Statistical test: difference across creative types
            arrays = []
            for t in df["creative_type"].unique():
                arrays.append(df[df["creative_type"] == t]["ctr"])
            stat, p = kruskal(*arrays)
            evidence.append({
                "kruskal_statistic": float(stat),
                "pvalue": float(p)
            })
        except Exception as e:
            evidence.append({"ctr_test_error": str(e)})

        # ------------------------------------------
        # Evidence block 2: Recent vs previous ROAS
        # ------------------------------------------
        try:
            df_sorted = df.sort_values("date")
            midpoint = int(len(df_sorted) * 0.5)

            prev = df_sorted.iloc[:midpoint]["roas"]
            recent = df_sorted.iloc[midpoint:]["roas"]

            prev_mean = prev.mean()
            recent_mean = recent.mean()

            drop_pct = (prev_mean - recent_mean) / prev_mean if prev_mean > 0 else 0

            evidence.append({
                "prev_mean_roas": float(prev_mean),
                "recent_mean_roas": float(recent_mean),
                "drop_pct": float(drop_pct)
            })
        except Exception as e:
            evidence.append({"roas_split_error": str(e)})

        # ------------------------------------------
        # Confidence scoring (simple heuristic)
        # ------------------------------------------
        confidence = 0.5  # default

        if "ctr" in hyp_text or "creative" in hyp_text:
            confidence = 0.8
        if "roas" in hyp_text or "drop" in hyp_text:
            confidence = max(confidence, 0.7)
        if "spend" in hyp_text or "overspending" in hyp_text:
            confidence = max(confidence, 0.6)

        h["confidence"] = round(confidence, 2)
        h["evidence"] = evidence

        output.append(h)

    return output
