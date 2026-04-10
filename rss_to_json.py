import feedparser
import json

rss_url = "https://techcrunch.com/feed/"
feed = feedparser.parse(rss_url)

articles = []

for entry in feed.entries[:10]:
    article = {
        "title": entry.get("title", ""),
        "summary": entry.get("summary", ""),
        "link": entry.get("link", ""),
        "source": "TechCrunch"
    }
    articles.append(article)

# 保存成 JSON 文件
with open("data/rss_articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"Saved {len(articles)} articles to data/rss_articles.json")