import re


def normalize_title(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    return set(title.split())


def is_duplicate(article1, article2, threshold=0.5):
    words1 = normalize_title(article1.get("title", ""))
    words2 = normalize_title(article2.get("title", ""))

    if not words1 or not words2:
        return False

    overlap_words = words1 & words2
    similarity = len(overlap_words) / min(len(words1), len(words2))

    # 方法1：整体相似度足够高
    if similarity >= threshold:
        return True

    # 方法2：命中多个核心词，也认为是重复
    important_overlap = {"florida", "ag", "openai", "shooting", "chatgpt", "fsu"}
    if len(overlap_words & important_overlap) >= 3:
        return True

    return False


def dedupe_articles(articles):
    unique_articles = []

    for article in articles:
        is_dup = False
        for existing_article in unique_articles:
            if is_duplicate(article, existing_article):
                is_dup = True
                break

        if not is_dup:
            unique_articles.append(article)

    return unique_articles