"""
AI科技日报 — Streamlit Product Demo
"""
import json
import os
import re
from pathlib import Path

import streamlit as st

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI科技日报",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: #111318;
}
[data-testid="stMain"] {
    background: #111318;
}
section[data-testid="stSidebar"] {
    background: #111318;
}

/* ── Header ── */
.aitd-header {
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #1e2130;
    margin-bottom: 2rem;
}
.aitd-product-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6c8ebf;
    background: #1a2035;
    border: 1px solid #2a3555;
    border-radius: 4px;
    padding: 3px 10px;
    margin-bottom: 0.75rem;
}
.aitd-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #f0f4ff;
    letter-spacing: -0.02em;
    margin: 0 0 0.3rem 0;
    line-height: 1.1;
}
.aitd-subtitle {
    font-size: 1rem;
    color: #6b7280;
    margin: 0 0 1rem 0;
}
.aitd-meta-bar {
    display: flex;
    gap: 1.2rem;
    align-items: center;
    flex-wrap: wrap;
}
.aitd-meta-chip {
    font-size: 0.78rem;
    color: #9ca3af;
    background: #1a1d29;
    border: 1px solid #272b3a;
    border-radius: 20px;
    padding: 3px 12px;
}
.aitd-meta-chip.live {
    color: #34d399;
    border-color: #065f46;
    background: #022c22;
}
.aitd-meta-chip.demo {
    color: #fbbf24;
    border-color: #78350f;
    background: #1c1000;
}

/* ── Market Pulse ── */
.aitd-pulse-card {
    background: linear-gradient(135deg, #0d1b3e 0%, #0a1628 100%);
    border: 1px solid #243358;
    border-left: 3px solid #5b8def;
    border-radius: 8px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 2rem;
}
.aitd-pulse-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #7baaf7;
    margin-bottom: 0.7rem;
}
.aitd-pulse-text {
    font-size: 1.05rem;
    color: #c0d0ee;
    line-height: 1.75;
    margin: 0;
    font-weight: 400;
}

/* ── Section headers ── */
.aitd-section-header {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4b5563;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2130;
}

/* ── Top Signal Cards ── */
.aitd-top-card {
    background: #13161f;
    border: 1px solid #1e2233;
    border-radius: 8px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.75rem;
    position: relative;
}
.aitd-top-card:hover {
    border-color: #2a3555;
}
.aitd-rank-badge {
    display: inline-block;
    width: 22px;
    height: 22px;
    line-height: 22px;
    text-align: center;
    font-size: 0.72rem;
    font-weight: 800;
    color: #0f1117;
    background: #5b8def;
    border-radius: 50%;
    margin-right: 0.6rem;
    vertical-align: middle;
}
.aitd-top-title {
    font-size: 1rem;
    font-weight: 700;
    color: #e8edf8;
    line-height: 1.4;
    display: inline;
    vertical-align: middle;
}
.aitd-score-badge {
    float: right;
    font-size: 0.75rem;
    font-weight: 700;
    color: #7baaf7;
    background: #0d1b3e;
    border: 1px solid #243358;
    border-radius: 4px;
    padding: 2px 8px;
    margin-left: 0.5rem;
}
.aitd-why-snippet {
    font-size: 0.87rem;
    color: #8b95aa;
    margin-top: 0.65rem;
    line-height: 1.7;
    border-left: 2px solid #243358;
    padding-left: 0.75rem;
}
.aitd-tags {
    margin-top: 0.7rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
}
.aitd-tag {
    font-size: 0.68rem;
    color: #6b7280;
    background: #1a1d29;
    border: 1px solid #272b3a;
    border-radius: 3px;
    padding: 1px 7px;
}

