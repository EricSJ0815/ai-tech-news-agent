def is_relevant_article(article):
    title = article.get("title", "").lower()
    summary = article.get("summary", "").lower()

    include_keywords = [
        "ai", "openai", "chatgpt", "meta ai", "claude",
        "anthropic", "llm", "model", "chip", "robot", "fusion"
    ]

    exclude_keywords = [
        "save", "discount", "pass", "ticket", "event"
    ]

    has_include = any(keyword in title or keyword in summary for keyword in include_keywords)
    has_exclude = any(keyword in title or keyword in summary for keyword in exclude_keywords)

    return has_include and not has_exclude


def filter_articles(articles):
    return [article for article in articles if is_relevant_article(article)]