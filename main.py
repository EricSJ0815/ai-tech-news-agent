import json
import os
from collections import Counter
from datetime import datetime, timezone
from src.agents.summarize_agent import SummarizeAgent
from src.agents.insight_agent import InsightAgent
from src.pipeline.filter_articles import filter_articles
from src.pipeline.dedupe_articles import dedupe_articles
from src.pipeline.score_articles import ScoreAgent
from src.utils.logger import get_logger

_log = get_logger()


# ── Freshness filter ───────────────────────────────────────────────────

def _apply_freshness_rules(articles):
    """
    Apply time-freshness rules after scoring.

    Rules:
      - deep_dive : hard cutoff at 72 h (3 days). Older → downgraded to brief.
      - brief     : soft cutoff at 48 h (log warn), hard cutoff at 72 h (drop).

    Articles whose `published` field cannot be parsed pass through unchanged
    (no date = treat as fresh to avoid silently dropping content).

    Safety fallback: if applying the hard 72 h rule leaves zero brief articles,
    relax to 120 h and log a warning (handles static / slow RSS feeds).
    """
    try:
        from dateutil import parser as dp
    except ImportError:
        _log.warning("[freshness] dateutil not installed; skipping freshness filter")
        return articles

    DEEP_DIVE_MAX_H = 72
    BRIEF_SOFT_MAX_H = 48
    BRIEF_HARD_MAX_H = 72
    BRIEF_FALLBACK_MAX_H = 120   # used only when zero briefs survive

    now = datetime.now(timezone.utc)

    # Step 1: annotate age
    for a in articles:
        pub = a.get("published", "")
        try:
            dt = dp.parse(pub).astimezone(timezone.utc)
            a["age_hours"] = (now - dt).total_seconds() / 3600
        except Exception:
            a["age_hours"] = None

    # Step 2: apply rules
    kept = []
    for a in articles:
        age = a.get("age_hours")
        decision = a.get("scoring", {}).get("decision", {})
        dtype = decision.get("type", "brief")

        if age is None:
            kept.append(a)
            continue

        if dtype == "deep_dive":
            if age > DEEP_DIVE_MAX_H:
                decision["type"] = "brief"
                _log.warning(
                    f"[freshness] deep_dive→brief (age={round(age)}h): {a.get('title','')[:55]}"
                )
                dtype = "brief"   # fall through to brief check
            else:
                kept.append(a)
                continue

        # dtype == "brief" at this point
        if age > BRIEF_HARD_MAX_H:
            _log.warning(
                f"[freshness] brief 丢弃 (age={round(age)}h): {a.get('title','')[:55]}"
            )
        else:
            if age > BRIEF_SOFT_MAX_H:
                _log.info(
                    f"[freshness] brief 超48h保留 (age={round(age)}h): {a.get('title','')[:55]}"
                )
            kept.append(a)

    # Step 3: safety fallback
    brief_count = sum(
        1 for a in kept
        if a.get("scoring", {}).get("decision", {}).get("type") == "brief"
    )
    if brief_count == 0:
        _log.warning(
            "[freshness] 无符合72h时效的 Brief，放宽至120h（RSS 更新慢或使用静态测试数据）"
        )
        for a in articles:
            age = a.get("age_hours")
            dtype = a.get("scoring", {}).get("decision", {}).get("type", "brief")
            if dtype == "brief" and a not in kept and (age is None or age <= BRIEF_FALLBACK_MAX_H):
                kept.append(a)

    return kept


# ── Market pulse / closing note 模板（基于 tag 主题匹配） ──────────────

