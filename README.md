# 🧠 AI Tech News Agent

An AI-powered multi-model pipeline that transforms English tech news into structured Chinese summaries, key insights, and daily reports.

---

## 🚀 Overview

This project is an AI content intelligence agent that automates the entire pipeline of:

**English Tech News → Chinese Structured Insights → AI Industry Analysis → Daily Report**

It leverages a **multi-model architecture**:

- **MiniMax** → Efficient batch summarization (title, summary, key points)
- **Claude (Sonnet)** → High-quality AI Insight generation

The final output is a **production-ready Markdown daily report**, suitable for content automation, research workflows, and AI-driven media products.

## ⚙️ Architecture

```text
[Tech News (JSON / API)]
        ↓
      MiniMax →  Summarization
        ↓
      Claude →  Insight Generation
        ↓
  Markdown Daily Report
```

## Key Features
🧩 Multi-model orchestration (MiniMax + Claude)
💰 Cost-efficient design
Low-cost model for bulk processing
High-quality model for reasoning tasks
🧠 AI-generated industry insights
📝 Automated structured content output (Markdown)
⚡ Modular Python architecture with API abstraction

## Demo Output
Example of generated daily report:
```
📰 AI Tech Daily
1. OpenAI发布GPT-5：多模态推理能力大幅提升
摘要：
OpenAI推出了具备多模态推理能力的GPT-5，在复杂问题解决任务上提升40%。
要点：
支持图像、音频、文本多模态处理
复杂推理能力显著提升
在科研与代码生成领域表现突出
AI Insight：
AI 正在从单一模型能力走向多模态统一智能，这将加速 AI 在教育、创意和自动化领域的落地，同时进一步拉开头部模型之间的技术差距。
```

## Project Structure
```
ai-tech-news-agent/
│
├── main.py                 # Pipeline entry point
├── config.py               # API config
│
├── src/
│   ├── summarize_agent.py  # MiniMax summarization
│   └── insight_agent.py    # Claude insight generation
│
├── data/
│   └── sample_articles.json
│
├── output/
│   └── daily_report.md
```

## Setup
1. Clone repository
git clone https://github.com/EricSJ0815/ai-tech-news-agent.git
cd ai-tech-news-agent
2. Install dependencies
pip install -r requirements.txt
3. Configure environment variables

## Create a `.env` file:
```env
MINIMAX_API_KEY=your_minimax_key
ANTHROPIC_API_KEY=your_claude_key
```

## Run
python main.py

Output will be generated in:
output/daily_report.md

## Future Improvements
- Automatic news ingestion (RSS / API / scraping)
- Streamlit-based web UI
- News importance filtering agent
- Email / Notion integration
- Personalized topic-based reports
- Why This Project Matters

## This project demonstrates how to:
- Design a multi-model AI system
- Optimize cost vs quality trade-offs
- Build a complete AI content pipeline
- Move from LLM usage → AI product thinking

👤 Author
```
Baijun Song
AI / LLM Applications / AI Agent Systems
```
