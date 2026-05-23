# SearXNG MCP Server

FastAPI-based server providing a search endpoint compatible with the Model Context Protocol (MCP). It features data guardrails using Microsoft Presidio to prevent Personally Identifiable Information (PII) leaks and sensitive word disclosures.

Model Context Protocol (MCP) に準拠した検索機能を提供する FastAPI ベースのサーバーです。個人情報（PII）の漏洩や機密ワードの送信を防ぐためのデータガードレール（情報流出防止機能）が標準で組み込まれています。

---

## 目次 / Table of Contents
1. [日本語版 / Japanese Version](#日本語版---japanese-version)
2. [English Version](#english-version)

---

## 日本語版 - Japanese Version

このプロジェクトは、AIエージェント（Claude Desktopなど）がSearXNGを介してWeb検索を行うためのブリッジです。検索クエリの送信時および検索結果の取得時の両方で、個人情報や機密性の高い言葉がやり取りされるのを自動的に防ぐ安全対策が施されています。

### 主な機能

- **FastAPIバックエンド**: 高速かつ非同期対応のモダンなAPIサーバー。
- **MCP統合**: `fastapi-mcp` を使用して、検索エンドポイントをAIエージェント用のMCPツールとして公開。
- **データガードレール（情報流出防止機能）**: 
  - **多言語インテリジェントマージ解析**: 英語（`en_core_web_sm`）と日本語（`ja_core_news_sm`）の両方のspaCy言語モデルおよび認識器を同時に実行・マージする高度な解析を実装。日本語文章内に含まれる英語メールアドレスや、日英混在したクエリでも漏れなく確実に個人情報（PII）を検出します。
  - **クエリフィルタ（入力防御）**: 検索クエリ内に個人情報（メール、電話番号、クレジットカード等）や指定の機密ワードが含まれる場合に、検索処理をブロック（400 Bad Request）またはプレースホルダーに匿名化。
  - **レスポンスフィルタ（出力防御）**: 検索結果（タイトルやコンテンツスニペット）に個人情報が含まれる場合、AIにデータを渡す前に自動マスキング（`[PHONE_NUMBER]` などのプレースホルダーに変換）。
  - **日本語・マイナンバーの境界バグ修正**: 日本語の文脈に隣接する12桁のマイナンバーも完全に検出できるように正規表現パターンを最適化（`(?<!\d)\d{12}(?!\d)`）。
  - **カスタム検出**: 日本の携帯/固定電話番号フォーマット、12桁のマイナンバー、および指定された `SENSITIVE_WORDS`（機密ワード）の検出に対応。
  - **AI用自律抑止指示**: ツールの詳細説明（Description）に日本語と英語で個人情報送信禁止の警告を明示し、AIモデル自身による自律的な送信防止を促進。
- **契約・統合テスト**: OpenAPI定義との整合性を担保する契約テスト、およびモックによる外部依存を排除した堅牢な統合テストスイート。

### プロジェクト構造

```
.
├── requirements-dev.txt
├── requirements.txt
├── searxng_config/
│   └── settings.yml       # SearXNGの設定ファイル
├── src/
│   ├── __init__.py
│   ├── config.py          # Pydanticを用いた環境変数・設定管理
│   ├── main.py            # FastAPIアプリケーションのエントリーポイントおよびMCPのセットアップ
│   ├── schemas.py         # リクエスト・レスポンスのPydanticモデル定義
│   ├── routers/
│   │   └── searxng_router.py # 検索エンドポイントの定義およびセキュリティガードレールの適用
│   └── services/
│       ├── searxng_service.py # SearXNG APIとの連携サービス
│       └── pii_service.py     # PII・機密ワードの検出およびマスキングを行うサービス
└── tests/
    ├── contract/
    │   └── test_search_api.py # OpenAPI契約検証テスト
    └── integration/
        ├── test_pii.py     # 個人情報・機密ワードフィルタリング機能の統合テスト
        └── test_search.py  # 検索APIの統合テスト
```

### 動作要件

- Python 3.11+
- `pip` または `uv` （推奨）
- Docker & Docker Compose （推奨環境）

### 起動方法

#### 1. Docker Composeを使用する場合（推奨）

FastAPIサーバーとSearXNGインスタンスが同時に起動します。

```bash
docker compose up --build
```

バックグラウンドで起動する場合は `-d` フラグを追加してください。

- **MCP サーバー**: `http://127.0.0.1:8000`
- **SearXNG サーバー**: `http://127.0.0.1:8080`

MCPサーバーの正常動作確認：
```bash
curl -i http://127.0.0.1:8000/mcp
```
`406 Not Acceptable`（`"Client must accept text/event-stream"`）が返ってくれば、正常に稼働しています。

> **セキュリティに関する重要事項:**
> SearXNGが正常かつ安全に動作するためには、セキュアな `SEARXNG_SECRET` 環境変数を設定する必要があります。
> 以下のコマンドでランダムな値を生成し、環境変数に設定、または `.env` ファイルに記述してください。
> ```bash
> openssl rand -hex 32
> ```
> 生成した値を設定して起動します：
> ```bash
> export SEARXNG_SECRET=your_generated_secret_here
> docker compose up --build
> ```

#### 2. ローカルで直接起動する場合

依存関係のインストール：
```bash
pip install -r requirements.txt
# または
uv pip install -r requirements.txt

# spaCyモデルおよび日本語形態素解析エンジンのダウンロード
python -m spacy download en_core_web_sm
python -m spacy download ja_core_news_sm
```


環境変数でSearXNGの接続先を指定して起動します：
```bash
export SEARXNG_URL=http://localhost:8080
uvicorn src.main:app --reload
```

- **APIドキュメント（Swagger UI）**: `http://127.0.0.1:8000/docs`
- **MCPエンドポイント**: `http://127.0.0.1:8000/mcp`

### 個人情報保護（PII）設定一覧

`.env` ファイルまたは環境変数経由で以下の設定をカスタマイズ可能です。

| 環境変数名 | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `PII_DETECTION_ENABLED` | bool | `True` | 個人情報および機密ワードの検出処理自体を有効にするか。 |
| `PII_BLOCK_LEVEL` | str | `"block"` | PII検出時の動作。`block`（検索拒否・エラー返却）、`anonymize`（匿名化して検索続行）、`off`（無効）。 |
| `PII_MASK_RESPONSE` | bool | `True` | 検索結果（タイトル、コンテンツ）内の個人情報をAIに返す前にマスキングするか。 |
| `SENSITIVE_WORDS` | list | `[]` | 検出時に無条件で検索をブロックする機密ワードのリスト（カンマ区切りで環境変数に指定可能）。 |
| `PII_ENTITIES` | list | `["PERSON", "EMAIL_ADDRESS", ...]` | 検出対象とするPIIカテゴリの指定。 |

### テストの実行方法

開発用依存関係をインストールし、`pytest` を実行します。テストはモックを使用して設計されているため、外部SearXNGとの接続なしで実行可能です。

```bash
# 依存関係のインストール
pip install -r requirements-dev.txt
# または
uv pip install -r requirements-dev.txt

# テストの実行
pytest -v
# または
uv run pytest -v
```

### 実際の検証・テスト結果（事例）

`docker compose` を用いて実際に SearXNG および MCP サーバーをローカルで起動し、接続テストを行った際の実機結果です。

#### 1. ヘルスチェックの確認 (`/`)
FastAPI サーバーが正常に起動し、SearXNG サービスと連携可能な状態であることを確認します。
```bash
curl -s http://127.0.0.1:8000/ | python3 -m json.tool
```
**出力結果:**
```json
{
    "status": "ok"
}
```

#### 2. 個人情報（PII）を含まない通常の検索 (`/search?q=python`)
検索キーワードに個人情報を含まない通常リクエストの例です。検索結果のコンテンツ内に含まれる個人情報（人名や地名など）が、AIエージェントに渡される前に自動的に匿名化・マスキングされているのが分かります。
```bash
curl -s "http://127.0.0.1:8000/search?q=python"
```
**出力結果 (抜粋):**
```json
{
  "query": "python",
  "results": [
    {
      "title": "Welcome to Python.org",
      "url": "https://www.python.org/",
      "content": "Python allows mandatory and optional arguments...",
      "engine": "google"
    },
    {
      "title": "Python",
      "url": "https://en.wikipedia.org/wiki/Python",
      "content": "<PERSON>",  // ← 人名が自動的に匿名化されています
      "engine": "wikipedia"
    },
    {
      "title": "Online Python - IDE, Editor...",
      "url": "https://www.online-python.com/",
      "content": "...development environment (<PERSON>). It is <LOCATION>, dependable...", // ← 人名や地名が自動的にマスキングされています
      "engine": "duckduckgo"
    }
  ],
  "number_of_results": 20
}
```

#### 3. クエリ入力における個人情報の送信ブロック (`/search?q=my email is test@example.com`)
ユーザーやAIエージェントが、クエリ入力として誤ってメールアドレスなどの機密個人情報を送信してしまった場合のブロック動作例です。SearXNG にリクエストが送信される前に、サーバー側で安全に遮断されます。
```bash
curl -s "http://127.0.0.1:8000/search?q=my%20email%20is%20test@example.com"
```
**出力結果 (400 Bad Request):**
```json
{
  "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: EMAIL_ADDRESS)"
}
```


---

## English Version

This project acts as a bridge allowing AI agents (such as Claude) to perform web searches using a local or remote SearXNG instance. It is built with an inline data guardrail system to secure query inputs and sanitize search result outputs, preventing the accidental transmission or exposure of sensitive data.

### Features

- **FastAPI Backend**: A modern, asynchronous high-performance web framework.
- **MCP Integration**: Exposes the search endpoint as an MCP-compatible tool using the `fastapi-mcp` library.
  - **Data Guardrails (PII & Sensitive Word Prevention)**:
    - **Multilingual Intelligent Merging**: Concurrently runs and merges results from both English (`en_core_web_sm`) and Japanese (`ja_core_news_sm`) spaCy models and custom recognizers. It captures PII like English emails written within Japanese sentences or mixed English/Japanese (code-switching) queries seamlessly without any loss.
    - **Query Filter (Input Guard)**: Scans input search queries. If any PII (names, email addresses, phone numbers, etc.) or configured sensitive words are detected, it either blocks the search (returns a `400 Bad Request`) or anonymizes the entities in the query based on configuration.
    - **Response Filter (Output Guard)**: Scans search result items (titles and content snippets) and automatically masks them before returning data to the AI agent.
    - **Optimized for Japanese Contexts**: Fixed single-word-boundary bugs for Japanese text structures, ensuring 12-digit Japanese My Number IDs are successfully detected even when adjacent to Japanese characters (`(?<!\d)\d{12}(?!\d)`).
    - **Custom Recognizers**: Out-of-the-box support for Japanese mobile/landline phone number formats, 12-digit Japanese My Number IDs, and custom `SENSITIVE_WORDS` matching.
    - **Self-Discipline Prompting**: Explicit warnings (Japanese/English) are embedded in the tool descriptions to proactively guide the LLM to avoid entering sensitive data.
- **Contract & Integration Tests**: OpenAPI validation tests and comprehensive mocked integration tests.

### Getting Started

#### 1. Running with Docker Compose (Recommended)

Spins up both the FastAPI application and the SearXNG instance automatically.

```bash
docker compose up --build
```

- **MCP Server**: `http://127.0.0.1:8000`
- **SearXNG Server**: `http://127.0.0.1:8080`

Verify that the MCP server is working correctly by sending a request:
```bash
curl -i http://127.0.0.1:8000/mcp
```
It should return a `406 Not Acceptable` (`"Client must accept text/event-stream"`), indicating that the server is up and listening.

> **Important Security Note:**
> You must set a secure `SEARXNG_SECRET` environment variable for SearXNG to function properly and securely.
> You can generate one using:
> ```bash
> openssl rand -hex 32
> ```
> Then, add it to your `.env` file or export it:
> ```bash
> export SEARXNG_SECRET=your_generated_secret_here
> docker compose up --build
> ```

#### 2. Running Locally

Install dependencies:
```bash
pip install -r requirements.txt
# Or
uv pip install -r requirements.txt

# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download ja_core_news_sm
```

Configure settings and run the application using `uvicorn`:
```bash
export SEARXNG_URL=http://localhost:8080
uvicorn src.main:app --reload
```

- **API Documentation**: `http://127.0.0.1:8000/docs`
- **MCP Endpoint**: `http://127.0.0.1:8000/mcp`

### Guardrail Configuration Settings

You can customize the security behaviors using environment variables or a `.env` file.

| Environment Variable | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `PII_DETECTION_ENABLED` | bool | `True` | Enable or disable the entire PII scanning process. |
| `PII_BLOCK_LEVEL` | str | `"block"` | Reaction when PII is detected in a query. Options: `block` (reject search & return 400), `anonymize` (replace with tags and proceed), `off` (do nothing). |
| `PII_MASK_RESPONSE` | bool | `True` | Mask PII found in the search results before returning them to the agent. |
| `SENSITIVE_WORDS` | list | `[]` | A list of sensitive words (comma-separated). Queries containing these will always be blocked. |
| `PII_ENTITIES` | list | `["PERSON", "EMAIL_ADDRESS", ...]` | A list of PII categories to recognize. |

### Running Tests

Tests are designed with mocks and can be executed offline without a live SearXNG service.

```bash
pip install -r requirements-dev.txt
pytest -v
```

### Live Verification & Test Results (Examples)

These are actual curl command outputs demonstrating the guardrails in action with `docker compose`.

#### 1. Health Check (`/`)
Verify that the FastAPI server is running correctly and integrated.
```bash
curl -s http://127.0.0.1:8000/ | python3 -m json.tool
```
**Response:**
```json
{
    "status": "ok"
}
```

#### 2. Safe Web Search Output Masking (`/search?q=python`)
A standard query containing no PII. Notice that when the retrieved search results contain private info (e.g., developer names or locations), the server automatically masks them using tags like `<PERSON>` or `<LOCATION>` before returning them.
```bash
curl -s "http://127.0.0.1:8000/search?q=python"
```
**Response (Excerpts):**
```json
{
  "query": "python",
  "results": [
    {
      "title": "Welcome to Python.org",
      "url": "https://www.python.org/",
      "content": "Python allows mandatory and optional arguments...",
      "engine": "google"
    },
    {
      "title": "Python",
      "url": "https://en.wikipedia.org/wiki/Python",
      "content": "<PERSON>",  // ← Developer's name automatically masked
      "engine": "wikipedia"
    },
    {
      "title": "Online Python - IDE, Editor...",
      "url": "https://www.online-python.com/",
      "content": "...development environment (<PERSON>). It is <LOCATION>, dependable...", // ← Personal names and locations masked
      "engine": "duckduckgo"
    }
  ],
  "number_of_results": 20
}
```

#### 3. Search Query Input Guardrail Blocking (`/search?q=my email is test@example.com`)
A scenario where an AI agent or a user accidentally includes a sensitive email address in the query. The MCP server safely intercepts the request and blocks it before it is dispatched to SearXNG.
```bash
curl -s "http://127.0.0.1:8000/search?q=my%20email%20is%20test@example.com"
```
**Response (400 Bad Request):**
```json
{
  "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: EMAIL_ADDRESS)"
}
```

