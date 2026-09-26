from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.book_quality import audit, check_ready, metrics, prepare, triage_errors


class BookQualityPipelineTests(unittest.TestCase):
    def make_fixture(self, *, with_key_terms=True, valid_review=True):
        root = Path(tempfile.mkdtemp(prefix="shelf_quality_test_"))
        (root / "transcript.json").write_text(
            json.dumps(
                {
                    "video_id": "TEST",
                    "title": "测试课",
                    "duration": 120,
                    "segments": [
                        {"start": "00:00:00", "end": "00:00:12", "text": "goto 是一种控制流语句。"},
                        {"start": "00:00:12", "end": "00:00:24", "text": "讲师认为它会影响程序结构，因为直接跳转会切断推理。"},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (root / "transcript.corrected.txt").write_text(
            "[00:00:00] goto 是一种控制流语句。\n"
            "[00:00:12] 讲师认为它会影响程序结构，因为直接跳转会切断推理。\n",
            encoding="utf-8",
        )
        (root / "meta.json").write_text(json.dumps({"duration": 120}), encoding="utf-8")
        (root / "book.md").write_text(
            "# 测试课\n\n"
            "*(参考时间: 00:00:00)*\n\n"
            "`goto`（让程序直接跳到指定位置继续执行的控制流语句）会影响程序结构。\n\n"
            "讲师认为，直接跳转会切断推理，因为读者难以判断下一步执行位置。\n",
            encoding="utf-8",
        )
        # The publishable artifact is the rendered HTML; the audit must bind
        # its fingerprint to the Markdown and sidecars.
        (root / "book.html").write_text("<!doctype html><article>测试课</article>\n", encoding="utf-8")
        source = prepare(root, window=600)
        quote = source["chunks"][0]["text"].splitlines()[0]
        item = {
            "id": "K01",
            "priority": "A",
            "topic": "控制流与可读性",
            "kind": "opinion",
            "why": "解释结构化控制流的学习价值",
            "sources": [{"chunk": "S01", "quote": quote}],
            "must_preserve": ["直接跳转会切断推理"],
            "terms": ["goto"],
            "uncertainty": "",
        }
        if with_key_terms:
            item["key_terms"] = [
                {
                    "term": "goto",
                    "definition": "让程序直接跳到指定位置继续执行的控制流语句",
                    "origin": "editor",
                }
            ]
        triage = {
            "version": 1,
            "status": "reviewed",
            "source_notes": ["使用校正字幕，保留原始 transcript.json 供核对"],
            "reviewed_chunks": ["S01"],
            "items": [item],
        }
        (root / "knowledge.triage.json").write_text(json.dumps(triage, ensure_ascii=False), encoding="utf-8")
        review = {
            "reviewer": "test-agent",
            "semantic_review": {
                "performed": True,
                "mode": "agent_assisted",
                "method": "逐窗阅读 source.md，并逐项对照 book.md 与字幕",
            },
            "items": [
                {
                    "id": "K01",
                    "status": "covered",
                    "evidence": ["goto`（让程序直接跳到指定位置继续执行的控制流语句）会影响程序结构。"],
                    "checks": [{"requirement": "直接跳转会切断推理", "evidence": "直接跳转会切断推理"}],
                    "term_checks": [
                        {
                            "term": "goto",
                            "status": "defined",
                            "first_use": "goto`（让程序直接跳到指定位置继续执行的控制流语句）",
                            "evidence": "goto`（让程序直接跳到指定位置继续执行的控制流语句）会影响程序结构。",
                        }
                    ],
                    "causal_check": {
                        "status": "pass",
                        "evidence": ["直接跳转会切断推理，因为读者难以判断下一步执行位置。"],
                        "note": "人工核对了原因与后果，没有用跨章节关键词拼接",
                    },
                    "attribution_check": {
                        "status": "pass",
                        "evidence": "讲师认为，直接跳转会切断推理",
                        "note": "正文保留讲师观点归属",
                    },
                    "note": "正文解释了术语、机制和讲师判断",
                }
            ],
            "source_sweep": {"chunks": ["S01"], "note": "完整回扫来源窗口"},
            "fidelity": {"status": "pass", "note": "事实、观点与推测边界已核对"},
            "redundancy": {"status": "pass", "note": "口癖和重复表达已压缩"},
            "accessibility": {"status": "pass", "note": "关键术语首现提供短释义，未给常用词强行加括号"},
        }
        if not valid_review:
            review.pop("semantic_review")
        (root / "coverage.audit.json").write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        return root, triage, review

    def test_valid_review_passes_with_source_and_semantic_evidence(self):
        root, triage, _ = self.make_fixture()
        self.assertEqual(triage_errors(triage, prepare(root)), [])
        report = audit(root)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["source_completeness"], "raw_and_corrected")
        self.assertEqual(report["metrics"]["reading_formula"], "reading_units / 400")
        check_ready(root)

    def test_term_checks_must_match_expected_names_not_only_count(self):
        root, _, review = self.make_fixture()
        review["items"][0]["term_checks"][0]["term"] = "wrong-term"
        (root / "coverage.audit.json").write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        report = audit(root)
        self.assertFalse(report["passed"])
        self.assertTrue(any("term_checks must match" in error or "missing term_check" in error for error in report["errors"]))

    def test_term_checks_reject_duplicate_names(self):
        root, _, review = self.make_fixture()
        review["items"][0]["term_checks"].append(dict(review["items"][0]["term_checks"][0]))
        (root / "coverage.audit.json").write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        report = audit(root)
        self.assertFalse(report["passed"])
        self.assertTrue(any("duplicate term_checks" in error for error in report["errors"]))

    def test_rendered_html_is_part_of_freshness_gate(self):
        root, _, _ = self.make_fixture()
        report = audit(root)
        self.assertTrue(report["passed"], report["errors"])
        (root / "book.html").write_text("<!doctype html><article>stale</article>\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            check_ready(root)

    def test_missing_rendered_html_blocks_audit(self):
        root, _, _ = self.make_fixture()
        (root / "book.html").unlink()
        report = audit(root)
        self.assertFalse(report["passed"])
        self.assertTrue(any("book.html" in error for error in report["errors"]))

    def test_missing_semantic_provenance_can_never_pass(self):
        root, _, _ = self.make_fixture(valid_review=False)
        report = audit(root)
        self.assertFalse(report["passed"])
        self.assertEqual(report["status"], "needs_review")
        self.assertTrue(any("provenance" in error or "performed" in error for error in report["errors"]))

    def test_a_item_without_key_terms_is_blocked_for_readability_audit(self):
        root, _, _ = self.make_fixture(with_key_terms=False)
        report = audit(root)
        self.assertFalse(report["passed"])
        self.assertTrue(any("key_terms" in error for error in report["errors"]))

    def test_no_learning_content_requires_explicit_outcome(self):
        root = Path(tempfile.mkdtemp(prefix="shelf_empty_test_"))
        (root / "transcript.json").write_text(
            json.dumps({"duration": 60, "segments": [{"start": "00:00:00", "text": "嗯嗯。"}]}), encoding="utf-8"
        )
        source = prepare(root)
        triage = {
            "version": 1,
            "status": "reviewed",
            "reviewed_chunks": [c["id"] for c in source["chunks"]],
            "items": [],
        }
        (root / "knowledge.triage.json").write_text(json.dumps(triage), encoding="utf-8")
        errors = triage_errors(triage, source)
        self.assertTrue(any("No A knowledge" in error for error in errors))

    def test_metrics_counts_markdown_as_one_approximate_unit_stream(self):
        result = metrics("# 标题\n\n中文 API\n\n```python\nprint('x')\n```", 60)
        self.assertGreater(result["reading_units"], 0)
        self.assertEqual(result["reading_minutes_300_500"][0], round(result["reading_units"] / 500, 2))
        self.assertEqual(result["reading_minutes_300_500"][1], round(result["reading_units"] / 300, 2))


if __name__ == "__main__":
    unittest.main()
