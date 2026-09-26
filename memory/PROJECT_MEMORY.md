# Project Memory

- Date: 2026-09-26
- Change: Shelf 的内容流程为校正字幕、来源窗口、知识分诊、正文、截帧、HTML 渲染、覆盖审稿、质量审计、发布。src/book_quality.py 负责结构证据、阅读指标和文件新鲜度；语义判断由 Agent 或编辑完成。
- Impact: knowledge.triage.json 与 coverage.audit.json 是内容流程的输入；quality/report.json 是审计结果。修改最终产物后必须重新审计。
- Verification: 9 个单元测试通过；第 05、10、28 讲临时副本均通过 triage_errors、audit 和 check_ready。
