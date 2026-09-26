# Decisions

- Date: 2026-09-26
- Change: 保留现有发布契约：存在 knowledge.triage.json 的书必须通过新鲜审计；无分诊文件的旧书继续兼容。合并代码不自动发布 pages。
- Impact: 结构门禁不等于独立语义或外部事实核验；阅读时长使用估算公式。
- Verification: publish.main 在新鲜审计下进入发布阶段；修改 HTML 后在该阶段之前退出。测试拦截后续发布操作，未创建或推送 pages。
