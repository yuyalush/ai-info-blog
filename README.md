# AI Info Blog

GitHub Copilot・Claude・ChatGPT などの AI 開発ツールや LLM の最新情報を毎日自動で収集・生成・公開するブログです。

**公開サイト:** https://yuyalush.github.io/ai-info-blog/

## 概要

毎朝 09:00 JST に GitHub Actions が起動し、前日の AI 関連ニュースを RSS フィードから収集、Claude API で日本語記事を生成して GitHub Pages に自動デプロイします。

```
毎日 09:00 JST
  │
  ▼
GitHub Actions 起動
  │
  ▼
RSS フィード収集（7ソース）
  │
  ▼
Claude Sonnet が日本語記事を生成
  │
  ▼
Hugo でビルド
  │
  ▼
GitHub Pages へデプロイ
```

## 扱うトピック

- **AI 開発ツール** — GitHub Copilot・Cursor・Cline などのアップデート
- **主要 LLM** — Claude・GPT・Gemini・Llama などの新機能・モデル更新
- **AI 業界ニュース** — 資金調達・企業提携・規制動向
- **技術トレンド** — エージェント・RAG・マルチモーダル・ファインチューニングなど

基本は前日のニュースですが、まだ取り上げていない内容であれば数日遡ることもあります。

## 技術スタック

| 役割 | 技術 |
|------|------|
| 記事生成 | [Claude Sonnet 4.6](https://www.anthropic.com) (Anthropic API) |
| ニュース収集 | RSS フィード + [feedparser](https://feedparser.readthedocs.io/) |
| 静的サイト | [Hugo](https://gohugo.io/) |
| 自動化 | [GitHub Actions](https://github.com/features/actions) |
| ホスティング | [GitHub Pages](https://pages.github.com/) |

## ディレクトリ構成

```
ai-info-blog/
├── .github/
│   └── workflows/
│       └── daily-post.yml    # 毎日実行される自動化ワークフロー
├── scripts/
│   ├── generate_post.py      # ニュース収集 & 記事生成スクリプト
│   └── requirements.txt      # Python 依存パッケージ
└── site/
    ├── config.toml           # Hugo 設定
    ├── content/
    │   └── posts/            # 生成された記事（Markdown）
    ├── layouts/              # Hugo テンプレート（カスタムテーマ）
    │   └── _default/
    │       ├── baseof.html
    │       ├── list.html
    │       └── single.html
    └── static/
        └── css/
            └── style.css     # サイトスタイル
```

## セットアップ

### 必要なもの

- GitHub アカウント
- Anthropic API キー（[取得はこちら](https://console.anthropic.com/)）

### 手順

**1. リポジトリをフォーク / クローン**

```bash
git clone https://github.com/yuyalush/ai-info-blog.git
cd ai-info-blog
```

**2. GitHub Secrets に API キーを登録**

リポジトリの Settings → Secrets and variables → Actions から追加するか、CLI で実行：

```bash
echo "YOUR_ANTHROPIC_API_KEY" | gh secret set ANTHROPIC_API_KEY
```

**3. GitHub Pages を有効化**

リポジトリの Settings → Pages → Source を **GitHub Actions** に設定する。

（初回のみ）手動でワークフローを実行してデプロイを確認：

```bash
gh workflow run daily-post.yml
```

### ローカルでの動作確認

```bash
# Python 依存パッケージをインストール
pip install -r scripts/requirements.txt

# 記事を手動生成（ANTHROPIC_API_KEY が必要）
ANTHROPIC_API_KEY=sk-ant-... python scripts/generate_post.py

# Hugo でローカルプレビュー
hugo server --source site
# → http://localhost:1313 で確認
```

## ワークフローの詳細

### `daily-post.yml`

| ステップ | 内容 |
|----------|------|
| RSS 収集 | 7つのフィードから過去3日分の記事を取得 |
| フィルタリング | AI 関連キーワードで絞り込み（重複除去含む） |
| 記事生成 | Claude Sonnet 4.6 が日本語で3〜5セクションの記事を生成 |
| コミット | `site/content/posts/YYYY-MM-DD.md` を main へプッシュ |
| ビルド | Hugo でミニファイ付きビルド |
| デプロイ | GitHub Pages へ公開 |

スケジュール: 毎日 `0 0 * * *`（UTC）= 09:00 JST  
手動実行: Actions タブから `workflow_dispatch` で即時実行可能。

### RSS フィードソース

| ソース | URL |
|--------|-----|
| Anthropic | anthropic.com/news |
| OpenAI | openai.com/news |
| GitHub Blog | github.blog |
| Microsoft AI | blogs.microsoft.com/ai |
| Google AI | ai.googleblog.com |
| TechCrunch AI | techcrunch.com/category/artificial-intelligence |
| VentureBeat AI | venturebeat.com/category/ai |
| The Verge | theverge.com |
| Wired AI | wired.com/tag/ai |

## ライセンス

MIT
