# Knowledge Triage（内部编辑清单）

读 `quality/source.md` 的所有分段。分段仅控制上下文，不代表篇幅配额。依照 stitcher_system.md 的 A/B/C 标准判断价值；按知识点聚合跨段重复，保留不同机制、例子、反例、条件。不要逐句登记，不因标题或时间位置删内容。

写 `knowledge.triage.json`：

```json
{
  "version": 1,
  "source_notes": ["原始/校正来源及疑点"],
  "reviewed_chunks": ["S01", "S02"],
  "items": [
    {"id":"K01", "priority":"A", "topic":"知识点",
     "kind":"observation", "why":"保留的学习价值",
     "sources":[{"chunk":"S01", "quote":"字幕中确实存在的短引文"}],
     "must_preserve":["读者必须理解的机制或条件", "有依据的因果/例子"],
     "terms":["术语"],
     "key_terms":[{"term":"术语", "definition":"在本语境中是什么/做什么的短提示", "origin":"editor"}],
     "uncertainty":"无或需标注的推测/疑词"},
    {"id":"K02", "priority":"C", "topic":"无价值等待",
     "kind":"observation", "why":"没有学习信息",
     "sources":[{"chunk":"S02", "quote":"确实存在的短引文"}],
     "must_preserve":[], "terms":[], "uncertainty":""}
  ]
}
```

`kind` 为 observation（来源陈述/演示）、opinion（观点）、prediction（预测）、speculation（推测），混合内容拆项或在 uncertainty 里分清。每项至少一个真实来源短引文；跨段链条按需要引用多个分段。A 项必须有 `key_terms` 字段：只列真正影响零基础理解、需要在首次出现处加短释义的术语；常用词不要列入。每个 key term 写一个简短 `definition` 提示，并将 `origin` 标为 `editor`（编者基础释义）或 `speaker`（讲师原意）。C 按删除类别概括，不列每个口癖；只有不存在 C 时才不列。

对读者可见的关键术语，首现释义应说明“是什么、做什么或解决什么问题”。缩写不能只展开英文；不要把多个术语塞在一个巨型括号里。`key_terms` 是可读性审查索引，不等于知识覆盖，价值和 `must_preserve` 才是正文契约。

每段必须审过并至少有一个有来源的清单项；零知识段可只对应一个 C 项。检查末段，不以「前面已经够多」停止。`reviewed_chunks` 表示实际阅读，不能先勾选再补读。专有名词清单不等于知识覆盖，价值和 must_preserve 才是正文契约。
