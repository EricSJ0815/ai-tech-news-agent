import streamlit as st
import json
from pathlib import Path

from src.agents.summarize_agent import SummarizeAgent
from src.agents.insight_agent import InsightAgent

st.set_page_config(
    page_title="AI Tech News Agent",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Tech News Agent")
st.caption("Turn English tech news into Chinese summaries, key points, and AI insights.")

st.markdown("### Choose Input Source")

use_sample = st.checkbox("Use built-in sample data", value=True)
uploaded_file = st.file_uploader("Or upload a JSON file", type="json")

articles = None

if use_sample:
    sample_path = Path("data/sample_articles.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        articles = json.load(f)
    st.success("Loaded sample_articles.json")
elif uploaded_file is not None:
    articles = json.load(uploaded_file)
    st.success("Uploaded JSON loaded successfully")

if articles is not None:
    st.markdown(f"**Articles loaded:** {len(articles)}")

    if st.button("Generate Report", type="primary"):
        progress_text = st.empty()
        progress_text.info("Generating Chinese summaries...")
        summarize_agent = SummarizeAgent()
        summarized = summarize_agent.summarize_articles(articles)

        progress_text.info("Generating AI insights...")
        insight_agent = InsightAgent()

        for item in summarized[:3]:
            insight = insight_agent.generate_insight(
                item["chinese_title"],
                item["chinese_summary"]
            )
            item["ai_insight"] = insight

        progress_text.success("Report generated successfully")

        st.markdown("---")
        st.markdown("## 📰 AI Tech Daily")

        for i, item in enumerate(summarized[:3], 1):
            with st.container():
                st.markdown(f"### {i}. {item['chinese_title']}")
                st.write(f"**摘要：** {item['chinese_summary']}")

                st.write("**要点：**")
                for p in item["key_points"]:
                    st.write(f"- {p}")

                st.write(f"**AI Insight：** {item['ai_insight']}")

                if item.get("source"):
                    st.write(f"**Source:** {item['source']}")
                if item.get("link"):
                    st.write(f"**Link:** {item['link']}")

                st.markdown("---")
else:
    st.warning("Please use sample data or upload a JSON file.")