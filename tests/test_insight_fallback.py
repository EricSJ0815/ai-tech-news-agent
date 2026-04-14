"""
Test: InsightAgent fallback stability
Covers three scenarios:
  1. Claude succeeds normally
  2. Claude fails → OpenAI fallback succeeds
  3. Both Claude and OpenAI fail → graceful degradation
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Make sure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.insight_agent import InsightAgent, _DEGRADED_INSIGHT

SAMPLE_TITLE = "OpenAI 正把 AI 工具从效率插件重塑为可分层定价的基础设施"
SAMPLE_SUMMARY = "OpenAI 宣布新一轮企业定价策略调整，将 ChatGPT 企业版拆分为三个计费层。"
FINAL_SCORE = 8


def _ok_claude_response():
    """Simulate a successful Claude HTTP 200 response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "content": [{"text": "真正的分水岭在于：OpenAI 率先固化企业定价体系。"}]
    }
    return mock


def _fail_claude_response():
    """Simulate Claude 529 overloaded."""
    mock = MagicMock()
    mock.status_code = 529
    mock.text = '{"error":{"type":"overloaded_error","message":"API overloaded"}}'
    return mock


def _ok_openai_response():
    """Simulate a successful OpenAI HTTP 200 response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [{"message": {"content": "OpenAI fallback insight 文本。"}}]
    }
    return mock


def _fail_openai_response():
    """Simulate OpenAI 500 error."""
    mock = MagicMock()
    mock.status_code = 500
    mock.text = '{"error":"Internal Server Error"}'
    return mock


class TestInsightFallback(unittest.TestCase):

    # ── Scenario 1: Claude 正常成功 ─────────────────────────────────────
    @patch("src.agents.insight_agent.time.sleep", return_value=None)
    @patch("src.agents.insight_agent.requests.post")
    def test_1_claude_success(self, mock_post, _mock_sleep):
        """Claude 正常返回 → 使用 Claude 结果，不触发 fallback。"""
        mock_post.return_value = _ok_claude_response()

        agent = InsightAgent()
        result = agent.generate_insight(SAMPLE_TITLE, SAMPLE_SUMMARY, FINAL_SCORE)

        self.assertIsNotNone(result)
        self.assertNotEqual(result, _DEGRADED_INSIGHT)
        self.assertIn("OpenAI", result)  # our mock text contains "OpenAI"
        # Claude should have been called exactly once
        self.assertEqual(mock_post.call_count, 1)
        print(f"\n[PASS] Scenario 1 — Claude success: {result[:60]}")

    # ── Scenario 2: Claude 失败 → OpenAI fallback 成功 ──────────────────
    @patch("src.agents.insight_agent.time.sleep", return_value=None)
    @patch("src.agents.insight_agent.requests.post")
    def test_2_claude_fail_openai_success(self, mock_post, _mock_sleep):
        """Claude 3 次全部 529 → OpenAI fallback 成功 → 日报正常生成。"""
        # First 3 calls = Claude failures, 4th call = OpenAI success
        mock_post.side_effect = [
            _fail_claude_response(),
            _fail_claude_response(),
            _fail_claude_response(),
            _ok_openai_response(),
        ]

        agent = InsightAgent()
        result = agent.generate_insight(SAMPLE_TITLE, SAMPLE_SUMMARY, FINAL_SCORE)

        self.assertIsNotNone(result)
        self.assertNotEqual(result, _DEGRADED_INSIGHT)
        self.assertIn("fallback", result)  # our mock OpenAI text contains "fallback"
        # Claude tried 3 times, then OpenAI once
        self.assertEqual(mock_post.call_count, 4)
        print(f"\n[PASS] Scenario 2 — Claude fail, OpenAI fallback: {result[:60]}")

    # ── Scenario 3: Claude 和 OpenAI 都失败 → 降级文案 ──────────────────
    @patch("src.agents.insight_agent.time.sleep", return_value=None)
    @patch("src.agents.insight_agent.requests.post")
    def test_3_both_fail_graceful_degradation(self, mock_post, _mock_sleep):
        """Claude 3 次失败 + OpenAI 失败 → 返回降级文案，不抛异常，不显示报错。"""
        mock_post.side_effect = [
            _fail_claude_response(),
            _fail_claude_response(),
            _fail_claude_response(),
            _fail_openai_response(),
        ]

        agent = InsightAgent()
        result = agent.generate_insight(SAMPLE_TITLE, SAMPLE_SUMMARY, FINAL_SCORE)

        # Must return degraded text (not an exception, not empty, not raw error)
        self.assertEqual(result, _DEGRADED_INSIGHT)
        self.assertNotIn("失败", result[:5])  # must not START with "失败"
        self.assertNotIn("error", result.lower())
        self.assertNotIn("Error", result)
        print(f"\n[PASS] Scenario 3 — Both fail, degraded: {result[:80]}")

    # ── Extra: pipeline 集成 — generate_insight 永不抛异常 ───────────────
    @patch("src.agents.insight_agent.time.sleep", return_value=None)
    @patch("src.agents.insight_agent.requests.post", side_effect=Exception("network down"))
    def test_4_exception_never_propagates(self, _mock_post, _mock_sleep):
        """即使底层抛出网络异常，generate_insight 也必须返回字符串，不能抛出。"""
        agent = InsightAgent()
        try:
            result = agent.generate_insight(SAMPLE_TITLE, SAMPLE_SUMMARY, FINAL_SCORE)
        except Exception as e:
            self.fail(f"generate_insight 不应该抛出异常，但抛出了: {e}")

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        print(f"\n[PASS] Scenario 4 — Network exception → degraded: {result[:60]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
