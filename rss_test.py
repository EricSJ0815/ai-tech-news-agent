import feedparser

rss_url = "https://techcrunch.com/feed/"

feed = feedparser.parse(rss_url)

print("Feed title:", feed.feed.get("title", "No title"))
print()

for i, entry in enumerate(feed.entries[:5], 1):
    print(f"{i}. {entry.get('title', 'No title')}")
    print(entry.get("link", "No link"))
    print(entry.get("published", "No published date"))
    print("-" * 50)