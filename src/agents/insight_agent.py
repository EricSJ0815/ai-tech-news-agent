import requests
import time

from src.utils.logger import get_logger
from src.utils.cache import ArticleCache, make_key

_log = get_logger()
_cache = ArticleCache()

# Graceful degradation text shown in UI when both providers fail.
# Must NOT look like an error message to end users.
_DEGRADED_INSIGHT = "当前分析服务繁忙，建议结合原文判断该事件的行业影响。"

# Fallback closing note when AI generation fails entirely.
_CLOSING_FALLBACK = (
    "今天的信号指向 AI 行业从「能力比拼」转向「商业兑现」，竞争焦点开始落到谁先跑通付费闭环。\n"
    "头部公司的动作在同步密集，格局收紧的速度快于多数人的预期。\n"
    "今天最值得记住的一句话：模型能力的差距正在收窄，但商业化节奏的差距才刚刚开始拉大。"
)


def _build_closing_fallback(deep_dive_items, brief_items):
    """模板降级版今日结论，当 AI 生成失败时使用。"""
    top = (deep_dive_items + brief_items)[:3]
    changes = []
    for item in top:
        title = (item.get("angle_title") or item.get("chinese_title", "")).strip()
        if title:
            changes.append(title)

    lines = ["今天的信号集中指向 AI 商业化与格局竞争两条主线。"]
    for title in changes[:2]:
        lines.append(f"其中值得关注的是：{title}。")
    lines.append("今天最值得记住的判断：谁能率先把技术优势转化为用户留存，谁就掌握了下一轮竞争的主动权。")
    return "\n".join(lines)


