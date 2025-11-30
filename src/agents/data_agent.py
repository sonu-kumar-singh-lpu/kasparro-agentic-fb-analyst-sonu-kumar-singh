import pandas as pd
import yaml
from pathlib import Path

def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_data(config):
    path = Path(config["data_csv"])
    df = pd.read_csv(path, parse_dates=["date"], low_memory=False)
    return df

def clean_data(df):
    df = df.copy()
    numeric_cols = ["spend", "impressions", "clicks", "ctr", "purchases", "revenue", "roas"]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "ctr" in df.columns:
        df["ctr"] = df["ctr"].fillna(
            (df["clicks"] / df["impressions"]).replace([float("inf"), float("nan")], 0)
        )

    df = df.fillna({"campaign_name": "unknown", "creative_message": ""})
    return df

def campaign_summary(df):
    return df.groupby("campaign_name").agg(
        total_spend=("spend", "sum"),
        mean_roas=("roas", "mean"),
        mean_ctr=("ctr", "mean"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        purchases=("purchases", "sum")
    ).reset_index()

def daily_summary(df):
    return df.groupby("date").agg(
        daily_spend=("spend", "sum"),
        daily_revenue=("revenue", "sum"),
        daily_roas=("roas", "mean"),
        daily_impressions=("impressions", "sum"),
        daily_clicks=("clicks", "sum")
    ).reset_index().sort_values("date")

def prompt_summary(df, top_k=5):
    camp = campaign_summary(df).sort_values("total_spend", ascending=False).head(top_k)

    summary = {
        "num_rows": int(len(df)),
        "total_spend": float(df["spend"].sum()),
        "avg_roas": float(df["roas"].mean()),
        "avg_ctr": float(df["ctr"].mean()),
        "top_campaigns": camp[["campaign_name", "total_spend", "mean_roas", "mean_ctr"]].to_dict(orient="records")
    }
    return summary

def prepare_data(config_path="config/config.yaml"):
    cfg = load_config(config_path)
    df = load_data(cfg)
    df = clean_data(df)

    summaries = {
        "campaign_summary": campaign_summary(df),
        "daily_summary": daily_summary(df),
        "prompt_summary": prompt_summary(df)
    }

    return df, summaries

if __name__ == "__main__":
    df, summaries = prepare_data()
    print("Rows:", len(df))
    print("Prompt Summary:", summaries["prompt_summary"])
