import json
import requests


class ScoreAgent:
    def __init__(self, api_key=None, model=None):
        from config import MINIMAX_API_KEY, MINIMAX_API_URL, MINIMAX_MODEL

        self.api_key = api_key or MINIMAX_API_KEY
        self.model = model or MINIMAX_MODEL
        self.api_url = MINIMAX_API_URL

        if not self.api_key:
            print("警告: 未设置 MINIMAX_API_KEY，请设置环境变量")

    def score_article(self, article):
        title = article.get("title", "")
        summary = article.get("summary", "")

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
                    "temperature": 0.2,
                    "max_tokens": 300,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self._parse_response(content)

            else:
                print(f"MiniMax 打分失败: {response.status_code}")
                print(response.text)
                return self._fallback_score()

        except Exception as e:
            print(f"MiniMax 打分出错: {str(e)}")
            return self._fallback_score()

    def _build_prompt(self, title, summary):
        return f"""你是科技媒体编辑，请判断下面这条新闻是否值得进入 AI Tech Daily 日报，并给出评分。

新闻标题：
{title}

新闻摘要：
{summary}

请从以下角度综合判断：
1. AI相关性
2. 行业影响力
3. 商业价值
4. 技术突破性

请输出纯 JSON，格式如下：
{{
  "importance_score": 0-10,
  "category": "AI产品 / 融资 / 芯片 / 机器人 / 泛科技 / 其他",
  "reason": "一句话解释为什么"
}}
"""

    def _parse_response(self, content):
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
            print(f"打分 JSON 解析失败: {str(e)}")
            return self._fallback_score()

    def _fallback_score(self):
        return {
            "importance_score": 5,
            "category": "其他",
            "reason": "模型打分失败，使用默认分数"
        }