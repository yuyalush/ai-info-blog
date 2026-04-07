#!/usr/bin/env python3
"""
Daily AI news article generator using Claude API + RSS feeds.
Fetches AI-related news from the past few days and generates a Japanese article.
"""

import os
import sys
import datetime
import re
from pathlib import Path

import feedparser
import anthropic

# ---------------------------------------------------------------------------
# RSS feed sources
# ---------------------------------------------------------------------------
FEEDS = [
    # AI Company blogs
    {"url": "https://www.anthropic.com/news/rss", "source": "Anthropic"},
    {"url": "https://openai.com/news/rss.xml", "source": "OpenAI"},
    {"url": "https://github.blog/feed/", "source": "GitHub"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "source": "Microsoft AI"},
    {"url": "https://ai.googleblog.com/feeds/posts/default", "source": "Google AI"},
    # Tech news
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch"},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat"},
    {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge"},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss", "source": "Wired"},
    {"url": "https://feeds.feedburner.com/oreilly/radar", "source": "O'Reilly Radar"},
]

# Keywords to filter for AI relevance
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "llm", "gpt",
    "claude", "gemini", "copilot", "chatgpt", "openai", "anthropic",
    "language model", "neural", "deep learning", "generative", "agent",
    "mistral", "llama", "transformer", "rag", "fine-tun", "diffusion",
    "github copilot", "google ai", "microsoft ai", "hugging face",
]

POSTS_DIR = Path(__file__).parent.parent / "site" / "content" / "posts"


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def fetch_recent_news(days_back: int = 3) -> list[dict]:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    articles = []

    for feed_info in FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime.datetime(
                        *entry.published_parsed[:6], tzinfo=datetime.timezone.utc
                    )
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime.datetime(
                        *entry.updated_parsed[:6], tzinfo=datetime.timezone.utc
                    )

                if published is None or published < cutoff:
                    continue

                title = entry.get("title", "").strip()
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:400]
                link = entry.get("link", "")

                if not title or not is_ai_related(title, summary):
                    continue

                articles.append({
                    "title": title,
                    "summary": summary.strip(),
                    "link": link,
                    "published": published.strftime("%Y-%m-%d"),
                    "source": feed_info["source"],
                })

        except Exception as exc:
            print(f"[WARN] Failed to fetch {feed_info['url']}: {exc}", file=sys.stderr)

    # Deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        key = a["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    # Sort by date descending
    unique.sort(key=lambda x: x["published"], reverse=True)
    return unique


def generate_article(articles: list[dict]) -> str:
    client = anthropic.Anthropic()

    news_text = "\n".join(
        f"- [{a['source']}] ({a['published']}) {a['title']}\n"
        f"  概要: {a['summary'][:250]}\n"
        f"  URL: {a['link']}"
        for a in articles[:30]
    )

    today_str = datetime.date.today().strftime("%Y年%m月%d日")

    prompt = f"""あなたはAI技術に詳しい日本語ブログライターです。
以下は過去3日間のAI関連ニュース一覧です。これらを基に、{today_str}付けのブログ記事を日本語で執筆してください。

## 対象トピック（優先度順）
1. GitHub Copilot / Claude / ChatGPT などAI開発ツールのアップデート
2. GPT・Claude・Gemini など主要LLMの新機能・モデル更新
3. AI業界の重要発表・資金調達・提携
4. 注目のAI技術トレンド（エージェント・RAG・マルチモーダルなど）

## ニュース一覧
{news_text}

## 記事フォーマット（必ず守ること）
- 1行目: `# 記事タイトル`（今日の主要ニュースを反映した魅力的な見出し）
- 2〜3行の導入文（今日のAI界隈のハイライトを簡潔に）
- 3〜5つのセクション（`## セクション名` 形式、各200〜350字）
  - 各セクションの末尾に参照URLを `> 参照: URL` で記載
- `## まとめ` セクション（100〜150字、今日のトレンドを総括）

重複や無関係なニュースは省略し、最も重要なものを厳選してください。
記事全体で1,000〜1,500字程度を目標にしてください。
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def save_post(content: str, date: datetime.date) -> Path:
    lines = content.strip().splitlines()

    # Extract title from first # heading
    title = f"AI News {date.strftime('%Y-%m-%d')}"
    body_lines = lines
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_lines = lines[i + 1 :]
            break

    # Escape double quotes in title
    title_escaped = title.replace('"', '\\"')

    front_matter = f"""---
title: "{title_escaped}"
date: {date.strftime("%Y-%m-%dT09:00:00+09:00")}
draft: false
tags: ["AI", "ニュース", "LLM", "GitHub Copilot", "Claude", "ChatGPT"]
description: "{title_escaped}"
---
"""

    post_content = front_matter + "\n" + "\n".join(body_lines).strip() + "\n"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path = POSTS_DIR / f"{date.strftime('%Y-%m-%d')}.md"
    post_path.write_text(post_content, encoding="utf-8")
    return post_path


def main() -> None:
    today = datetime.date.today()
    post_path = POSTS_DIR / f"{today.strftime('%Y-%m-%d')}.md"

    if post_path.exists():
        print(f"Post for {today} already exists: {post_path}. Skipping.")
        return

    print("Fetching recent AI news from RSS feeds...")
    articles = fetch_recent_news(days_back=3)
    print(f"Found {len(articles)} AI-related articles")

    if not articles:
        print("No relevant articles found. Skipping post generation.")
        sys.exit(0)

    print("Generating article with Claude...")
    content = generate_article(articles)

    print("Saving post...")
    saved_path = save_post(content, today)
    print(f"Post saved: {saved_path}")


if __name__ == "__main__":
    main()
