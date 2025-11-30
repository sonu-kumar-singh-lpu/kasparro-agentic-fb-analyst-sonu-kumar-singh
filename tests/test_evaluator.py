import pandas as pd
from src.agents.evaluator import evaluate_creative_hypothesis

def test_evaluator_runs():
    df = pd.DataFrame({
        "creative_type": ["A","A","B","B"],
        "ctr": [0.01,0.02,0.03,0.04]
    })

    result = evaluate_creative_hypothesis(df)
    assert "evidence" in result
    assert "confidence" in result
