import json
import requests


WEIGHTS = {
    "ai_relevance": 0.35,
    "market_impact": 0.30,
    "novelty": 0.20,
    "discussion_value": 0.15,
}


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
                    "max_tokens": 600,
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
        return f"""你是科技媒体编辑，请判断下面这条新闻是否值得进入 AI Tech Daily 日报，并从 4 个维度分别评分。

新闻标题：
{title}

新闻摘要：
{summary}

请从以下 4 个维度各给出 0-10 的整数评分：

1. ai_relevance：与 AI（LLM / Agent / AI Infra / AI 应用）的直接相关程度
2. market_impact：对行业、公司、资本市场、竞争格局的潜在影响
3. novelty：信息增量和新颖程度，是否只是重复报道
4. discussion_value：是否具有讨论价值、传播价值、观点延展空间

只输出合法 JSON，不允许任何 markdown、代码块、注释或 JSON 以外的文字。直接以 {{ 开头,以 }} 结尾。
{{
  "scores": {{
    "ai_relevance": 0,
    "market_impact": 0,
    "novelty": 0,
    "discussion_value": 0
  }},
  "tags": ["标签1", "标签2", "标签3"],
  "category": "AI产品 / 融资 / 芯片 / 机器人 / 泛科技 / 其他",
  "reasoning": {{
    "summary": "一句话解释入选或排除原因",
    "key_factors": ["关键因素1", "关键因素2"]
  }}
}}
"""

    def _clamp_score(self, value):
        try:
            v = float(value)
            return max(0, min(10, v))
        except (TypeError, ValueError):
            return 5

    def _compute_scoring(self, scores, tags, category, reasoning):
        ai_relevance = self._clamp_score(scores.get("ai_relevance", 5))
        market_impact = self._clamp_score(scores.get("market_impact", 5))
        novelty = self._clamp_score(scores.get("novelty", 5))
        discussion_value = self._clamp_score(scores.get("discussion_value", 5))

        final_score = round(
            WEIGHTS["ai_relevance"] * ai_relevance
            + WEIGHTS["market_impact"] * market_impact
            + WEIGHTS["novelty"] * novelty
            + WEIGHTS["discussion_value"] * discussion_value,
            2,
        )

        if final_score >= 6:
            decision_type = "deep_dive"
        elif final_score >= 2:
            decision_type = "brief"
        else:
            decision_type = "drop"

        confidence = round(final_score / 10, 2)

        safe_tags = tags if isinstance(tags, list) else []
        key_factors = reasoning.get("key_factors", [])
        safe_key_factors = key_factors if isinstance(key_factors, list) else []

        return {
            "scoring": {
                "scores": {
                    "ai_relevance": ai_relevance,
                    "market_impact": market_impact,
                    "novelty": novelty,
                    "discussion_value": discussion_value,
                },
                "final_score": final_score,
                "decision": {
                    "type": decision_type,
                    "confidence": confidence,
                },
                "tags": safe_tags,
                "category": category,
                "reasoning": {
                    "summary": reasoning.get("summary", ""),
                    "key_factors": safe_key_factors,
                },
            },
            # 向后兼容字段
            "importance_score": final_score,
            "category": category,
            "reason": reasoning.get("summary", ""),
        }

    def _parse_response(self, content):
        try:
            content = content.strip()
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
            raw = json.loads(content.strip())

            scores = raw.get("scores", {})
            tags = raw.get("tags", [])
            category = raw.get("category", "其他")
            reasoning = raw.get("reasoning", {})

            return self._compute_scoring(scores, tags, category, reasoning)

        except Exception as e:
            print(f"打分 JSON 解析失败: {str(e)}")
            return self._fallback_score()

    def _fallback_score(self):
        return self._compute_scoring(
            scores={
                "ai_relevance": 5,
                "market_impact": 5,
                "novelty": 5,
                "discussion_value": 5,
            },
            tags=[],
            category="其他",
            reasoning={
                "summary": "模型打分失败，使用默认分数",
                "key_factors": [],
            },
        )
