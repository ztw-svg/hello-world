# hello-world

这是一个可直接运行的 **Karpathy 风格个人知识库（LLM Wiki）工作流**最小实现：
- 三层结构：`raw/`（原始资料）→ `wiki/`（编译后的知识页）→ `schema/`（规则）。
- 三个核心操作：`ingest`（摄入）、`query`（查询）、`lint`（体检）。
- 索引与日志：`wiki/index.md` + `wiki/log.md`。

> 说明：本实现参考了 Andrej Karpathy 在 **2026-04-04** 发布的 `llm-wiki` 思路（“把知识编译进 wiki，而不是每次 query 临时检索”），并做成一个本地可跑脚手架。

---

## 1) 快速开始

### 环境
- Python 3.10+

### 初始化
```bash
python3 pkb_workflow.py --root . init
```

会创建：
```text
raw/
wiki/
  index.md
  log.md
  pages/
  entities/
schema/
  AGENTS.md
```

---

## 2) 如何使用

### Step A. 放入原始资料（raw 层）
例如：
```bash
cat > raw/transformer-notes.md <<'EOF'
Transformer 使用 self-attention 建模长距离依赖。
在训练中通常需要位置编码。
多头注意力可以从不同子空间捕捉关系。
EOF
```

### Step B. 摄入（ingest）
```bash
python3 pkb_workflow.py ingest raw/transformer-notes.md --title "Transformer 笔记"
```

脚本会自动：
1. 在 `wiki/pages/` 生成页面（含 summary、实体）。
2. 更新 `wiki/entities/` 里的实体页与回链。
3. 更新 `wiki/index.md`。
4. 追加 `wiki/log.md`。

### Step C. 查询（query）
```bash
python3 pkb_workflow.py query "位置编码有什么作用？"
```

会返回候选页面及分数，帮助你快速定位。

如需把查询结果沉淀成页面：
```bash
python3 pkb_workflow.py query "多头注意力有什么优势？" --save
```

### Step D. 体检（lint）
```bash
python3 pkb_workflow.py lint
```

会检查：
- orphan pages（孤儿页）
- missing summary（缺 Summary 的页）
- duplicate titles（重复标题）

### Step E. 从 NotebookLM/其他工具导出目录一键导入

如果你把资料导出到某个本地目录（例如 `~/Downloads/notebooklm-exports`），可以直接批量导入：

```bash
python3 pkb_workflow.py import-dir ~/Downloads/notebooklm-exports
```

默认行为：
- 复制 `.md/.txt/.markdown` 到 `raw/`
- 自动执行 ingest（写入 `wiki/pages` / `wiki/entities` / `wiki/index.md` / `wiki/log.md`）

可选参数：
```bash
# 只导入 raw，不自动 ingest
python3 pkb_workflow.py import-dir ~/Downloads/notebooklm-exports --no-ingest

# 移动文件（而不是复制）
python3 pkb_workflow.py import-dir ~/Downloads/notebooklm-exports --move
```

---

## 3) 典型工作流（建议）

1. 你每天把文章/读书笔记/会议纪要放入 `raw/`。
2. 每次只 ingest 1~3 篇，边看边纠偏。
3. 提问时先 query，再把高价值回答 `--save` 回 wiki。
4. 每周跑一次 lint，清理结构问题。
5. 如果你用 NotebookLM 或别的工具，固定一个“导出目录”，每天跑一次 `import-dir`。

这就形成了“可累积”的知识库：越用越有价值。

---

## 4) 进阶建议

- 目前的“实体抽取/摘要”是启发式（轻量、零依赖）。
- 生产版建议把 `summarize()` / `extract_entities()` 替换为你常用 LLM API。
- 也可对接 Obsidian（把该目录当 Vault 打开）获得图谱浏览体验。

---

## 5) Google AI Pro 用户推荐方案（Gemini + Drive）

如果你已经有 Google AI Pro，希望使用 Google 生态来跑知识库，可以用仓库里的：

```bash
google_pkb_workflow.py
```

这个版本支持：
- 用 Gemini API 生成更好的摘要和实体（有 `GEMINI_API_KEY` 时）
- 无 key 时自动回退到本地启发式算法
- 把 `--root` 指到 Google Drive 同步目录，实现“云端存储 + 本地运行”

### 快速开始

```bash
# 1) 初始化（可把目录放进 Google Drive）
python3 google_pkb_workflow.py --root ~/GoogleDrive/my-pkb init

# 2) 摄入文档
python3 google_pkb_workflow.py \
  --root ~/GoogleDrive/my-pkb \
  --api-key "$GEMINI_API_KEY" \
  ingest ~/Downloads/note.md --title "我的笔记"

# 3) 基于 wiki 回答问题，并把回答落盘到 wiki/answers/
python3 google_pkb_workflow.py \
  --root ~/GoogleDrive/my-pkb \
  --api-key "$GEMINI_API_KEY" \
  answer "这周项目里关于检索质量优化的结论是什么？"
```

### 建议的 Google 工作流

1. 在 NotebookLM / Google Docs / 网页里整理资料。  
2. 导出为 txt/md 到本地目录。  
3. 用 `google_pkb_workflow.py ingest` 持续编译进 wiki。  
4. 用 `answer` 做问答沉淀，形成 `wiki/answers/`。  
