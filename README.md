# 🧠 AI Tech News Agent

An AI-powered multi-model pipeline that transforms English tech news into structured Chinese summaries, key insights, and daily reports.

---

## 🚀 Overview

This project is an **AI News Intelligence Agent** that automates the full pipeline of:

**RSS Tech News → Filtering → Deduplication → LLM-based Ranking → Chinese Summary → AI Insight → Daily Report**

Unlike simple summarization tools, this system introduces a **decision-making layer**, enabling the agent to determine:

- Which news is relevant
- Which news is important
- Why it should be included in the daily reportproducts.

## ⚙️ Architecture

```text
[Tech News RSS]
        ↓
  RSS → JSON Conversion
        ↓
  Rule-based Filtering
        ↓
  Deduplication
        ↓
  LLM-based Scoring (MiniMax)
        ↓
  Top-K Selection
        ↓
  MiniMax → Chinese Summarization
        ↓
  Claude → AI Insight Generation
        ↓
  Markdown Daily Report
```

## Key Features
🧠 AI Decision Layer (Core Innovation)

- LLM-based importance scoring (0–10)
- Category classification (AI Product / Funding / Chip / etc.)
- Explainable selection reasoning

🧩 Multi-model Orchestration

- MiniMax → summarization + scoring (cost-efficient)
- Claude (Sonnet) → high-quality reasoning (AI Insight)

🧹 Data Processing Pipeline

- Rule-based filtering (remove irrelevant content)
- Title-based deduplication (remove duplicate events)
- Top-K ranking selection

📊 Explainable Output

Each selected news includes:
- Importance score
- Category
- Reason for selection

📝 Structured Output

- Markdown daily report
- Ready for automation / publishing / integration

## Demo Output
Example of generated daily report:
```
## 1. Snap有望重启AR眼镜项目，携手高通推进新品研发

**重要性评分：** 8/10

**类别：** AI产品

**入选原因：** Snap的AR眼镜涉及AI技术应用，且与高通合作可能带来技术突破，对AI硬件领域有重要影响。

**摘要：** Snap公司宣布与高通达成新合作，这标志着其搁置多年的增强现实眼镜项目或将迎来重要进展。

**要点：**
- Snap与高通建立新合作伙伴关系，旨在推动AR眼镜研发。
- 该项目曾长期处于停滞状态，此次合作有望带来突破。
- AR眼镜被视为Snap未来发展的重要方向，市场期待已久。

**AI Insight：** 这一合作表明AR眼镜市场正进入新的竞争阶段，Snap凭借其在社交AR领域的内容生态优势，有望在苹果Vision Pro引领的空间计算浪潮中占据差异化定位。高通芯片技术的加持将帮助Snap解决此前AR硬件项目面临的功耗和性能瓶颈，为消费级AR眼镜的普及奠定技术基础。

**来源：** TechCrunch

**链接：** https://techcrunch.com/2026/04/10/snap-gets-closer-to-releasing-new-ai-glasses-after-years-long-hiatus/
```
🖥️ Web UI Preview


## Project Structure
```
ai-tech-news-agent/
│
├── main.py                     # Pipeline entry point
├── config.py                   # API config
│
├── src/
│   ├── summarize_agent.py      # MiniMax summarization
│   └── insight_agent.py        # Claude insight generation
│
├── filter_articles.py          # Rule-based filtering
├── dedupe_articles.py          # Deduplication logic
├── score_articles.py           # LLM scoring agent
│
├── data/                       # (ignored in Git)
├── output/                     # (ignored in Git)
```

## Setup
1. Clone repository
```
git clone https://github.com/EricSJ0815/ai-tech-news-agent.git
cd ai-tech-news-agent
```

2. Install dependencies
```
pip install -r requirements.txt
```
3. Configure environment variables
```
## Create a `.env` file:
```env
MINIMAX_API_KEY=your_minimax_key
ANTHROPIC_API_KEY=your_claude_key
```

## Run
```
python main.py
```
Output will be generated in:
```
output/daily_report.md
```

## Future Improvements
- Multi-source ingestion (Reuters, The Verge, etc.)
- Scheduled automation (daily cron job)
- Streamlit dashboard enhancement
- Email / Notion / Slack integration
- Personalized topic filtering
- LLM-based filtering agent (full replacement of rule-based filter)

## This project demonstrates how to:
- Building AI Agents beyond simple LLM calls
- Designing multi-stage intelligent pipelines
- Combining rule-based systems + LLM decision-making
- Creating explainable AI systems
- Thinking from tool → system → product

👤 Author
```
Baijun Song
AI / LLM Applications / AI Agent Systems
```
