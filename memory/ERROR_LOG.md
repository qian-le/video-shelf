# Error Log

- Date: 2026-09-26
- Change: 确认第 05、10、28 讲样本缺少原始 transcript.json，审计报告均返回 corrected_only 和时长估算警告；这是样本证据边界，不是本次新增回归。
- Impact: 不能将样本审计通过描述为原始/校正双源核验，也不能把估算阅读时长当实测。
- Verification: 在三个样本的临时副本执行 audit，检查 source_completeness、warnings 和 passed；三者均通过并保留上述警告。
