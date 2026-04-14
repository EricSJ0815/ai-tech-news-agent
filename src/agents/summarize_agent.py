import json
import requests

from src.utils.cache import ArticleCache, make_key

_cache = ArticleCache()


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
        """为单条新闻生成中文摘要（命中缓存则跳过模型调用）"""
        title = article.get("title", "")
        summary = article.get("summary", "")
        decision_type = article.get("scoring", {}).get("decision", {}).get("type", "brief")

        # Cache key includes decision_type so deep_dive / brief 内容分开存储
        cache_key = make_key(article.get("link", ""), title, article.get("source", ""))
        cache_key = f"{cache_key}|{decision_type}"
        cached = _cache.get("summary", cache_key)
        if cached is not None:
            return cached

        llm_result = self._call_llm(title, summary, decision_type)

        result = {
            "essence": llm_result.get("essence", ""),
            "original_title": title,
            "angle_title": llm_result.get("angle_title", ""),
            "why_it_matters": llm_result.get("why_it_matters", ""),
            "chinese_title": llm_result.get("chinese_title", title),
            "chinese_summary": llm_result.get("chinese_summary", summary),
            "key_points": llm_result.get("key_points", []),
            "source": article.get("source", ""),
            "link": article.get("link", ""),
            "importance_score": article.get("importance_score"),
            "category": article.get("category"),
            "score_reason": article.get("score_reason"),
        }
        _cache.set("summary", cache_key, result)
        return result

    def _call_llm(self, title, summary, decision_type="brief"):
        """调用 MiniMax API 生成中文摘要"""
        prompt = self._build_prompt(title, summary, decision_type)

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
                    "max_tokens": 1024,
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

    def _build_prompt(self, title, summary, decision_type="brief"):
        """构建 prompt，根据 decision_type 调整内容强度分层"""
        essence_block = ""  # Only populated for deep_dive

        if decision_type == "deep_dive":
            essence_block = (
                "\n0. essence：【本质句，JSON 第一个字段，必须满足以下全部要求】\n"
                "   - 用一句话说明这条新闻的「核心变化」\n"
                "   - 优先使用「从 A → B」结构（如：从模型能力竞争 → 商业化收入竞争）\n"
                "   - 如不适合用「→」，可用「不再是 X，而是 Y」结构\n"
                "   - 【严禁】空话：「AI 正在发展」「技术不断进步」「行业正在变革」\n"
                "   - 必须具体到公司 / 赛道 / 动作 / 市场层\n"
                "   【合格示例】：\n"
                "   - 「从模型能力竞争 → 企业客户收入竞争」\n"
                "   - 「AI 辅助工具不再只面向开发者，开始进入普通消费者日常决策」\n"
                "   - 「搜索入口定义权从算法层转移到 AI 对话层」\n"
                "   - 「监管从「讨论」进入「执法」阶段，合规成本开始实质性落地」"
            )
            angle_title_rules = (
                "1. angle_title：【Deep Dive 强判断标题】必须同时满足以下全部要求：\n"
                "   - 表达「判断 / 趋势 / 战略意图」，而不是描述事件本身\n"
                "   - 必须体现「变化」而不是「状态」，让读者一眼看出行业正在发生什么转向\n"
                "   - 优先使用以下结构（任选一种）：\n"
                "     「不只是…而是…」/「从…转向…」/「开始取代…」/「正在重塑…」/「不再是…而是…」/「本质上…」/「把…带向…」\n"
                "   - 如果可能，优先体现「旧 vs 新」的对比，例如：\n"
                "     从模型能力 → 商业化能力 / 从通用 → 场景分层 / 从工具 → 基础设施\n"
                "   - 必须回答隐含问题：这家公司在做什么战略动作？行业正在发生什么转向？\n"
                "   - 允许轻微主观判断，这是编辑风格，不是论文\n"
                "   【必须避免】：\n"
                "   - 「某公司发布了…」/「某公司推出了…」/「某产品更新了…」\n"
                "   - 描述状态而不体现变化的句子\n"
                "   【合格示例】：\n"
                "   - 「OpenAI 正把 AI 工具从效率插件重塑为可分层定价的基础设施」\n"
                "   - 「Anthropic 不再打通用能力，而是把竞争带向企业场景分层」\n"
                "   - 「Google 的这个动作本质上是在把搜索入口的定义权从传统算法转移到 AI」"
            )
            why_it_matters_rules = (
                "2. why_it_matters：【2~3 句话】，严格按以下结构展开：\n"
                "   第1句（必须）：谁赢谁输——哪家公司 / 哪类产品会从中获益，哪类会受压\n"
                "   第2句（必须）：对市场结构的影响——这会改变竞争格局 / 定价逻辑 / 用户行为吗？\n"
                "   第3句（可选）：趋势判断——这是否标志着某个行业趋势正在加速或转向？\n"
                "   【强制要求】：\n"
                "   - 不允许重复摘要内容\n"
                "   - 不允许只有1句话\n"
                "   - 必须从竞争/商业层给出判断，语气像给投资人写的竞争分析"
            )
            chinese_summary_rules = (
                "4. chinese_summary：【Deep Dive 深度摘要】必须写 3~5 句话，严格按以下顺序展开：\n"
                "   第1句：发生了什么（核心事件，时间/规模/范围要具体）\n"
                "   第2句：公司具体做了什么（动作细节，有哪些 feature / 机制 / 参数）\n"
                "   第3句：为什么现在做（动机或背景，竞争压力 / 市场时机 / 战略需要）\n"
                "   第4~5句（可选）：与过去有什么不同，或与竞品相比有何差异\n"
                "   【强制要求】：\n"
                "   - 每句都必须包含具体信息，不允许空洞表达\n"
                "   - 不允许重复同一个意思\n"
                "   - 不允许写成单纯摘要风（「该公司宣布…」结束即可），必须有分析密度\n"
                "   【中文自然表达】：\n"
                "   - 禁止翻译腔：「该公司」「本次」「此举旨在」「据报道」\n"
                "   - 用主动句和短句，避免一句话超过50字\n"
                "   - 像《第一财经》《晚点LatePost》的中文科技报道风格"
            )
            key_points_rules = (
                "5. key_points：【Deep Dive 核心信息点】必须写 3~5 条，每条一句话，要求：\n"
                "   - 每条必须是具体信息（数字 / feature 名称 / 机制 / 对象 / 范围）\n"
                "   - 尽量包含数据、产品名、技术机制，避免泛化表达\n"
                "   - 禁止出现「提升了效率」「增强了能力」「优化了体验」等空洞短语\n"
                "   【合格示例】：\n"
                "   - 「上下文窗口从 128K 扩展至 1M tokens，主要针对代码和长文档场景」\n"
                "   - 「新定价层 $200/月，包含无限制 o3 访问，面向专业开发者」\n"
                "   - 「API 延迟中位数降至 800ms，较上一版本降低 40%」"
            )
            json_schema = """{
  "essence": "...",
  "angle_title": "...",
  "why_it_matters": "...",
  "chinese_title": "...",
  "chinese_summary": "...",
  "key_points": ["...", "...", "...", "...", "..."]
}"""
            field_count = "6 个"
            extra_rules = ""

        else:  # brief
            angle_title_rules = (
                "1. angle_title：【信号标题】\n"
                "   - 表达「发生的关键动作」或「行业变化方向」\n"
                "   - 一眼能抓住信号，语气简洁有力\n"
                "   - 优先表达变化，而不是描述状态\n"
                "   【合格示例】：\n"
                "   - 「Meta 在开源端加速布局」\n"
                "   - 「企业 AI 采购正在向垂直场景集中」\n"
                "   - 「小模型开始承接更多推理任务」\n"
                "   【避免】：「某公司发布了…」「某产品推出了…」等纯事件描述"
            )
            why_it_matters_rules = (
                "2. why_it_matters：【信号句，必须以「👉 信号：」开头，共1句话】\n"
                "   格式：「👉 信号：[直接结论]」\n"
                "   - 回答：这条新闻为什么值得专业读者关注？\n"
                "   - 直接给判断，不描述事实（事实已在 chinese_summary 里）\n"
                "   - 语气像 VC 合伙人的内部简报\n"
                "   【严格禁止】：\n"
                "   - 以「这」开头的解释性句子\n"
                "   - 「因为…所以…」「由于…导致…」「这意味着…」\n"
                "   - 纯陈述句（没有判断方向）\n"
                "   【合格示例】：\n"
                "   - 「👉 信号：电动车赛道正从高端竞争转向规模化平价竞争」\n"
                "   - 「👉 信号：大模型厂商开始把能力变现从 API 转向订阅制」\n"
                "   - 「👉 信号：监管压力首次落到合规成本层，中小 AI 公司面临淘汰」"
            )
            chinese_summary_rules = (
                "4. chinese_summary：【2–3 句自然中文，必须有信息密度】\n"
                "   第1句（必须）：发生了什么——谁做了什么，规模/范围/数字要具体\n"
                "   第2句（必须）：具体细节——产品特性、参数、时间节点、影响范围中的1–2个\n"
                "   第3句（可选）：背景或对比——与之前有什么不同，或行业意义（一句话，不展开）\n"
                "   【要求】：\n"
                "   - 每句必须包含至少1个具体信息（数字/产品名/公司名/时间）\n"
                "   - 用自然中文，像人写的，不是英文直译\n"
                "   - 总长度控制在 60–120 字之间\n"
                "   【严禁】：\n"
                "   - 因果解释（「为了…」「由于…」「因为…所以…」）\n"
                "   - 直译腔（「该公司宣布…」「本次发布…」「此举旨在…」）\n"
                "   - 只写1句话（信息量不足）\n"
                "   【合格示例】：\n"
                "   - 「YouTube 宣布上调美国区 Premium 价格，个人月费从 $13.99 升至 $15.99，家庭版从 $22.99 升至 $24.99。这是继去年 11 月后第二次涨价，涨幅约 13%。YouTube 同步宣布允许创作者发布最长 3 分钟的 Shorts。」\n"
                "   - 「Snap 推出新一代 AR 眼镜 Spectacles 5，支持室内空间映射和手势操控，面向美国开发者限量开放申请。眼镜内置双摄、Wi-Fi 6 连接，单次使用续航约 45 分钟。定价尚未公布，预计今年晚些时候正式上市。」"
            )
            key_points_rules = (
                "5. key_points：【2~3 个信息点】\n"
                "   - 每条一句话，优先包含数字 / 产品名 / 具体机制\n"
                "   - 不重复 chinese_summary\n"
                "   - 禁止「提升了效率」「增强了能力」「优化了体验」等空洞短语"
            )
            json_schema = """{
  "angle_title": "...",
  "why_it_matters": "...",
  "chinese_title": "...",
  "chinese_summary": "...",
  "key_points": ["...", "...", "..."]
}"""
            field_count = "5 个"
            extra_rules = ""

        return f"""你是一位 AI 科技媒体的资深编辑，风格参考 The Information / 投资人竞争分析简报。请处理以下英文科技新闻。

英文标题：{title}

英文摘要：{summary}

请按以下 {field_count} 字段输出，必须是纯 JSON，不允许任何 markdown 或代码块：
{essence_block}

{angle_title_rules}

{why_it_matters_rules}

3. chinese_title：简洁准确的中文新闻标题（比 angle_title 更中性，适合存档）

{chinese_summary_rules}

{key_points_rules}
{extra_rules}
【中文写作质量要求】（适用于所有字段）：
- 语言要自然，像中文母语者写的，而不是英文翻译过来的
- 避免以下翻译腔表达：「该公司」「本次」「此举」「旨在」「据悉」「据报道」
- 避免主谓分离过远的句式（中文里主语和谓语应紧密相连）
- 用主动语态，避免「被…」的被动句（除非原文强调被动性）
- 数字保留英文（$200/月，不写「200美元每月」）

输出纯 JSON：
{json_schema}"""

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
            "essence": "",
            "angle_title": "",
            "why_it_matters": "",
            "chinese_title": f"[待处理] {title}",
            "chinese_summary": summary[:100] + "..." if len(summary) > 100 else summary,
            "key_points": ["信息处理中，请稍后重试"],
        }
