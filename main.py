import json
import os
from datetime import datetime
from src.summarize_agent import SummarizeAgent
from src.insight_agent import InsightAgent


def generate_markdown_report(summarized):
    """生成 Markdown 日报内容"""
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"# AI Tech Daily - {today}\n\n"

    for i, item in enumerate(summarized[:3], 1):
        content += f"## {i}. {item['chinese_title']}\n\n"
        content += f"**摘要：** {item['chinese_summary']}\n\n"

        content += f"**要点：**\n"
        for point in item["key_points"]:
            content += f"- {point}\n"

        content += "\n"
        content += f"**AI Insight：** {item.get('ai_insight', '暂无')}\n\n"
        content += f"**来源：** {item['source']}\n\n"
        content += f"**链接：** {item['link']}\n\n"
        content += "---\n\n"

    return content


def main():
    print("=== AI Tech News Intelligence Agent ===\n")

    # 读取测试数据
    print("Step 1: 加载测试数据...")
    with open("data/sample_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"已加载 {len(articles)} 条新闻\n")

    # 生成中文摘要（MiniMax）
    print("Step 2: 生成中文摘要（MiniMax）...\n")
    summarize_agent = SummarizeAgent()
    summarized = summarize_agent.summarize_articles(articles)

    # 生成 AI Insight（Claude）
    print("Step 3: 生成 AI Insight（Claude）...\n")
    insight_agent = InsightAgent()

    for item in summarized[:3]:
        insight = insight_agent.generate_insight(
            item["chinese_title"],
            item["chinese_summary"]
        )
        item["ai_insight"] = insight

    # 生成 Markdown 内容
    print("Step 4: 生成 Markdown 日报...\n")
    markdown_content = generate_markdown_report(summarized)

    # 确保 output 目录存在
    os.makedirs("output", exist_ok=True)

    # 写入文件
    file_path = "output/daily_report.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print("✅ 日报已生成：", file_path)


if __name__ == "__main__":
    main()