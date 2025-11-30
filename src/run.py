# src/run.py
import argparse
import json
import os
from datetime import datetime, timezone
import pandas as pd
import matplotlib.pyplot as plt

from src.agents.data_agent import prepare_data
from src.agents.planner import generate_plan
from src.agents.insight_agent import find_hypotheses
from src.agents.evaluator import score_hypotheses
from src.agents.creative_generator import (
    generate_variants_for_campaign,
    fallback_generate,
    normalize_campaign_name_for_generator,
)


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_charts(df, outdir):
    ensure_dir(outdir)

    # CTR by creative type
    fig, ax = plt.subplots(figsize=(8, 4))
    if "creative_type" in df.columns and "ctr" in df.columns:
        grp = df.groupby("creative_type")["ctr"].mean().reset_index()
        ax.bar(grp["creative_type"], grp["ctr"])
        plt.xticks(rotation=25)
        plt.title("CTR by Creative Type")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, "ctr_by_creative.png"))
        plt.close()
    else:
        # create an empty placeholder plot
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No creative_type / ctr data", ha="center", va="center")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, "ctr_by_creative.png"))
        plt.close()

    # Daily ROAS
    if "date" in df.columns and "roas" in df.columns:
        try:
            daily = df.groupby("date")["roas"].mean().reset_index()
            plt.figure(figsize=(8, 4))
            plt.plot(daily["date"], daily["roas"])
            plt.title("Daily ROAS")
            plt.tight_layout()
            plt.savefig(os.path.join(outdir, "daily_roas.png"))
            plt.close()
        except Exception:
            # fallback placeholder
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.text(0.5, 0.5, "Insufficient ROAS/time data", ha="center", va="center")
            plt.tight_layout()
            plt.savefig(os.path.join(outdir, "daily_roas.png"))
            plt.close()
    else:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No date/roas data", ha="center", va="center")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, "daily_roas.png"))
        plt.close()


def write_report(path, query, summaries, hypotheses, creatives):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# FB Ads Analysis Report\n\n")
        f.write(f"**Query:** {query}\n\n")
        f.write(f"**Generated at:** {datetime.now(timezone.utc).isoformat()} UTC\n\n")

        f.write("## Summary Metrics\n")
        if isinstance(summaries, dict) and "prompt_summary" in summaries:
            for k, v in summaries["prompt_summary"].items():
                f.write(f"- **{k}**: {v}\n")
        else:
            f.write("- No summary metrics available\n")
        f.write("\n")

        f.write("## Hypotheses\n")
        for h in hypotheses:
            if isinstance(h, dict):
                f.write(f"### {h.get('hypothesis','(no title)')}\n")
                f.write(f"- Reason: {h.get('reason','')}\n")
                if "confidence" in h:
                    f.write(f"- Confidence: {h['confidence']}\n")
                f.write("\n")
            else:
                f.write(f"- {str(h)}\n\n")

        f.write("## Creatives Generated\n")
        for camp, items in creatives.items():
            f.write(f"### {camp}\n")
            for it in items:
                # graceful for different structures
                headline = it.get("headline", it.get("message", "")).strip()
                body = it.get("body", "")
                cta = it.get("cta", "")
                f.write(f"- **{headline}** — {body} ({cta})\n")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="User query")
    parser.add_argument("--use-llm", action="store_true", help="Enable LLM creative generation")
    args = parser.parse_args()

    query = args.query
    USE_LLM = args.use_llm

    print("🔄 Running full agent pipeline...")

    print("📥 Loading data...")
    df, summaries = prepare_data()

    print("🧠 Generating plan...")
    plan = generate_plan(query)

    print("🔍 Generating hypotheses...")
    hypotheses = find_hypotheses(df, summaries)

    print("📊 Scoring hypotheses...")
    hypotheses = score_hypotheses(df, hypotheses)

    print("🎨 Generating creative suggestions...")
    creatives = {}
    # iterate original campaign names but store under normalized canonical keys
    if "campaign_name" in df.columns:
        for camp in df["campaign_name"].unique():
            canon = normalize_campaign_name_for_generator(camp)
            if USE_LLM:
                items = generate_variants_for_campaign(df, camp, n_variants=6)
            else:
                items = fallback_generate(df, camp, n_variants=6)

            # ensure we have a list
            if not isinstance(items, list):
                items = [items]

            creatives.setdefault(canon, []).extend(items)
    else:
        # fallback: single generic generation
        canon = "All Campaigns"
        if USE_LLM:
            creatives[canon] = generate_variants_for_campaign(df, "", n_variants=6)
        else:
            creatives[canon] = fallback_generate(df, "", n_variants=6)

    # dedupe variants inside each canonical campaign
    try:
        from src.agents.creative_generator import _dedupe_variants
        for k in list(creatives.keys()):
            creatives[k] = _dedupe_variants(creatives[k])
    except Exception:
        pass

    print("💾 Saving JSON outputs...")
    ensure_dir("reports")
    ensure_dir("reports/figures")

    save_json("reports/creatives.json", creatives)
    save_json("reports/insights.json", hypotheses)

    print("📈 Creating plots...")
    generate_charts(df, "reports/figures")

    print("📝 Writing report.md...")
    write_report("reports/report.md", query, summaries, hypotheses, creatives)

    print("🗂 Writing logs...")
    ensure_dir("logs")
    log_data = {
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_hypotheses": len(hypotheses) if isinstance(hypotheses, list) else 0,
        "num_campaign_keys": len(creatives)
    }
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    with open(f"logs/log_{timestamp_str}.json", "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print("✅ DONE — All outputs written successfully.")


if __name__ == "__main__":
    main()
