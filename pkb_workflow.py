#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are", "as", "by",
    "that", "this", "it", "be", "from", "at", "we", "you", "your", "their", "our", "can", "will", "not",
    "通过", "以及", "一个", "我们", "你", "他们", "可以", "需要", "进行", "如果", "已经", "没有", "这个", "那个",
    "并且", "因为", "所以", "或者", "其中", "如何", "什么", "为什么", "用于", "关于",
}


def now_str() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\-\s\u4e00-\u9fff]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-") or "untitled"


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".markdown"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"暂不支持的文件类型: {suffix}，请先转成 .md/.txt")


def is_supported_text(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".txt", ".markdown"}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']+|[\u4e00-\u9fff]{2,}", text)
    return [w.lower() for w in words if w.lower() not in STOPWORDS and len(w) > 1]


def summarize(text: str, max_sentences: int = 5) -> str:
    sentences = re.split(r"(?<=[。！？.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return "（空内容）"
    first = sentences[: max(2, min(max_sentences, len(sentences)))]
    return "\n".join(f"- {s}" for s in first)


def extract_entities(text: str, top_k: int = 8) -> list[str]:
    # 非严格实体抽取：用高频词近似，实际项目应交给 LLM。
    tokens = tokenize(text)
    counts = Counter(tokens)
    return [w for w, _ in counts.most_common(top_k)]


def append_log(log_path: Path, kind: str, title: str, detail: str) -> None:
    day = dt.datetime.utcnow().strftime("%Y-%m-%d")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n## [{day}] {kind} | {title}\n")
        f.write(f"- time: {now_str()}\n")
        f.write(f"- detail: {detail}\n")


def parse_index(index_path: Path) -> dict[str, str]:
    pages: dict[str, str] = {}
    if not index_path.exists():
        return pages
    for line in index_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"- \[(.+?)\]\((.+?)\):\s*(.+)", line)
        if m:
            _, link, summary = m.groups()
            pages[link] = summary
    return pages


def write_index(index_path: Path, pages: dict[str, str]) -> None:
    head = "# Index\n\n> Wiki 页面总览（由脚本维护）\n\n"
    body = "\n".join([f"- [{Path(p).stem}]({p}): {s}" for p, s in sorted(pages.items())])
    index_path.write_text(head + body + "\n", encoding="utf-8")


def init_repo(root: Path) -> None:
    for rel in ["raw", "wiki/pages", "wiki/entities", "schema"]:
        (root / rel).mkdir(parents=True, exist_ok=True)

    schema = root / "schema/AGENTS.md"
    if not schema.exists():
        schema.write_text(
            """# LLM Wiki 维护规则\n\n## 目标\n- 将 raw/ 中的新资料编译到 wiki/，而不是每次查询临时检索。\n\n## 三层结构\n1. raw/: 原始资料，只读。\n2. wiki/: 可演化知识页（LLM 或脚本维护）。\n3. schema/: 工作流与命名规范。\n\n## Ingest\n- 新增来源后，创建 summary 页面。\n- 更新 index.md。\n- 更新/创建相关 entity 页面并回链。\n- 追加 log.md。\n\n## Query\n- 先读 index.md 定位页面。\n- 回答时附引用页面路径。\n- 重要问答可落盘为新页面。\n\n## Lint\n- 检查孤儿页（无任何页面链接到它）。\n- 检查无 summary 的页面。\n- 检查重复标题。\n""",
            encoding="utf-8",
        )

    index = root / "wiki/index.md"
    if not index.exists():
        index.write_text("# Index\n\n> Wiki 页面总览（由脚本维护）\n", encoding="utf-8")

    log = root / "wiki/log.md"
    if not log.exists():
        log.write_text("# Log\n\n> 追加式操作日志\n", encoding="utf-8")


def ingest(root: Path, source_file: Path, title: str | None = None) -> Path:
    raw_dir = root / "raw"
    if raw_dir not in source_file.parents:
        raise ValueError("请把来源文件放到 raw/ 目录下再 ingest。")

    text = read_text(source_file)
    page_title = title or source_file.stem
    slug = slugify(page_title)
    page_path = root / f"wiki/pages/{slug}.md"

    summary = summarize(text)
    entities = extract_entities(text)

    links = [f"[[../entities/{slugify(e)}]]" for e in entities]

    page_path.write_text(
        f"# {page_title}\n\n"
        f"- source: `{source_file.as_posix()}`\n"
        f"- ingested_at: {now_str()}\n\n"
        f"## Summary\n{summary}\n\n"
        f"## Key Entities\n"
        + "\n".join(f"- {e} {l}" for e, l in zip(entities, links))
        + "\n",
        encoding="utf-8",
    )

    # 更新 entity 页面
    for e in entities:
        e_slug = slugify(e)
        e_path = root / f"wiki/entities/{e_slug}.md"
        if not e_path.exists():
            e_path.write_text(f"# {e}\n\n## Mentions\n", encoding="utf-8")
        with e_path.open("a", encoding="utf-8") as f:
            f.write(f"- [[../pages/{slug}.md]] ({now_str()})\n")

    # 更新 index
    idx_path = root / "wiki/index.md"
    pages = parse_index(idx_path)
    pages[f"pages/{slug}.md"] = summary.splitlines()[0].lstrip("- ") if summary else ""
    write_index(idx_path, pages)

    append_log(root / "wiki/log.md", "ingest", page_title, f"source={source_file.as_posix()} entities={len(entities)}")
    return page_path


