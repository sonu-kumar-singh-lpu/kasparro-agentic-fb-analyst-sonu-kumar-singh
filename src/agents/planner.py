import json

def generate_plan(query):
    """
    Returns a fixed structured plan for the agent pipeline.
    """
    plan = {
        "query": query,
        "tasks": [
            {
                "task_id": "load_data",
                "description": "Load and clean dataset using DataAgent",
                "agent": "DataAgent"
            },
            {
                "task_id": "summarize_data",
                "description": "Generate summary metrics for prompts and analysis",
                "agent": "DataAgent"
            },
            {
                "task_id": "generate_hypotheses",
                "description": "Identify potential reasons for ROAS or CTR issues",
                "agent": "InsightAgent"
            },
            {
                "task_id": "evaluate_hypotheses",
                "description": "Perform quantitative validation of each hypothesis",
                "agent": "EvaluatorAgent"
            },
            {
                "task_id": "generate_creatives",
                "description": "Generate new messaging ideas for low-performance campaigns",
                "agent": "CreativeAgent"
            },
            {
                "task_id": "compile_report",
                "description": "Aggregate insights, evidence, and creatives into a final report",
                "agent": "ReportGenerator"
            }
        ],
        "total_tasks": 6
    }
    return plan