/* ── Deep Dive ── */
.aitd-dive-header {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    margin-bottom: 0.8rem;
}
.aitd-dive-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e8edf8;
    line-height: 1.45;
    flex: 1;
}
.aitd-source-line {
    font-size: 0.8rem;
    color: #4b5563;
    margin-bottom: 0.9rem;
}
.aitd-source-line a {
    color: #7baaf7;
    text-decoration: none;
}
.aitd-why-block {
    background: #0c1520;
    border-left: 2px solid #5b8def;
    border-radius: 0 4px 4px 0;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1rem;
}
.aitd-why-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7baaf7;
    margin-bottom: 0.35rem;
}
.aitd-why-text {
    font-size: 1.08rem;
    color: #9dafc7;
    line-height: 1.85;
    margin: 0;
}
.aitd-summary-text {
    font-size: 1.05rem;
    color: #8b95aa;
    line-height: 1.85;
    margin-bottom: 1rem;
}
.aitd-kp-item {
    font-size: 1rem;
    color: #7b8699;
    padding: 0.3rem 0;
    padding-left: 1rem;
    position: relative;
    line-height: 1.8;
}
.aitd-kp-item::before {
    content: "—";
    position: absolute;
    left: 0;
    color: #374151;
}
.aitd-insight-block {
    background: #0d1a10;
    border: 1px solid #1e3d24;
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin-top: 1.1rem;
}
.aitd-insight-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6ee7a0;
    margin-bottom: 0.4rem;
}
.aitd-insight-text {
    font-size: 1rem;
    color: #8ed9b0;
    line-height: 1.85;
    font-style: italic;
    margin: 0;
}

/* ── Quick Brief info-stream ── */
.aitd-brief-stream {
    margin-top: 0.25rem;
}
.aitd-brief-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    padding: 1.1rem 0;
    border-bottom: 1px solid #141720;
}
.aitd-brief-row:last-child {
    border-bottom: none;
}
.aitd-brief-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #5b8def;
    margin-top: 0.6rem;
    flex-shrink: 0;
}
.aitd-brief-body {
    flex: 1;
    min-width: 0;
}
.aitd-brief-headline {
    display: flex;
    align-items: baseline;
    gap: 0.45rem;
    flex-wrap: wrap;
    margin-bottom: 0.45rem;
}
.aitd-brief-link {
    font-size: 1rem;
    font-weight: 600;
    color: #d1d9f0;
    text-decoration: none;
    line-height: 1.5;
}
.aitd-brief-link:hover {
    color: #b8cef5;
}
.aitd-brief-no-link {
    font-size: 1rem;
    font-weight: 600;
    color: #d1d9f0;
    line-height: 1.5;
}
.aitd-brief-src {
    font-size: 0.73rem;
    color: #4b5563;
    white-space: nowrap;
}
/* Bullet list replacing old summary/why paragraphs */
.aitd-brief-bullets {
    margin: 0;
    padding: 0;
}
.aitd-brief-bullet {
    font-size: 0.97rem;
    color: #8b96aa;
    line-height: 1.8;
    margin: 0.22rem 0 0 0;
    padding-left: 0.1rem;
}
.aitd-brief-bullet-why {
    font-size: 0.95rem;
    color: #6a8bbf;
    line-height: 1.8;
    margin: 0.22rem 0 0 0;
    padding-left: 0.1rem;
}

/* ── Closing Note ── */
.aitd-closing-card {
    background: #0e1118;
    border: 1px solid #1e2130;
    border-top: 2px solid #1e3a6e;
    border-radius: 8px;
    padding: 1.5rem 1.6rem;
    margin-top: 2rem;
    margin-bottom: 1rem;
}
.aitd-closing-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4b5563;
    margin-bottom: 0.7rem;
}
.aitd-closing-text {
    font-size: 1rem;
    color: #8b95aa;
    line-height: 1.7;
    margin: 0;
}