class InsightAgent:
    def __init__(self, api_key=None, model=None):
        """初始化 AI Insight 生成器"""
        from config import (
            ANTHROPIC_API_KEY, ANTHROPIC_API_URL, ANTHROPIC_MODEL,
            OPENAI_API_KEY, OPENAI_API_URL, OPENAI_MODEL,
        )

        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or ANTHROPIC_MODEL
        self.api_url = ANTHROPIC_API_URL

        self.openai_api_key = OPENAI_API_KEY
        self.openai_api_url = OPENAI_API_URL
        self.openai_model = OPENAI_MODEL

        if not self.api_key:
            _log.warning("未设置 ANTHROPIC_API_KEY，请设置环境变量")
        if not self.openai_api_key:
            _log.warning("未设置 OPENAI_API_KEY，OpenAI fallback 不可用")

    def generate_insight(self, chinese_title, chinese_summary, final_score=7,
                         link="", source=""):
        """为单条新闻生成 AI Insight。
        优先使用 Claude；多次失败后自动切换 OpenAI；两者都失败则返回降级文案。
        命中缓存时直接返回，不调用任何模型。

        link / source 仅用于构建缓存 key，不影响输出内容。
        """
        # ── 0. 缓存检查 ────────────────────────────────────────────────────
        # score_bucket 区分高/中强度 prompt，避免用错误强度的缓存
        score_bucket = "high" if final_score >= 8 else "mid"
        cache_key = make_key(link, chinese_title, source) + f"|{score_bucket}"
        cached = _cache.get("insight", cache_key)
        if cached is not None:
            return cached

        prompt = self._build_prompt(chinese_title, chinese_summary, final_score)

        # ── 1. 尝试 Claude（最多 3 次）────────────────────────────────────
        result = self._call_claude(prompt, chinese_title)
        if result is not None:
            _cache.set("insight", cache_key, result)
            return result

        # ── 2. Claude 全部失败 → 切换 OpenAI ─────────────────────────────
        _log.warning(f"[insight] Claude 全部重试失败，切换 OpenAI fallback | title={chinese_title[:40]}")
        result = self._call_openai(prompt, chinese_title)
        if result is not None:
            _cache.set("insight", cache_key, result)
            return result

        # ── 3. 两者都失败 → 降级文案（不写入缓存，避免缓存错误状态）─────────
        _log.error(
            f"[insight] Claude 和 OpenAI 均失败，使用降级文案 | title={chinese_title[:40]}"
        )
        return _DEGRADED_INSIGHT

    def generate_closing_note(self, deep_dive_items, brief_items):
        """生成今日结论（4–6 句）：主线 + 2–3 个关键变化 + 收束判断。
        优先使用 Claude；失败后用 OpenAI；都失败则返回模板降级内容。
        结果不写入 cache（每次运行内容不同）。
        """
        if not deep_dive_items and not brief_items:
            return _CLOSING_FALLBACK

        # 只取前5篇高分文章的摘要喂给模型
        top = (deep_dive_items + brief_items)[:5]
        articles_text = "\n\n".join(
            f"【{i+1}】{item.get('angle_title') or item.get('chinese_title', '')}\n"
            f"  摘要：{item.get('chinese_summary', '')[:120]}\n"
            f"  信号：{item.get('why_it_matters', '')[:100]}"
            for i, item in enumerate(top)
        )

        prompt = f"""你是 AI 科技媒体的资深编辑，每天为专业读者写今日结论。

今日重点文章（按重要性排序）：
{articles_text}

请根据以上内容，写「今日结论」。

【严格输出结构，按行输出，不加任何标题或解释】：

第1行：「今天最重要的变化是：[一句话，概括当天最核心的单一主线]」
（从所有文章中提炼出最重要的主线，必须具体，不能泛化）

中间：2–4 条 bullet，每条以「• 」开头，每条独立一行
（每条一句话，具体，不重复，必须有公司/产品/数字/赛道等具体信息）

最后一行：「接下来：[未来判断，预测接下来会发生什么或什么值得持续观察]」
（语气像 VC 内部分析，给出1个具体的方向性判断，不能是问句）

写作规则：
- 不能重复以上文章的原句，必须提炼
- 不写"综上所述"、"总体来看"等套话
- 中文要自然，像人写的
- bullet 每条必须有具体信息，禁止「AI 正在发展」「行业正在变革」等空话

输出示例（仅参考格式，不要照抄内容）：
今天最重要的变化是：AI 工具正从「开发者专用」转向「企业全员部署」
• 微软将 Copilot 从插件升级为企业协作基础设施，目标覆盖 500 强中 85% 的工作场景
• Meta 开源 Llama 3 405B，首次在通用评测上超越 GPT-4o
• 欧盟 AI Act 高风险分类首次落地执法，3 家大厂被迫暂停特定功能
接下来：争夺 AI 工具在企业中的「默认入口」将成为下半年最关键的竞争节点

直接输出文本，不加标题，不加任何解释。"""

        result = self._call_claude(prompt, "closing_note")
        if result is not None:
            _log.info("[closing] Claude 生成今日结论成功")
            return result

        _log.warning("[closing] Claude 失败，切换 OpenAI 生成今日结论")
        result = self._call_openai(prompt, "closing_note")
        if result is not None:
            _log.info("[closing] OpenAI 生成今日结论成功")
            return result

        _log.error("[closing] Claude 和 OpenAI 均失败，使用模板降级")
        return _build_closing_fallback(deep_dive_items, brief_items)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _call_claude(self, prompt, title_hint=""):
        """调用 Claude，最多重试 3 次。成功返回文本，失败返回 None。"""
        max_retries = 3
        for attempt in range(max_retries):
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
                        "max_tokens": 400,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    text = response.json().get("content", [{}])[0].get("text", "").strip()
                    _log.info(f"[insight] Claude 成功 (attempt {attempt+1}) | title={title_hint[:40]}")
                    return text

                _log.warning(
                    f"[insight] Claude HTTP {response.status_code} (attempt {attempt+1}) "
                    f"| title={title_hint[:40]} | body={response.text[:120]}"
                )

            except Exception as e:
                _log.warning(
                    f"[insight] Claude 异常 (attempt {attempt+1}): {e} | title={title_hint[:40]}"
                )

            if attempt < max_retries - 1:
                wait = 2 * (attempt + 1)
                _log.debug(f"[insight] 等待 {wait}s 后重试 Claude...")
                time.sleep(wait)

        return None  # 全部失败

    def _call_openai(self, prompt, title_hint=""):
        """调用 OpenAI，单次尝试。成功返回文本，失败返回 None。"""
        if not self.openai_api_key:
            _log.error("[insight] OpenAI API key 未配置，无法 fallback")
            return None
        try:
            response = requests.post(
                self.openai_api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}",
                },
                json={
                    "model": self.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0.4,
                },
                timeout=30,
            )

            if response.status_code == 200:
                text = (
                    response.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                _log.info(
                    f"[insight] OpenAI fallback 成功 | title={title_hint[:40]}"
                )
                return text

            _log.error(
                f"[insight] OpenAI HTTP {response.status_code} | title={title_hint[:40]} "
                f"| body={response.text[:120]}"
            )
        except Exception as e:
            _log.error(f"[insight] OpenAI 异常: {e} | title={title_hint[:40]}")

        return None  # fallback 也失败

    def _build_prompt(self, chinese_title, chinese_summary, final_score=7):
        # Insight 强度控制：高分用完整分析结构，中分用简洁 1 句话
        if final_score >= 8:
            intensity_rules = (
                "【Insight 强度：高（完整分析结构，必须 2 句话）】\n"
                "本条新闻重要性高，Insight 必须：\n"
                "- 严格输出 2 句话，不能只有 1 句，不能超过 3 句\n"
                "- 第1句：这个动作对行业格局意味着什么（结构性变化 / 竞争重塑 / 新赛道形成）\n"
                "- 第2句：未来 6~12 个月最值得关注的信号（哪家公司的反应 / 哪个指标 / 哪个时间节点）\n"
                "- 使用完整判断结构（分水岭 / 决策转折 / 预判方向）\n"
                "- 明确指出赢家/输家或行业拐点\n"
                "- 优先使用以下结构：\n"
                "  · 「真正的分水岭在于…」\n"
                "  · 「关键不在于…而在于…」\n"
                "  · 「这不只是…而是…」\n\n"
                "风格示例（只参考语气结构）：\n"
                "- 「真正的分水岭在于：谁能先把模型能力转化成企业愿意持续付费的产品——Anthropic 现在领先了一步。接下来最值得观察的是 OpenAI 的企业定价反应，以及 6 个月内哪家的续费率先走高。」\n"
                "- 「关键不在于这个功能本身，而在于 OpenAI 正在把定价权从竞争对手手里拿走。如果 Google 不在年底前推出对等能力，其企业客户的流失速度将超出预期。」"
            )
        else:
            intensity_rules = (
                "【Insight 强度：中（简洁直接，1 句话）】\n"
                "本条新闻属于中等重要，Insight 必须：\n"
                "- 控制在 1 句话内\n"
                "- 直接给方向性结论，不需要完整分析框架\n"
                "- 语气仍然是 VC 视角，但更简练\n"
                "- 优先使用：\n"
                "  · 「接下来更值得关注的是…」\n"
                "  · 「这意味着…正在加速」\n"
                "  · 直接点出 1 个关键变量\n\n"
                "【避免】：过度展开，1 句话说完即止"
            )

        return f"""你是一位 AI 行业首席分析师，为机构投资人和产品决策者撰写市场判断，风格参考 Bloomberg Intelligence / The Information。

新闻标题：{chinese_title}
新闻摘要：{chinese_summary}

{intensity_rules}

【通用强制规则】：
- 不允许复述新闻内容，直接给结论
- 必须是「结论句」，而不是「解释句」
- 必须隐含投资人或产品决策者视角：
  · 如果你是投资人：这改变了你对哪个赛道的判断？
  · 如果你是产品负责人：这意味着你需要做什么决策？
- 语气：资深 VC 合伙人内部简报，不是学生作业

请直接输出 insight，不加标题，不加项目符号，不加引号。"""
