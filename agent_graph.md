# Agent Graph — Kasparro Agentic FB Analyst

This document explains the complete agent architecture for the FB Ads Analyst system.  
It shows how data flows between agents, the input/output schema, and how the final outputs are generated.

---

## 🔷 High-Level Architecture  
**(Planner → Agents → Evaluator → Creative Generator → Report)**

```text
                  ┌────────────────────┐
                  │     USER QUERY     │
                  └──────────┬─────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │   PLANNER AGENT    │
                  │ (task breakdown)   │
                  └──────────┬─────────┘
                             │ tasks[]
                             ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                     EXECUTION SEQUENCE                         │
 │                                                                │
 │   1. DataAgent → Load + clean data → df, summaries            │
 │   2. InsightAgent → Generate hypotheses                       │
 │   3. EvaluatorAgent → Score hypotheses with statistics        │
 │   4. CreativeAgent → Generate ads (LLM or fallback)           │
 │                                                                │
 └───────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │    REPORT BUILDER  │
                  │ report.md + JSON   │
                  └──────────┬─────────┘
                             │
                             ▼
                 reports/{insights,creatives,report}.*
```

---

## 🔷 Agent Descriptions

### **1. Planner Agent**
**File:** `src/agents/planner.py`  
**Responsibility:**  
Turn a natural-language query (e.g., "Analyze ROAS drop") into structured tasks.

**Output Schema:**
```json
{
  "query": "Analyze ROAS drop",
  "tasks": [
    {"task_id": "load_data", "agent": "DataAgent"},
    {"task_id": "summarize_data", "agent": "DataAgent"},
    {"task_id": "generate_hypotheses", "agent": "InsightAgent"},
    {"task_id": "evaluate_hypotheses", "agent": "EvaluatorAgent"},
    {"task_id": "generate_creatives", "agent": "CreativeAgent"},
    {"task_id": "compile_report", "agent": "ReportGenerator"}
  ],
  "total_tasks": 6
}
```

### **2. Data Agent**
**File:** `src/agents/data_agent.py`  
**Responsibility:**

- Load dataset (CSV)
- Clean & enrich fields
- Compute ROAS, CTR, spend summaries
- Provide summary for LLM context

**Outputs:**

- `df` (clean DataFrame)
- `prompt_summary`
- Top campaigns
- ROAS/CTR statistics

### **3. Insight Agent**
**File:** `src/agents/insight_agent.py`  
**Responsibility:**

- Analyze performance trends
- Generate hypotheses about ROAS/CTR issues
- Attach affected campaigns

**Example Output:**
```json
[
  {
    "hypothesis": "Creative fatigue or weak messaging",
    "reason": "CTR < 1% for key campaigns",
    "affected_campaigns": ["Men Bold Colors Drop", "WOMEN Seamless Everyday"]
  }
]
```

### **4. Evaluator Agent**
**File:** `src/agents/evaluator.py`  
**Responsibility:**  
Validate hypotheses using statistical evidence.

**Uses:**

- Kruskal–Wallis test
- CTR by creative_type
- ROAS recent vs previous window
- Variance comparison

**Outputs:**

- Confidence score
- Evidence list

### **5. Creative Generator**
**File:** `src/agents/creative_generator.py`  
**Responsibility:**

- Generate creatives using OpenAI LLM (JSON only)
- Fallback creative generation if LLM is off
- Normalize campaign keys
- Return ad variants with headline, body, CTA

**Output Example:**
```json
{
  "Men ComfortMax": [
    {
      "variant_id": "v1",
      "headline": "Cloud-Soft Comfort",
      "body": "Premium modal comfort.",
      "cta": "Shop now"
    }
  ]
}
```

---

## 🔷 Data Flow Diagram

```text
dataset.csv
     │
     ▼
┌───────────────┐
│   DataAgent   │
└───────┬───────┘
        │ df + summary
        ▼
┌───────────────┐
│ InsightAgent  │
└───────┬───────┘
        │ hypotheses[]
        ▼
┌───────────────┐
│ EvaluatorAgent│
└───────┬───────┘
        │ scored_hypotheses[]
        ▼
┌───────────────┐
│ CreativeAgent │
└───────┬───────┘
        │ creatives{}
        ▼
      report.md
```

---

## 🔷 Example Execution Flow

1. User enters: "Analyze ROAS drop"
2. **Planner Agent** → breaks into tasks
3. **Data Agent** → loads + cleans data
4. **Insight Agent** → creates hypotheses
5. **Evaluator Agent** → validates them
6. **Creative Agent** → generates ad variants
7. **Report Builder** creates:
   - `insights.json`
   - `creatives.json`
   - `report.md`
   - Charts in `reports/figures/`
8. Log file created under `/logs/`

---

