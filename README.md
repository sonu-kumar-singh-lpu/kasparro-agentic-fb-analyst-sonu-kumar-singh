# 📊 Kasparro — Agentic FB Ads Performance Analyst

**Applied AI Engineer Assignment — Sonu Kumar Singh**

This repository contains a fully functional agentic AI system designed to analyze Facebook Ads performance, generate insights, validate hypotheses using statistical tests, and create LLM-generated marketing creatives — fully aligned with the Kasparro assignment requirements.

The system follows a complete **Planner → Agents → Evaluator → Creative Generator → Report** pipeline and produces:

- `insights.json`
- `creatives.json`
- `report.md`
- Visualizations (`reports/figures/`)
- Execution logs (`logs/`)

---
<p align="center">
  <img src="assets/demo.gif" width="800">
</p>

## 🗂️ 1. Project Structure

```
kasparro-agentic-fb-analyst-sonu-kumar-singh/
│
├── src/
│   ├── agents/
│   │   ├── data_agent.py
│   │   ├── insight_agent.py
│   │   ├── evaluator.py
│   │   ├── creative_generator.py
│   │   └── planner.py
│   ├── utils/
│   └── run.py
│
├── data/
│   └── synthetic_fb_ads_undergarments.csv
│
├── reports/
│   ├── insights.json
│   ├── creatives.json
│   ├── report.md
│   └── figures/
│
├── logs/
│   └── log_*.json
│
├── prompts/
├── config/
├── tests/
├── scripts/
│   └── clean_creatives.py
│
├── agent_graph.md
├── requirements.txt
└── README.md
```

---

## ⚙️ 2. Setup Instructions

### Install all dependencies:

```bash
pip install -r requirements.txt
```

### Set OpenAI API Key (optional):

**Windows:**
```bash
setx OPENAI_API_KEY "your_key_here"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your_key_here"
```

> **Note:** If no key is provided, the system automatically switches to offline creative generation.

---

## 🚀 3. How to Run

### Fast run (offline mode):

```bash
python -m src.run "Analyze ROAS drop"
```

### Full LLM mode (recommended):

```bash
python -m src.run "Analyze ROAS drop" --use-llm
```

### Outputs will appear in:

```
reports/
    report.md
    insights.json
    creatives.json
    figures/*.png

logs/
    log_*.json
```

---

## 🧠 4. Agent Graph (Architecture)

The system uses a modular agent pipeline:

```text
USER QUERY
    ↓
PLANNER AGENT (task breakdown)
    ↓
────────────────────────────────────────────
1. DataAgent → load + clean + summarize data
2. InsightAgent → generate hypotheses
3. EvaluatorAgent → validate using statistics
4. CreativeAgent → generate ads (LLM/fallback)
────────────────────────────────────────────
    ↓
REPORT BUILDER → Markdown + JSON outputs
```

> Full graph documentation is available in **[agent_graph.md](agent_graph.md)**.

---

## 📈 5. Sample Generated Outputs

### `insights.json`
Validated hypotheses + reasons + statistical evidence.

### `creatives.json`
LLM-generated (or fallback) creatives including:
- headline
- body copy
- CTA
- variant IDs

### `report.md`
Contains:
- Summary
- Charts
- Insights
- Recommendations
- Creative Variants

### `figures/`
Contains automatically generated:
- CTR by Creative Type
- Daily ROAS Trend

---

## 🧪 6. Testing

Run all tests using:

```bash
pytest tests/
```

---

## 📝 7. Submission

Publish your project on GitHub as:

```
kasparro-agentic-fb-analyst-sonu-kumar-singh
```

Then submit the GitHub link in the form.

---

## 👤 8. Author

**Sonu Kumar Singh**  
Applied AI Engineer Assignment — Kasparro

---

## 📄 License

This project is submitted as part of the Kasparro Applied AI Engineer assignment.

---

## 🔗 Additional Resources

- [Agent Architecture Documentation](agent_graph.md)
- [Requirements File](requirements.txt)
- [Sample Dataset](data/synthetic_fb_ads_undergarments.csv)