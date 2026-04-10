import json
import os
from datetime import datetime
from src.agents.summarize_agent import SummarizeAgent
from src.agents.insight_agent import InsightAgent
from filter_articles import filter_articles
from dedupe_articles import dedupe_articles
from score_articles import ScoreAgent


def generate_markdown_report(summarized):
    """生成 Markdown 日报内容"""
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"# AI Tech Daily - {today}\n\n"

    for i, item in enumerate(summarized[:3], 1):
        content += f"## {i}. {item['chinese_title']}\n\n"

        # 新增：可解释筛选信息
        if "importance_score" in item:
            content += f"**重要性评分：** {item['importance_score']}/10\n\n"
        if "category" in item:
            content += f"**类别：** {item['category']}\n\n"
        if "score_reason" in item:
            content += f"**入选原因：** {item['score_reason']}\n\n"

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
    
    with open("data/rss_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"已加载 {len(articles)} 条新闻\n")

    articles = filter_articles(articles)
    print(f"筛选后保留 {len(articles)} 条新闻\n")

    articles = dedupe_articles(articles)
    print(f"去重后剩余 {len(articles)} 条新闻\n")

    print("Step 1.5: 使用 MiniMax 对新闻进行重要性打分...\n")
    score_agent = ScoreAgent()

    for article in articles:
        score_result = score_agent.score_article(article)
        article["importance_score"] = score_result["importance_score"]
        article["category"] = score_result["category"]
        article["score_reason"] = score_result["reason"]
    
    articles = sorted(articles, key=lambda x: x.get("importance_score", 0), reverse=True)
    print("===== 模型打分排序结果（从高到低） =====")
    for i, article in enumerate(articles, 1):
        print(f"{i}. [{article.get('importance_score', 0)}分] {article['title']}")
    print()

    articles = articles[:3]
    print(f"排序后选出 {len(articles)} 条重点新闻\n")

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