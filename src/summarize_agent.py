import json
import requests


class SummarizeAgent:
    def __init__(self, api_key=None, model=None):
        """初始化摘要生成器"""
        from config import MINIMAX_API_KEY, MINIMAX_API_URL, MINIMAX_MODEL

        self.api_key = api_key or MINIMAX_API_KEY
        self.model = model or MINIMAX_MODEL
        self.api_url = MINIMAX_API_URL

        if not self.api_key:
            print("警告: 未设置 MINIMAX_API_KEY，请设置环境变量")

    def summarize_articles(self, articles):
        """
        将英文科技新闻转换为中文摘要

        参数:
            articles: 英文新闻列表

        返回:
            包含中文摘要的新闻列表
        """
        summarized = []

        for article in articles:
            chinese_data = self._generate_chinese_summary(article)
            summarized.append(chinese_data)

        return summarized

    def _generate_chinese_summary(self, article):
        """为单条新闻生成中文摘要"""
        title = article.get("title", "")
        summary = article.get("summary", "")

        llm_result = self._call_llm(title, summary)

        return {
            "original_title": title,
            "chinese_title": llm_result.get("chinese_title", title),
            "chinese_summary": llm_result.get("chinese_summary", summary),
            "key_points": llm_result.get("key_points", []),
            "source": article.get("source", ""),
            "link": article.get("link", ""),
        }

    def _call_llm(self, title, summary):
        """调用 MiniMax API 生成中文摘要"""
        prompt = self._build_prompt(title, summary)

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self._parse_llm_response(content)
            else:
                print(f"MiniMax API 调用失败: {response.status_code}")
                print(response.text)
                return self._fallback_response(title, summary)

        except Exception as e:
            print(f"MiniMax 调用出错: {str(e)}")
            return self._fallback_response(title, summary)

    def _build_prompt(self, title, summary):
        """构建 prompt"""
        return f"""你是一位专业的科技新闻编辑。请将以下英文科技新闻转换为高质量的简体中文摘要。

英文标题：{title}

英文摘要：{summary}

请按以下要求输出：
1. chinese_title: 简洁有力的中文新闻标题（不要直译，要像真实新闻标题）
2. chinese_summary: 1-2句话的中文摘要，说明“发生了什么”和“为什么重要”
3. key_points: 2-3个关键要点，每个要点一句话

输出格式必须是纯 JSON：
{{
  "chinese_title": "...",
  "chinese_summary": "...",
  "key_points": ["...", "...", "..."]
}}"""

    def _parse_llm_response(self, content):
        """解析 LLM 返回的 JSON"""
        try:
            content = content.strip()
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
            return json.loads(content.strip())
        except Exception as e:
            print(f"JSON 解析失败: {str(e)}")
            return {}

    def _fallback_response(self, title, summary):
        """当 LLM 调用失败时的简单回退"""
        return {
            "chinese_title": f"[待处理] {title}",
            "chinese_summary": summary[:100] + "..." if len(summary) > 100 else summary,
            "key_points": ["信息处理中，请稍后重试"],
        }