_PULSE_RULES = [
    # 结构：① 今天最重要的变化是什么 ② 为什么重要 / 影响什么 ③（可选）接下来更值得关注什么
    ({"pricing", "定价", "subscription", "付费", "commercialization", "商业化", "revenue"},
     "今天最重要的变化不在模型能力，而在 AI 商业化定价策略的分化开始实质性加速。"
     "不同路线的定价逻辑正在分叉——谁能率先把价格体系固化为客户的默认选项，将决定下一阶段市场份额的争夺结果。"
     "接下来最值得关注的是：头部公司的报价模式是否向企业客户侧倾斜，以及哪家的续费率先出现结构性拐点。"),
    ({"regulation", "监管", "safety", "安全", "policy", "政策", "compliance"},
     "今天的主线是监管与安全议题同步升温，行业正进入新一轮合规压力窗口期。"
     "监管收紧的速度已超过大多数公司的产品架构调整节奏——合规成本将在未来 6 个月内成为实质性的竞争变量。"
     "接下来更值得关注的是：谁会在监管文件落地前完成技术层的预埋，而不只是做公关层面的响应。"),
    ({"chip", "芯片", "nvidia", "hardware", "算力", "gpu", "infra"},
     "今天的核心信号来自算力基础设施层，供应链与算力入口的争夺正在进入新的激烈阶段。"
     "算力竞争的决胜点已不只是硬件产能——谁能把成本优势转化成推理侧的定价权，才是下一阶段护城河的真正来源。"
     "值得持续追踪的是：独立算力提供商能否在 NVIDIA 主导的格局中打开足够的价格差异空间。"),
    ({"funding", "融资", "investment", "vc", "投资", "raise"},
     "今天资本的信号比较清晰：AI 赛道的押注节奏仍在提速，而且方向在向应用层集中。"
     "这一轮融资浪潮的结构变化在于：钱不再只进模型层，企业工作流和垂直场景正成为新的投资锚点。"
     "接下来更值得关注的不是谁拿到了钱，而是哪批公司率先跑通企业付费闭环——那才是下一轮估值重估的真实触发器。"),
    ({"agent", "llm", "reasoning", "model", "模型", "benchmark"},
     "今天的重点在模型能力层的持续演进，但真正的分水岭已不在 benchmark，而在应用落地速度。"
     "模型层的差距正在收窄，谁能率先把通用能力包装成用户愿意持续付费的产品，将成为下一阶段的核心竞争点。"
     "接下来更值得观察的是：哪个应用层玩家正在把模型能力转化为真实的用户留存指标。"),
    ({"openai", "anthropic", "google", "microsoft", "meta", "competition", "竞争"},
     "今天头部 AI 公司的动作在同步密集，这轮博弈已不只是产品比拼，而是市场入口和分发渠道的提前占位。"
     "头部公司正在拉开与中游的距离——资源集中效应叠加产品整合，将让竞争格局在未来两个季度内加速固化。"
     "接下来更值得追踪的是：头部之外，哪家公司有能力在细分场景建立足够深的护城河，而不是被整合进更大的生态。"),
]