def search_pages(root: Path, question: str, top_k: int = 5) -> list[tuple[Path, int]]:
    q = tokenize(question)
    if not q:
        return []
    score_map: dict[Path, int] = defaultdict(int)
    for md in (root / "wiki").rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore").lower()
        for tok in q:
            if tok in text:
                score_map[md] += text.count(tok)
    return sorted(score_map.items(), key=lambda kv: kv[1], reverse=True)[:top_k]


def query(root: Path, question: str, save: bool = False) -> str:
    results = search_pages(root, question)
    if not results:
        answer = "未找到相关页面。先 ingest 一些资料再查询。"
    else:
        lines = [f"问题：{question}", "", "候选页面："]
        for p, s in results:
            lines.append(f"- {p.relative_to(root).as_posix()} (score={s})")
        lines.append("\n建议：打开以上页面进行综合回答，并将高价值问答写回 wiki/pages/。")
        answer = "\n".join(lines)

    append_log(root / "wiki/log.md", "query", question[:60], f"hits={len(results)}")

    if save:
        slug = slugify(f"qa-{question[:40]}")
        out = root / f"wiki/pages/{slug}.md"
        out.write_text(f"# QA: {question}\n\n{answer}\n", encoding="utf-8")
    return answer


def lint(root: Path) -> dict[str, list[str]]:
    pages = list((root / "wiki").rglob("*.md"))
    content = {p: p.read_text(encoding="utf-8", errors="ignore") for p in pages}
    rel = {p: p.relative_to(root).as_posix() for p in pages}

    inbound = Counter()
    all_titles = Counter()
    for p, text in content.items():
        for m in re.findall(r"\[\[(.+?)\]\]", text):
            target = m.replace("../", "")
            if not target.endswith(".md"):
                target += ".md"
            inbound[target] += 1
        tm = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if tm:
            all_titles[tm.group(1).strip().lower()] += 1

    issues = {"orphans": [], "missing_summary": [], "duplicate_titles": []}
    for p, text in content.items():
        path = rel[p].replace("wiki/", "")
        if path not in {"index.md", "log.md"} and inbound[path] == 0:
            issues["orphans"].append(path)
        if "/pages/" in rel[p] and "## Summary" not in text:
            issues["missing_summary"].append(path)

    issues["duplicate_titles"] = [t for t, c in all_titles.items() if c > 1]

    append_log(root / "wiki/log.md", "lint", "health-check", json.dumps({k: len(v) for k, v in issues.items()}, ensure_ascii=False))
    return issues


def import_dir(root: Path, source_dir: Path, do_ingest: bool = True, move: bool = False) -> list[Path]:
    """
    把外部目录中的 .md/.txt/.markdown 文件导入 raw/，并可选自动 ingest。
    用于对接 NotebookLM/其他工具导出的本地目录。
    """
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"source_dir 不存在或不是目录: {source_dir}")

    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    imported_pages: list[Path] = []

    candidates = sorted([p for p in source_dir.iterdir() if p.is_file() and is_supported_text(p)])
    if not candidates:
        append_log(root / "wiki/log.md", "import", source_dir.as_posix(), "no_supported_files")
        return imported_pages

    for src in candidates:
        stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        dst_name = f"{slugify(src.stem)}-{stamp}{src.suffix.lower()}"
        dst = raw_dir / dst_name
        if move:
            shutil.move(src.as_posix(), dst.as_posix())
        else:
            shutil.copy2(src.as_posix(), dst.as_posix())

        if do_ingest:
            page = ingest(root, dst, title=src.stem)
            imported_pages.append(page)

    append_log(
        root / "wiki/log.md",
        "import",
        source_dir.as_posix(),
        f"files={len(candidates)} ingest={do_ingest} move={move}",
    )
    return imported_pages


def main() -> None:
    parser = argparse.ArgumentParser(description="Karpathy 风格 LLM Wiki 个人知识库工作流（轻量实现）")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="知识库根目录")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="初始化目录结构")

    p_ingest = sub.add_parser("ingest", help="摄入 raw 文件")
    p_ingest.add_argument("source", type=Path, help="raw/ 下的 .md/.txt 文件")
    p_ingest.add_argument("--title", type=str, default=None, help="页面标题")

    p_query = sub.add_parser("query", help="查询 wiki 页面")
    p_query.add_argument("question", type=str)
    p_query.add_argument("--save", action="store_true", help="把查询结果存成页面")

    sub.add_parser("lint", help="健康检查")

    p_import = sub.add_parser("import-dir", help="从导出目录批量导入到 raw/，并可选自动 ingest（适合 NotebookLM 导出）")
    p_import.add_argument("source_dir", type=Path, help="外部导出目录（仅扫描第一层文件）")
    p_import.add_argument("--no-ingest", action="store_true", help="仅导入 raw，不自动 ingest")
    p_import.add_argument("--move", action="store_true", help="移动文件而非复制")

    args = parser.parse_args()
    root = args.root.resolve()

    if args.cmd == "init":
        init_repo(root)
        print(f"✅ initialized at {root}")
    elif args.cmd == "ingest":
        page = ingest(root, args.source.resolve(), args.title)
        print(f"✅ ingested -> {page}")
    elif args.cmd == "query":
        print(query(root, args.question, args.save))
    elif args.cmd == "lint":
        issues = lint(root)
        print(json.dumps(issues, ensure_ascii=False, indent=2))
    elif args.cmd == "import-dir":
        pages = import_dir(root, args.source_dir.resolve(), do_ingest=not args.no_ingest, move=args.move)
        if pages:
            print("✅ imported and ingested pages:")
            for p in pages:
                print(f"- {p}")
        else:
            print("✅ import completed (no pages ingested)")


if __name__ == "__main__":
    main()
