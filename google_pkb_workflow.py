#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are", "as", "by",
    "that", "this", "it", "be", "from", "at", "we", "you", "your", "their", "our", "can", "will", "not",
    "通过", "以及", "一个", "我们", "你", "他们", "可以", "需要", "进行", "如果", "已经", "没有", "这个", "那个",
}


def now_str() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\-\s\u4e00-\u9fff]", "", text.strip().lower())
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80].strip("-") or "untitled"


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']+|[\u4e00-\u9fff]{2,}", text)
    return [w.lower() for w in words if w.lower() not in STOPWORDS and len(w) > 1]


def heuristic_summary(text: str, n: int = 4) -> str:
    parts = [p.strip() for p in re.split(r"(?<=[。！？.!?])\s+", text) if p.strip()]
    if not parts:
        return "（空内容）"
    return "\n".join(f"- {x}" for x in parts[:n])


def heuristic_entities(text: str, top_k: int = 8) -> list[str]:
    c = Counter(tokenize(text))
    return [w for w, _ in c.most_common(top_k)]


def gemini_generate(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="ignore"))
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return json.dumps(body, ensure_ascii=False)


def llm_summary_and_entities(text: str, api_key: str | None) -> tuple[str, list[str]]:
    if not api_key:
        return heuristic_summary(text), heuristic_entities(text)

    prompt = (
        "你是知识库编译助手。请根据输入文本返回 JSON，格式: "
        "{\"summary\": [\"...\"], \"entities\": [\"...\"]}。"
        "summary 给 3-6 条要点，entities 给 5-10 个核心实体词。仅输出 JSON。\n\n"
        f"文本:\n{text[:15000]}"
    )
    out = gemini_generate(prompt, api_key)
    try:
        m = re.search(r"\{.*\}", out, flags=re.S)
        data = json.loads(m.group(0) if m else out)
        summary = "\n".join(f"- {x}" for x in data.get("summary", []) if isinstance(x, str))
        entities = [x for x in data.get("entities", []) if isinstance(x, str)]
        if summary and entities:
            return summary, entities[:10]
    except Exception:
        pass
    return heuristic_summary(text), heuristic_entities(text)


def init_root(root: Path) -> None:
    for rel in ["raw", "wiki/pages", "wiki/entities", "wiki/answers"]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "wiki/index.md").write_text("# Index\n\n", encoding="utf-8") if not (root / "wiki/index.md").exists() else None
    (root / "wiki/log.md").write_text("# Log\n\n", encoding="utf-8") if not (root / "wiki/log.md").exists() else None


def append_log(root: Path, kind: str, detail: str) -> None:
    with (root / "wiki/log.md").open("a", encoding="utf-8") as f:
        f.write(f"## {kind} @ {now_str()}\n- {detail}\n")


def upsert_index(root: Path, rel_path: str, summary_line: str) -> None:
    idx = root / "wiki/index.md"
    rows = idx.read_text(encoding="utf-8", errors="ignore").splitlines() if idx.exists() else ["# Index", ""]
    entries = [x for x in rows if x.startswith("- [")]
    other = [x for x in rows if not x.startswith("- [")]
    mapping = {}
    for e in entries:
        m = re.match(r"- \[(.+?)\]\((.+?)\):\s*(.*)", e)
        if m:
            _, p, s = m.groups()
            mapping[p] = s
    mapping[rel_path] = summary_line
    rebuilt = other + [f"- [{Path(p).stem}]({p}): {s}" for p, s in sorted(mapping.items())]
    idx.write_text("\n".join(rebuilt).rstrip() + "\n", encoding="utf-8")


def ingest(root: Path, source: Path, title: str | None, api_key: str | None) -> Path:
    if not source.exists():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8", errors="ignore")
    title = title or source.stem
    slug = slugify(title)

    summary, entities = llm_summary_and_entities(text, api_key)
    page = root / f"wiki/pages/{slug}.md"
    page.write_text(
        f"# {title}\n\n- source: `{source}`\n- ingested_at: {now_str()}\n\n"
        f"## Summary\n{summary}\n\n## Key Entities\n"
        + "\n".join(f"- {e}" for e in entities)
        + "\n",
        encoding="utf-8",
    )

    for e in entities[:12]:
        ep = root / f"wiki/entities/{slugify(e)}.md"
        if not ep.exists():
            ep.write_text(f"# {e}\n\n## Mentions\n", encoding="utf-8")
        with ep.open("a", encoding="utf-8") as f:
            f.write(f"- [[../pages/{slug}.md]]\n")

    first_line = summary.splitlines()[0].lstrip("- ") if summary.splitlines() else ""
    upsert_index(root, f"pages/{slug}.md", first_line)
    append_log(root, "ingest", f"{source} -> pages/{slug}.md")
    return page


def search(root: Path, q: str, top_k: int = 5) -> list[tuple[Path, int]]:
    toks = tokenize(q)
    scores: dict[Path, int] = {}
    for p in (root / "wiki/pages").glob("*.md"):
        t = p.read_text(encoding="utf-8", errors="ignore").lower()
        s = sum(t.count(tok) for tok in toks)
        if s > 0:
            scores[p] = s
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]


def answer(root: Path, question: str, api_key: str | None, model: str) -> str:
    hits = search(root, question)
    if not hits:
        return "没有检索到相关页面，请先 ingest。"
    context = []
    for p, s in hits:
        context.append(f"[{p.name} score={s}]\n" + p.read_text(encoding="utf-8", errors="ignore")[:4000])

    if api_key:
        prompt = (
            "根据以下 wiki 页面回答问题，并在结尾列出引用页面文件名。\n\n"
            f"问题：{question}\n\n" + "\n\n".join(context)
        )
        out = gemini_generate(prompt, api_key, model=model)
    else:
        out = "未配置 GEMINI_API_KEY，以下是候选页面：\n" + "\n".join(f"- {p.name} (score={s})" for p, s in hits)

    ans_file = root / f"wiki/answers/{slugify(question)[:60]}.md"
    ans_file.write_text(f"# Q: {question}\n\n{out}\n", encoding="utf-8")
    append_log(root, "answer", f"{question} -> {ans_file.name}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Google 生态可用的个人知识库工作流（Gemini + 本地/Drive 目录）")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="知识库根目录（可设为 Google Drive 同步目录）")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Gemini 模型名")
    parser.add_argument("--api-key", type=str, default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("source", type=Path)
    p_ingest.add_argument("--title", type=str, default=None)

    p_answer = sub.add_parser("answer")
    p_answer.add_argument("question", type=str)

    args = parser.parse_args()
    root = args.root.resolve()

    if args.cmd == "init":
        init_root(root)
        print(f"✅ initialized at {root}")
    elif args.cmd == "ingest":
        init_root(root)
        page = ingest(root, args.source.resolve(), args.title, args.api_key)
        print(f"✅ ingested: {page}")
    elif args.cmd == "answer":
        init_root(root)
        print(answer(root, args.question, args.api_key, model=args.model))


if __name__ == "__main__":
    main()