/* ── Generate button ── */
div[data-testid="stButton"] button {
    background: #1d4ed8;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    padding: 0.6rem 1.6rem;
    transition: background 0.15s;
}
div[data-testid="stButton"] button:hover {
    background: #2563eb;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #13161f;
    border: 1px solid #1e2233 !important;
    border-radius: 8px !important;
    margin-bottom: 0.6rem;
}
[data-testid="stExpanderDetails"] {
    background: #13161f;
    border-top: 1px solid #1e2233;
    padding-top: 1rem;
}
/* P1: expander header — more visual weight, easier to scan */
[data-testid="stExpander"] summary {
    background: #16192500 !important;
    padding: 0.75rem 1rem !important;
    border-radius: 8px 8px 0 0 !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary div {
    font-size: 1.02rem !important;
    font-weight: 700 !important;
    color: #dde5f8 !important;
    line-height: 1.45 !important;
}

/* ── Essence (Deep Dive "本质" line) ── */
.aitd-essence {
    font-size: 1.08rem;
    font-weight: 700;
    color: #f5cc6a;
    background: #1c1500;
    border-left: 3px solid #d97706;
    padding: 0.65rem 1.1rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.3rem;
    line-height: 1.75;
    letter-spacing: 0.01em;
}

/* ── Closing note typography ── */
.aitd-closing-summary {
    font-size: 1.08rem;
    font-weight: 600;
    color: #e2e8f8;
    line-height: 1.85;
    margin: 0 0 0.9rem 0;
}
.aitd-closing-bullet {
    font-size: 1rem;
    color: #9ca3af;
    line-height: 1.8;
    margin: 0.3rem 0 0 0.4rem;
    padding-left: 0.3rem;
}
.aitd-closing-judgment {
    font-size: 1.05rem;
    font-weight: 500;
    color: #93b4f0;
    line-height: 1.85;
    margin: 0.9rem 0 0 0;
    font-style: italic;
}

/* ── Divider ── */
hr {
    border-color: #1e2130 !important;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────

def _tags_html(tags):
    if not tags:
        return ""
    chips = "".join(f'<span class="aitd-tag">{t}</span>' for t in tags[:5])
    return f'<div class="aitd-tags">{chips}</div>'


def _normalize_numbered(text: str) -> str:
    """Convert '1. xxx\\n2. yyy' numbered lists to '• xxx\\n• yyy' bullets.
    Also splits multi-sentence prose (by 。) with <br> for readability.
    Returns HTML-safe string."""
    if not text:
        return ""
    # Split on newlines; check for numbered patterns
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
    result = []
    has_numbers = any(re.match(r'^\d+[.)]\s+', l) for l in raw_lines)
    if has_numbers:
        for line in raw_lines:
            line = re.sub(r'^\d+[.)]\s+', '• ', line)
            result.append(line)
        return "<br>".join(result)
    # Plain prose: join sentences with <br> when separated by 。
    full = " ".join(raw_lines)
    sentences = [s.strip() + "。" for s in full.split("。") if s.strip()]
    if len(sentences) > 1:
        return "<br>".join(sentences)
    return full


def _load_cached_report():
    """Load the last saved report object from output/ if it exists."""
    report_json_path = Path("output/last_report.json")
    if report_json_path.exists():
        with open(report_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("report"), data.get("markdown")
    # Fall back to parsing the markdown report for demo mode
    md_path = Path("output/daily_report.md")
    if md_path.exists():
        return None, md_path.read_text(encoding="utf-8")
    return None, None


def _save_report(report, markdown):
    os.makedirs("output", exist_ok=True)
    with open("output/last_report.json", "w", encoding="utf-8") as f:
        json.dump({"report": report, "markdown": markdown}, f, ensure_ascii=False, indent=2)
    with open("output/daily_report.md", "w", encoding="utf-8") as f:
        f.write(markdown)


# ── Render helpers ─────────────────────────────────────────────────────

def render_header(meta, is_live):
    mode_chip = (
        '<span class="aitd-meta-chip live">● 实时生成</span>'
        if is_live else
        '<span class="aitd-meta-chip demo">● 缓存数据</span>'
    )
    st.markdown(f"""
<div class="aitd-header">
  <div class="aitd-product-tag">AI 智能简报</div>
  <h1 class="aitd-title">AI 科技日报</h1>
  <p class="aitd-subtitle">由 AI 驱动的每日科技情报，带有编辑判断</p>
  <div class="aitd-meta-bar">
    <span class="aitd-meta-chip">📅 {meta['date']}</span>
    <span class="aitd-meta-chip">🧠 {meta['deep_dive_count']} 深度解读 · ⚡ {meta['brief_count']} 快讯</span>
    <span class="aitd-meta-chip">📰 精选 {meta['total_articles']} 条新闻</span>
    {mode_chip}
  </div>
</div>
""", unsafe_allow_html=True)


def render_market_pulse(pulse_text):
    st.markdown(f"""
<div class="aitd-pulse-card">
  <div class="aitd-pulse-label">⚡ 今日市场判断</div>
  <p class="aitd-pulse-text">{pulse_text}</p>
</div>
""", unsafe_allow_html=True)


def render_signals_all(items):
    """Unified renderer for ALL signal-level items (top signals + remaining deep dives).
    P0-1: single '🔥 今日重点信号' section, no separate '深度解读' header.
    Items[0] is expanded; all others start collapsed.
    """
    st.markdown('<div class="aitd-section-header">🔥 今日重点信号</div>', unsafe_allow_html=True)
    for i, item in enumerate(items, 1):
        title   = item.get("angle_title") or item.get("chinese_title", "")
        why     = item.get("why_it_matters", "")
        summary = item.get("chinese_summary", "")
        key_points = item.get("key_points", [])
        insight = item.get("ai_insight", "")
        tags    = item.get("tags", [])
        link    = item.get("link", "")
        source  = item.get("source", "")
        orig    = item.get("original_title", "")

        tag_str = ("　" + "　".join(f"#{t}" for t in tags[:3])) if tags else ""
        label   = f"{title}{tag_str}"

        essence = item.get("essence", "")

        with st.expander(label, expanded=(i == 1)):
            # 本质句 — Deep Dive only, rendered first for immediate framing
            if essence:
                st.markdown(
                    f'<div class="aitd-essence">👉 本质：{essence}</div>',
                    unsafe_allow_html=True,
                )

            # 原始英文标题（deep dive only）
            if orig:
                st.markdown(
                    f'<div class="aitd-source-line">{orig}</div>',
                    unsafe_allow_html=True,
                )

            # 为什么重要 — P0-2: normalize numbered / multi-sentence text
            if why:
                why_html = _normalize_numbered(why)
                st.markdown(f"""
<div class="aitd-why-block" style="margin-top:0.5rem">
  <div class="aitd-why-label">为什么重要</div>
  <p class="aitd-why-text">{why_html}</p>
</div>""", unsafe_allow_html=True)

            # 摘要
            if summary:
                st.markdown(
                    f'<p class="aitd-summary-text" style="margin-top:0.9rem">{summary}</p>',
                    unsafe_allow_html=True,
                )

            # 关键信息点
            if key_points:
                kp_html = "".join(f'<div class="aitd-kp-item">{p}</div>' for p in key_points)
                st.markdown(kp_html, unsafe_allow_html=True)

            # AI 洞察
            if insight:
                st.markdown(f"""
<div style="border-left:2px solid #6ee7a0;padding:0.7rem 1.1rem;margin-top:1rem;
            background:#0d1a10;border-radius:0 4px 4px 0;border:1px solid #1e3d24;
            border-left:2px solid #6ee7a0">
  <span style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;
               text-transform:uppercase;color:#6ee7a0">💡 AI 洞察</span>
  <p style="font-size:1rem;color:#8ed9b0;font-style:italic;
            margin:0.35rem 0 0 0;line-height:1.85">{insight}</p>
</div>""", unsafe_allow_html=True)

            # 原文入口
            if link and link != "#":
                source_label = source if source else "原文"
                st.markdown(f"""
<div style="margin-top:1rem;padding-top:0.7rem;border-top:1px solid #1f2937">
  <a href="{link}" target="_blank" rel="noopener noreferrer"
     style="font-size:0.82rem;color:#7baaf7;text-decoration:none;font-weight:500">
    🔗 查看原文 · {source_label} →</a>
</div>""", unsafe_allow_html=True)


def render_quick_brief(brief_items):
    if not brief_items:
        return
    st.markdown('<div class="aitd-section-header">📡 今日其他信号</div>', unsafe_allow_html=True)

    rows_html = ""
    for item in brief_items[:15]:
        title = item.get("angle_title") or item.get("chinese_title", "")
        summary = item.get("chinese_summary", "")
        why = item.get("why_it_matters", "")
        link = item.get("link", "")
        source = item.get("source", "")

        # Title — clickable link if available
        if link and link != "#":
            title_html = f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="aitd-brief-link">{title}</a>'
        else:
            title_html = f'<span class="aitd-brief-no-link">{title}</span>'

        src_html = f'<span class="aitd-brief-src">· {source}</span>' if source else ""

        # Build bullet block:
        # 1. 👉 信号 first (why_it_matters) — scan-priority signal line
        # 2. Fact bullets from chinese_summary sentences below
        signal_html = f'<p class="aitd-brief-bullet-why" style="margin-bottom:0.5rem">{why}</p>' if why else ""
        fact_html = ""
        if summary:
            sentences = [s.strip() + "。" for s in summary.split("。") if s.strip()]
            for sent in sentences:
                fact_html += f'<p class="aitd-brief-bullet">• {sent}</p>'
        bullets_html = signal_html + fact_html

        rows_html += f"""
<div class="aitd-brief-row">
  <span class="aitd-brief-dot"></span>
  <div class="aitd-brief-body">
    <div class="aitd-brief-headline">{title_html}{src_html}</div>
    <div class="aitd-brief-bullets">{bullets_html}</div>
  </div>
</div>"""

    st.markdown(f'<div class="aitd-brief-stream">{rows_html}</div>', unsafe_allow_html=True)


def render_closing_note(note):
    """Render structured closing note:
    - para[0]     → bold summary line (.aitd-closing-summary)
    - para[1..N-2] → bullet points   (.aitd-closing-bullet, prefixed with •)
    - para[-1]    → closing judgment (.aitd-closing-judgment, italic blue)
    Paragraphs are split on blank lines; single-paragraph notes fall back to plain text.
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", note) if p.strip()]
    if not paras:
        st.markdown(f"""
<div class="aitd-closing-card">
  <div class="aitd-closing-label">💡 今日结论</div>
  <p class="aitd-closing-text">{note}</p>
</div>
""", unsafe_allow_html=True)
        return

    parts_html = f'<p class="aitd-closing-summary">{paras[0]}</p>'

    if len(paras) >= 3:
        for para in paras[1:-1]:
            bullet = para if para.startswith("•") else f"• {para}"
            parts_html += f'<p class="aitd-closing-bullet">{bullet}</p>'
        parts_html += f'<p class="aitd-closing-judgment">{paras[-1]}</p>'
    elif len(paras) == 2:
        parts_html += f'<p class="aitd-closing-judgment">{paras[1]}</p>'

    st.markdown(f"""
<div class="aitd-closing-card">
  <div class="aitd-closing-label">💡 今日结论</div>
  {parts_html}
</div>
""", unsafe_allow_html=True)


def render_full_report(report, is_live):
    meta = report["report_meta"]
    deep_dive = report["deep_dive"]
    brief = report["brief"]
    top_items = (deep_dive + brief)[:3]

    # 过滤掉已出现在 Top Signals 的条目，避免重复
    top_titles = {item.get("angle_title") or item.get("chinese_title", "") for item in top_items}
    # Deep dive items not already shown in top signals
    deep_dive_extra = [item for item in deep_dive
                       if (item.get("angle_title") or item.get("chinese_title", "")) not in top_titles]
    brief_extra = [item for item in brief
                   if (item.get("angle_title") or item.get("chinese_title", "")) not in top_titles]

    render_header(meta, is_live)
    render_market_pulse(meta["market_pulse"])
    all_signals = top_items + deep_dive_extra
    if all_signals:
        render_signals_all(all_signals)
    st.markdown("<hr>", unsafe_allow_html=True)
    if brief_extra:
        render_quick_brief(brief_extra)
        st.markdown("<hr>", unsafe_allow_html=True)
    render_closing_note(meta["closing_note"])


# ── Main app ───────────────────────────────────────────────────────────

def main():
    # ── Mode detection ───────────────────────────────────────────────────
    # Admin/operator mode: append ?admin=1 to the URL.
    # Viewer mode (default): no query param — read-only, no pipeline trigger.
    is_admin = st.query_params.get("admin", "") in ("1", "true", "yes")

    # ── Sidebar (admin only) ─────────────────────────────────────────────
    if is_admin:
        with st.sidebar:
            st.markdown("### 运营者设置")
            data_source = st.selectbox(
                "数据来源",
                ["🌐 实时 RSS（多源拉取）", "data/rss_articles.json", "data/sample_articles.json"],
                index=0,
            )
            st.markdown("---")
            st.markdown(
                '<span style="font-size:0.75rem;color:#4b5563">'
                "AI 科技日报 · 运营者模式<br>"
                "Powered by MiniMax + Claude"
                "</span>",
                unsafe_allow_html=True,
            )
    else:
        # Hide sidebar toggle entirely for a clean viewer experience
        st.markdown("""
<style>
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }
</style>""", unsafe_allow_html=True)
        data_source = "🌐 实时 RSS（多源拉取）"  # unused in viewer mode

    # ── Session state ────────────────────────────────────────────────────
    if "report" not in st.session_state:
        st.session_state.report = None
        st.session_state.markdown = None
        st.session_state.is_live = False

    # ── Auto-load cached report on first visit (both modes) ──────────────
    if st.session_state.report is None:
        cached_report, cached_md = _load_cached_report()
        if cached_report:
            st.session_state.report = cached_report
            st.session_state.markdown = cached_md
            st.session_state.is_live = False

    # ── Admin: generate button ────────────────────────────────────────────
    generate_clicked = False
    if is_admin:
        col_btn, col_info = st.columns([2, 8])
        with col_btn:
            generate_clicked = st.button("⚡ 生成今日简报", type="primary", use_container_width=True)
        with col_info:
            st.markdown(
                '<span style="font-size:0.78rem;color:#4b5563;line-height:2.5">'
                "🔧 运营者模式 — 生成后自动保存，内测用户将立即看到最新内容</span>",
                unsafe_allow_html=True,
            )

    # ── Pipeline execution (admin only) ──────────────────────────────────
    if generate_clicked:
        status = st.empty()
        progress = st.progress(0)

        steps = [
            (10, "正在筛选新闻..."),
            (30, "正在评估信号强度..."),
            (55, "正在生成中文摘要..."),
            (80, "正在生成 AI 洞察..."),
            (95, "正在渲染简报..."),
        ]
        step_iter = iter(steps)

        def progress_cb(_msg):
            try:
                pct, label = next(step_iter)
                status.markdown(
                    f'<span style="color:#6b7280;font-size:0.85rem">⏳ {label}</span>',
                    unsafe_allow_html=True,
                )
                progress.progress(pct)
            except StopIteration:
                pass

        try:
            import sys
            _stale = {'main', 'src.agents.insight_agent', 'src.agents.summarize_agent'}
            for _mod in list(sys.modules.keys()):
                if _mod in _stale:
                    del sys.modules[_mod]
            from main import run_pipeline
            if data_source == "🌐 实时 RSS（多源拉取）":
                from src.ingestion.rss_ingestor import ingest_all
                status.markdown(
                    '<span style="color:#6b7280;font-size:0.85rem">⏳ 正在拉取 RSS 源...</span>',
                    unsafe_allow_html=True,
                )
                rss_articles = ingest_all(verbose=False)
                report, markdown = run_pipeline(
                    articles=rss_articles,
                    progress_cb=progress_cb,
                )
            else:
                report, markdown = run_pipeline(
                    data_path=data_source,
                    progress_cb=progress_cb,
                )
            progress.progress(100)
            status.markdown(
                '<span style="color:#34d399;font-size:0.85rem">✓ 简报已生成并保存，内测用户刷新页面即可查看</span>',
                unsafe_allow_html=True,
            )
            _save_report(report, markdown)
            st.session_state.report = report
            st.session_state.markdown = markdown
            st.session_state.is_live = True
        except Exception as e:
            progress.empty()
            status.error(f"流程执行出错：{e}")
            st.stop()

    # ── Render report ─────────────────────────────────────────────────────
    if st.session_state.report:
        render_full_report(st.session_state.report, st.session_state.is_live)

    elif is_admin and not generate_clicked:
        # Admin empty state — no cached report exists yet
        st.markdown("""
<div style="text-align:center;padding:6rem 2rem;color:#374151">
  <div style="font-size:3rem;margin-bottom:1rem">⚡</div>
  <div style="font-size:1.1rem;font-weight:600;color:#6b7280;margin-bottom:0.5rem">
    尚无日报缓存
  </div>
  <div style="font-size:0.9rem;color:#4b5563">
    点击 <strong style="color:#7baaf7">生成今日简报</strong> 运行完整流程，
    生成后自动保存供内测用户查看。
  </div>
</div>
""", unsafe_allow_html=True)

    else:
        # Viewer empty state — no cached report found
        st.markdown("""
<div style="text-align:center;padding:6rem 2rem;color:#374151">
  <div style="font-size:3rem;margin-bottom:1rem">📰</div>
  <div style="font-size:1.1rem;font-weight:600;color:#6b7280;margin-bottom:0.5rem">
    今日简报准备中
  </div>
  <div style="font-size:0.9rem;color:#4b5563">
    最新内容即将发布，请稍后刷新页面。
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
