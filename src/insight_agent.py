import requests


class InsightAgent:
    def __init__(self, api_key=None, model=None):
        """初始化 AI Insight 生成器"""
        from config import ANTHROPIC_API_KEY, ANTHROPIC_API_URL, ANTHROPIC_MODEL

        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or ANTHROPIC_MODEL
        self.api_url = ANTHROPIC_API_URL

        if not self.api_key:
            print("警告: 未设置 ANTHROPIC_API_KEY，请设置环境变量")

    def generate_insight(self, chinese_title, chinese_summary):
        """为单条新闻生成 AI Insight"""
        prompt = self._build_prompt(chinese_title, chinese_summary)

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.model,
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("content", [{}])[0].get("text", "").strip()
            else:
                print(f"Claude API 调用失败: {response.status_code}")
                print(response.text)
                return "Insight 生成失败，请稍后重试。"

        except Exception as e:
            print(f"Claude 调用出错: {str(e)}")
            return "Insight 生成失败，请稍后重试。"

    def _build_prompt(self, chinese_title, chinese_summary):
        return f"""你是一位 AI 行业分析师，请基于以下科技新闻生成一段简体中文 AI Insight。

新闻标题：
{chinese_title}

新闻摘要：
{chinese_summary}

要求：
1. 输出 1-2 句话
2. 不要重复摘要内容
3. 重点回答“这意味着什么”
4. 可以从以下角度选择：
- 行业趋势
- 商业影响
- 技术竞争
- 产品机会

请直接输出简体中文 insight，不要加标题，不要加项目符号。"""