_CLOSING_RULES = [
    # 结构：核心趋势（1句）| 关键变化（1–2条，• 开头）| 对你的影响（1–2条，→ 开头）
    ({"pricing", "定价", "subscription", "付费", "commercialization", "商业化"},
     "核心趋势：AI 商业化正在从「功能定价」转向「价值定价」，定价权争夺已成为新的主战场。\n"
     "• 关键变化：头部公司开始对企业客户推行分层报价，低价通道正在系统性关闭；订阅模式向使用量挂钩转移。\n"
     "→ 对你的影响：如果你在评估 AI 工具采购，现在锁定年度合同比未来按量付费更划算；如果你在做产品，定价模型的选择将直接影响你能否进入企业采购清单。"),
    ({"regulation", "监管", "safety", "安全", "policy", "政策", "compliance"},
     "核心趋势：AI 监管的重心正在从「数据合规」转向「模型行为问责」，合规压力正在系统化。\n"
     "• 关键变化：监管机构开始要求模型透明度而非仅要求数据透明度；企业 AI 部署的法律风险窗口正在收窄。\n"
     "→ 对你的影响：如果你在部署 AI 产品，现在需要提前做模型行为审计，而不是等监管落地再应对；合规能力正在成为企业客户采购 AI 的新门槛。"),
    ({"chip", "芯片", "nvidia", "hardware", "算力", "gpu", "infra"},
     "核心趋势：算力竞争正在从「堆硬件」转向「推理效率」，谁能降低单次推理成本谁就掌握定价主动权。\n"
     "• 关键变化：新一代推理芯片开始在性价比上挑战 GPU 垄断；云厂商正在加速自研算力以减少对 NVIDIA 的依赖。\n"
     "→ 对你的影响：如果你在做 AI 应用，推理成本将在未来 12 个月内下降，现在绑定高价算力合同需要重新评估；如果你在投资算力赛道，关注推理侧而非训练侧的新入局者。"),
    ({"funding", "融资", "investment", "vc", "投资", "raise"},
     "核心趋势：AI 投资的重心正在从「模型层」向「应用层」转移，资本开始追逐可验证的商业回报而非技术潜力。\n"
     "• 关键变化：大额融资开始集中在有明确企业客户和 ARR 的公司；纯技术故事的估值倍数正在压缩。\n"
     "→ 对你的影响：如果你在融资，现在讲「我有付费客户」比「我有更好的模型」更有说服力；如果你在做企业 AI，现在是拿下标杆客户、建立收入证明的最关键窗口。"),
    ({"openai", "anthropic", "google", "microsoft", "meta", "competition", "竞争"},
     "核心趋势：头部 AI 公司的竞争已从「模型能力比拼」转向「生态锁定」，谁先完成工作流绑定谁就赢得下一个周期。\n"
     "• 关键变化：头部公司正在通过 API 定价、插件生态、企业集成三条路线同时圈地；中间层的独立 AI 工具正在被整合压力挤压。\n"
     "→ 对你的影响：如果你在做独立 AI 工具，现在需要找到头部平台无法覆盖的垂直场景，而不是做通用功能的优化版；如果你在部署 AI，选择平台时要考虑被锁定的长期成本。"),
    ({"agent", "llm", "reasoning", "model", "模型", "benchmark"},
     "核心趋势：模型能力的同质化正在加速，竞争重心正在从「谁的模型更强」转向「谁能先把模型能力转化成用户留存」。\n"
     "• 关键变化：benchmark 分数的市场影响力正在下降；用户真正愿意付费的是「解决我具体问题」的产品，而不是「通用能力最强」的模型。\n"
     "→ 对你的影响：如果你在做 AI 产品，现在投入到垂直场景的深度定制比追通用模型能力更有回报；如果你在选 AI 工具，开始用「它能否解决我的具体场景」而不是「它的模型评分」来做决策。"),
]


def _match_editorial(rules, tag_set, fallback):
    for keywords, text in rules:
        if keywords & tag_set:
            return text
    return fallback


def _build_closing_note(deep_dive_items, brief_items, tag_set, insight_agent=None):
    """
    今日结论：优先用 AI 生成（4–6 句，有主线 + 关键变化 + 收束判断）。
    AI 失败时退化到模板。
    """
    if insight_agent is not None:
        return insight_agent.generate_closing_note(deep_dive_items, brief_items)

    # ── 模板降级 ────────────────────────────────────────────────────────
    _CLOSING_FALLBACK_TEXT = (
        "今天的信号指向 AI 行业从「能力比拼」转向「商业兑现」。\n"
        "• 关键变化：市场评估 AI 的标准在从「能力」转向「留存率和续费数据」。"
    )
    matched = _match_editorial(_CLOSING_RULES, tag_set, fallback=_CLOSING_FALLBACK_TEXT)
    template_lines = [l.strip() for l in matched.split("\n") if l.strip()]
    trend_line = template_lines[0] if template_lines else "核心趋势：AI 行业格局持续演进。"

    key_changes = []
    for item in deep_dive_items[:2]:
        title = (item.get("angle_title") or item.get("chinese_title", "")).strip()
        if title:
            key_changes.append(f"• {title}")
    if not key_changes:
        for item in brief_items[:1]:
            title = (item.get("angle_title") or item.get("chinese_title", "")).strip()
            if title:
                key_changes.append(f"• {title}")

    return "\n".join([trend_line] + key_changes)


