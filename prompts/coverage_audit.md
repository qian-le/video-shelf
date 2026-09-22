# Coverage Audit（内部审稿）

读当前书、完整知识清单及对应字幕。逐个检查 A/B 项的解释、因果、例子、限制、观点归属，而不是关键词是否出现。另回看每个分段，查 triage 本身是否漏掉高价值知识；若有，先补清单。检查书中无来源的新说法。

写 `coverage.audit.json`：

```json
{
  "version":1,
  "reviewer":"实际执行者及方法，不伪称独立盲评",
  "items":[
    {"id":"K01", "status":"covered", "evidence":["正文原样短引文"],
     "checks":[{"requirement":"must_preserve 的原样条目", "evidence":"支撑这条的正文原样短引文"}],
     "term_checks":[{"term":"术语", "status":"defined", "first_use":"术语（说明它在当前语境中做什么）", "evidence":"包含首现短释义的正文原样短引文"}],
     "causal_check":{"status":"pass", "evidence":["包含原因→推理→结果的正文原样短引文"], "note":"逐项读过因果链，而非只看关键词"},
     "attribution_check":{"status":"pass", "evidence":"包含讲师观点/预测归属的正文原样短引文", "note":"事实、观点与预测边界仍清楚"},
     "note":"为何满足，推测是否仍被标注"}
  ],
  "source_sweep":{"chunks":["S01", "S02"], "note":"回看完整来源后的遗漏检查"},
  "fidelity":{"status":"pass", "note":"事实/观点/预测边界及无来源增补检查"},
  "redundancy":{"status":"pass", "note":"C 删除，B 合并，正文与附录不重复"},
  "budget_note":"超出软目标时解释原因，否则可为空"
}
```

每个 A/B 项恰好一条记录。status 只能是 covered / partial / missing / distorted；covered 时每条 must_preserve 都要有对应 checks 证据。A 项的每个 `key_term` 都要有 `term_checks`：`evidence` 必须是书中首现短释义的原样引文，不能只命中名词；缩写要说明中文作用。A 项还要有明确的 `causal_check`（或写明 not_applicable）和逐项阅读后的语义说明；`opinion`/`prediction`/`speculation` 必须有 `attribution_check`。纯名词命中最多 partial。C 不应出现在书里，但不可只凭短词判断泄漏，需审读上下文。

顶层必须保存真实执行 provenance，例如：

```json
"semantic_review": {
  "performed": true,
  "mode": "agent_assisted",
  "method": "逐窗阅读 quality/source.md，并逐项对照 book.md 与原字幕"
}
```

没有 `semantic_review.performed=true`、来源回扫和逐项引文时，脚本只能报告 needs review，不能声称覆盖通过。脚本做的是结构证据校验，不能从关键词自动推出语义覆盖，也不能声称模型已经运行。

审查命令检查来源引文、正文引文、漏审条目和阅读预算；它不能证明语义覆盖或独立确认新闻。未通过时返回修订，不自动发布。不要自动把 partial 改成 covered；修正文后重做相关审查。改书会使原审查过期，须再次运行。

小白可读性审查：逐节检查首次出现的专业词是否有紧邻的括号通俗解释，解释是否引入新障碍。fidelity.note 之外增加 `accessibility: {"status":"pass", "note":"首次术语解释及理解路径检查"}`。不要求重复解释，也不要求为普通词加括号。