def _top_tag_set(items, n=5):
    all_tags = []
    for item in items:
        all_tags.extend(item.get("tags", []))
    return set(t.lower() for t, _ in Counter(all_tags).most_common(n))


# ── Report builder ─────────────────────────────────────────────────────

def build_report_object(summarized, scoring_map, insight_agent=None):
    """
    组装结构化 report object。
    scoring_map: { article["title"]: article["scoring"] }
    insight_agent: 传入后用于 AI 生成今日结论；None 则退化为模板。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    deep_dive_items = []
    brief_items = []

    for item in summarized:
        scoring = scoring_map.get(item.get("original_title", ""), {})
        decision_type = scoring.get("decision", {}).get("type", "brief")
        final_score = scoring.get("final_score", 0)
        tags = scoring.get("tags", [])
        reason_summary = scoring.get("reasoning", {}).get("summary", "")

        if decision_type == "deep_dive":
            deep_dive_items.append({
                "essence": item.get("essence", ""),
                "angle_title": item.get("angle_title", "") or item.get("chinese_title", ""),
                "why_it_matters": item.get("why_it_matters", ""),
                "chinese_title": item.get("chinese_title", ""),
                "original_title": item.get("original_title", ""),
                "source": item.get("source", ""),
                "link": item.get("link", ""),
                "final_score": final_score,
                "tags": tags,
                "reason_summary": reason_summary,
                "chinese_summary": item.get("chinese_summary", ""),
                "key_points": item.get("key_points", []),
                "ai_insight": item.get("ai_insight", ""),
            })
        else:
            brief_items.append({
                "angle_title": item.get("angle_title", "") or item.get("chinese_title", ""),
                "chinese_title": item.get("chinese_title", ""),
                "final_score": final_score,
                "tags": tags,
                "chinese_summary": item.get("chinese_summary", ""),
                "why_it_matters": item.get("why_it_matters", ""),
                "source": item.get("source", ""),
                "link": item.get("link", ""),
            })

    deep_dive_items.sort(key=lambda x: x["final_score"], reverse=True)
    brief_items.sort(key=lambda x: x["final_score"], reverse=True)

    tag_set = _top_tag_set(deep_dive_items + brief_items)

    market_pulse = _match_editorial(
        _PULSE_RULES, tag_set,
        fallback="今天没有单一主线，但多个信号同时指向同一个方向：AI 商业化正在进入以客户留存为核心的新阶段，而不是以功能堆叠为主的早期竞争。接下来最值得关注的是：哪家公司的产品数据开始出现用户黏性的结构性拐点。"
    )
    closing_note = _build_closing_note(deep_dive_items, brief_items, tag_set, insight_agent)

    return {
        "report_meta": {
            "date": today,
            "total_articles": len(summarized),
            "deep_dive_count": len(deep_dive_items),
            "brief_count": len(brief_items),
            "market_pulse": market_pulse,
            "closing_note": closing_note,
        },
        "deep_dive": deep_dive_items,
        "brief": brief_items,
    }


# ── Markdown renderer ──────────────────────────────────────────────────

def generate_markdown_report(report):
    meta = report["report_meta"]
    deep_dive = report["deep_dive"]
    brief = report["brief"]

    lines = []

    # ── Header ──────────────────────────────────────────────────────────
    lines.append(f"# AI Tech Daily — {meta['date']}\n")
    lines.append(f"> {meta['market_pulse']}\n")
    lines.append(
        f"*Deep Dive {meta['deep_dive_count']} · Brief {meta['brief_count']} · "
        f"共 {meta['total_articles']} 篇*\n"
    )
    lines.append("---\n")

    # ── 今日最重要的 N 件事 ─────────────────────────────────────────────
    # Top 3 是"强信号层"：一眼抓住今天发生了什么
    # 标题用 angle_title，补充 why_it_matters 第一句作为行业判断锚点
    top_items = (deep_dive + brief)[:3]
    if top_items:
        lines.append("## 🔥 今日最值得关注的事\n")
        for i, item in enumerate(top_items, 1):
            title = item["angle_title"] or item.get("chinese_title", "")
            score = item["final_score"]
            lines.append(f"{i}. **{title}** *({score})*")
            # 补充 why_it_matters 第一句作为行业判断信号（仅 deep_dive 有此字段）
            why = item.get("why_it_matters", "")
            if why:
                first_sentence = why.split("。")[0] + "。" if "。" in why else why
                lines.append(f"   > {first_sentence}")
        lines.append("")
        lines.append("---\n")

    # ── Deep Dive ────────────────────────────────────────────────────────
    if deep_dive:
        lines.append("## 🧠 Deep Dive\n")
        for i, item in enumerate(deep_dive, 1):
            # 标题：用 angle_title
            lines.append(f"### {i}. {item['angle_title']}\n")

            # meta 行：score + tags
            tag_str = " ".join(f"`{t}`" for t in item["tags"]) if item["tags"] else ""
            meta_line = f"**{item['final_score']}/10**"
            if tag_str:
                meta_line += f"　{tag_str}"
            lines.append(meta_line + "\n")

            # 原标题 + 来源
            lines.append(f"*{item['original_title']}*　[{item['source']}]({item['link']})\n")

            # Why it matters
            if item["why_it_matters"]:
                lines.append(f"**Why it matters：** {item['why_it_matters']}\n")

            # 摘要
            lines.append(f"**摘要：** {item['chinese_summary']}\n")

            # 要点
            if item["key_points"]:
                for point in item["key_points"]:
                    lines.append(f"- {point}")
                lines.append("")

            # AI Insight
            if item["ai_insight"]:
                lines.append(f"💡 *{item['ai_insight']}*\n")

            lines.append("---\n")

    # ── 今日其他信号 ─────────────────────────────────────────────────────
    # 过滤掉已出现在 Top Signals 的条目，避免重复
    top_titles = {(i.get("angle_title") or i.get("chinese_title", "")) for i in top_items}
    brief_extra = [i for i in brief
                   if (i.get("angle_title") or i.get("chinese_title", "")) not in top_titles]

    if brief_extra:
        lines.append("## 📡 今日其他信号\n")
        for item in brief_extra[:15]:
            tag_str = " ".join(f"`{t}`" for t in item["tags"]) if item["tags"] else ""
            title = (item.get("angle_title") or item.get("chinese_title", "")).strip()
            # 第2句：取 summary 第一句作为补充说明
            raw_summary = item.get("chinese_summary", "")
            first_sent = raw_summary.split("。")[0] + "。" if "。" in raw_summary else raw_summary
            line = f"- **{title}**"
            if first_sent:
                line += f"　{first_sent}"
            if tag_str:
                line += f"　{tag_str}"
            lines.append(line)
        lines.append("")
        lines.append("---\n")

    # ── Closing Note ─────────────────────────────────────────────────────
    lines.append("## 💡 今日结论\n")
    lines.append(f"> {meta['closing_note']}\n")

    return "\n".join(lines)


# ── Pipeline (reusable entry point) ───────────────────────────────────

def run_pipeline(data_path="data/rss_articles.json", progress_cb=None, articles=None):
    """
    Execute full pipeline and return (report_object, markdown_content).

    articles: pre-fetched article list (e.g. from ingest_all()).
              When provided, data_path is ignored.
    progress_cb: optional callable(message: str) for progress updates.
    """
    def _step(msg):
        print(msg)
        if progress_cb:
            progress_cb(msg)

    _step("Step 1: 加载数据...")
    if articles is not None:
        _step(f"使用传入数据，共 {len(articles)} 条新闻")
    else:
        with open(data_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        _step(f"已加载 {len(articles)} 条新闻")

    articles = filter_articles(articles)
    _step(f"筛选后保留 {len(articles)} 条")

    articles = dedupe_articles(articles)
    _step(f"去重后剩余 {len(articles)} 条")

    _step("Step 1.5: 对新闻打分...")
    score_agent = ScoreAgent()
    for article in articles:
        score_result = score_agent.score_article(article)
        article["scoring"] = score_result["scoring"]
        article["importance_score"] = score_result["importance_score"]
        article["category"] = score_result["category"]
        article["score_reason"] = score_result["reason"]

    articles = sorted(articles, key=lambda x: x.get("importance_score", 0), reverse=True)
    articles = [a for a in articles if a.get("scoring", {}).get("decision", {}).get("type") != "drop"]

    _step("Step 1.6: 应用时效规则（Deep Dive ≤72h，Brief ≤72h）...")
    articles = _apply_freshness_rules(articles)

    # 按 decision type 分桶，分别限制上限，避免 brief 被高分 deep_dive 全部挤掉
    deep_dive_pool = [a for a in articles if a.get("scoring", {}).get("decision", {}).get("type") == "deep_dive"]
    brief_pool     = [a for a in articles if a.get("scoring", {}).get("decision", {}).get("type") == "brief"]
    articles = deep_dive_pool[:5] + brief_pool[:12]
    _step(f"选出 {len(articles)} 条（deep_dive: {len(deep_dive_pool[:5])}, brief: {len(brief_pool[:12])}）")

    decision_map = {
        a["title"]: a.get("scoring", {}).get("decision", {}).get("type", "brief")
        for a in articles
    }
    scoring_map = {a["title"]: a.get("scoring", {}) for a in articles}

    _step("Step 2: 生成中文摘要...")
    summarize_agent = SummarizeAgent()
    summarized = summarize_agent.summarize_articles(articles)

    _step("Step 3: 生成 AI Insight...")
    insight_agent = InsightAgent()
    for item in summarized:
        original_title = item.get("original_title", "")
        decision_type = decision_map.get(original_title, "brief")
        if decision_type == "deep_dive":
            final_score = scoring_map.get(original_title, {}).get("final_score", 7)
            item["ai_insight"] = insight_agent.generate_insight(
                item["chinese_title"],
                item["chinese_summary"],
                final_score=final_score,
                link=item.get("link", ""),
                source=item.get("source", ""),
            )
        else:
            item["ai_insight"] = ""

    _step("Step 4: 组装报告...")
    report = build_report_object(summarized, scoring_map, insight_agent=insight_agent)
    markdown_content = generate_markdown_report(report)

    # ── Pipeline run summary (logged to file) ─────────────────────────
    try:
        from src.utils.logger import get_logger
        _pipeline_log = get_logger()
        meta = report["report_meta"]
        _pipeline_log.info("[pipeline] RUN SUMMARY:")
        _pipeline_log.info(f"  date         : {meta['date']}")
        _pipeline_log.info(f"  deep_dive    : {meta['deep_dive_count']}")
        _pipeline_log.info(f"  brief        : {meta['brief_count']}")
        _pipeline_log.info(f"  total_articles: {meta['total_articles']}")
        _pipeline_log.info(f"  market_pulse : {meta['market_pulse'][:60]}...")
    except Exception:
        pass  # summary logging is non-critical

    return report, markdown_content


# ── Main ───────────────────────────────────────────────────────────────

def main():
    print("=== AI Tech News Intelligence Agent ===\n")
    report, markdown_content = run_pipeline()

    os.makedirs("output", exist_ok=True)
    file_path = "output/daily_report.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    json_path = "output/last_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"report": report, "markdown": markdown_content}, f, ensure_ascii=False, indent=2)
    print("✅ 日报已生成：", file_path)


if __name__ == "__main__":
    main()
