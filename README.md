# SearXNG MCP Server

FastAPI-based server providing a search endpoint compatible with the Model Context Protocol (MCP). It features robust data guardrails using Microsoft Presidio to prevent external information leaks via search queries and to protect user privacy by masking retrieved results within the AI context.

Model Context Protocol (MCP) に準拠した検索機能を提供する FastAPI ベースのサーバーです。AIエージェントが外部へ機密情報を送信してしまう「外部情報流出」を防ぐためのクエリフィルタと、検索された公開データからAIコンテキストへの個人情報混入を防ぐ出力フィルタという二重のデータガードレールを実装しています。

---

## 目次 / Table of Contents
1. [日本語版 / Japanese Version](#日本語版---japanese-version)
2. [English Version](#english-version)

---

## 日本語版 - Japanese Version

このプロジェクトは、AIエージェント（Claude Desktopなど）がSearXNGを介してWeb検索を行うためのブリッジです。**AIエージェントが外部（インターネット上）へ機密情報を送信してしまう「外部情報流出リスク」を未然に防ぐ強力な入力防御**と、検索された公開データから**AIエージェントのコンテキスト（チャットログ等）へ他者の個人情報が無用に蓄積されるのを防ぐ出力プライバシー保護**の二重のガードレールが施されています。

### 主な機能

- **FastAPIバックエンド**: 高速かつ非同期対応のモダンなAPIサーバー。
- **MCP統合**: `fastapi-mcp` を使用して、検索エンドポイントをAIエージェント用のMCPツールとして公開。
- **データガードレール（情報流出防止・プライバシー保護機能）**: 
  - **多言語インテリジェントマージ解析**: 英語（`en_core_web_sm`）と日本語（`ja_core_news_sm`）の両方のspaCy言語モデルおよび認識器を同時に実行・マージする高度な解析を実装。日本語文章内に含まれる英語メールアドレスや、日英混在したクエリでも漏れなく確実に個人情報（PII）を検出します。
  - **クエリフィルタ（入力防御 - 最重要セキュリティ）**: AIエージェントが誤って内部の機密データや個人情報（APIキー、メール、電話番号、クレジットカード等）を検索クエリとして**外部へ送信（流出）するのを完全にブロック**（400 Bad Request）、またはプレースホルダーに匿名化します。
  - **レスポンスフィルタ（出力防御 - プライバシー＆コンプライアンス）**: 検索された結果（タイトルやコンテンツスニペット）に個人情報が含まれる場合、AIのコンテキストや保存ログに不要な個人情報が取り込まれるのを防ぐため、自動マスキング（`<PERSON>` 等のプレースホルダーに変換）を施します。
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

### MCPクライアント（Claude Desktop）への登録方法

AIエージェントのクライアントでこのSearXNG MCPツールを利用するには、設定ファイル（通常は `~/.config/Claude/claude_desktop_config.json`）に以下のいずれかの設定を追記します。

#### A. Stdioトランスポート（推奨・直接起動）
クライアントがMCPサーバーのコマンドを自動的に立ち上げて標準入出力でやり取りする最も一般的な設定です。
* **uv (Pythonパッケージマネージャ) を使用して直接実行する場合:**
  ```json
  {
    "mcpServers": {
      "searxng-mcp": {
        "command": "uv",
        "args": [
          "run",
          "--package",
          "fastapi-mcp",
          "mcp",
          "run",
          "/absolute/path/to/project/searxng_mcp/src/main.py"
        ],
        "env": {
          "SEARXNG_URL": "http://localhost:8080",
          "PII_BLOCK_LEVEL": "block",
          "PII_MASK_RESPONSE": "false"
        }
      }
    }
  }
  ```
  *(注: `/absolute/path/to/project/` の部分は、プロジェクトをクローンした実際のローカル絶対パスに置き換えてください。)*

#### B. SSE (HTTP) トランスポート（バックグラウンド起動したサーバーに接続）
本サーバーをバックグラウンド（ポート8000）で起動しておき、クライアントがHTTP SSE経由でネットワーク接続する設定です。
```json
{
  "mcpServers": {
    "searxng-mcp-sse": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```


### 個人情報保護（PII）設定一覧

`.env` ファイルまたは環境変数経由で以下の設定をカスタマイズ可能です。

| 環境変数名 | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `PII_DETECTION_ENABLED` | bool | `True` | 個人情報および機密ワードの検出処理自体を有効にするか。 |
| `PII_BLOCK_LEVEL` | str | `"block"` | PII検出時の動作。`block`（検索拒否・エラー返却）、`anonymize`（匿名化して検索続行）、`off`（無効）。 |
| `PII_MASK_RESPONSE` | bool | `False` | 検索結果（タイトル、コンテンツ）内の個人情報をAIに返す前にマスキングするか。（デフォルトは検索の正確性を損なわないためオフ） |
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

### 実際の検証・テスト結果とオプション設定別の具体例

`docker compose` を用いて実際に SearXNG および MCP サーバーをローカルで起動し、接続テストを行った際の実機結果です。

このプロジェクトでは、**「外部への意図しない個人情報送信（クエリ流出）を防ぐこと」を最も重大なセキュリティリスク**と捉えています。そのため、クエリフィルタ（入力防御）は初期状態で強力に有効化されている一方、検索効率と正確性を落とさないために検索結果（レスポンス）のマスキングは初期状態でオフ（`False`）に設定されています。

---

#### 1. 初期状態（デフォルト設定）での検証結果
初期状態では、以下の環境変数が適用されています：
* `PII_BLOCK_LEVEL="block"` (クエリ内の個人情報は送信せず完全にブロック)
* `PII_MASK_RESPONSE=False` (検索結果に含まれる公開データはそのまま正確にAIへ受け渡す)

##### A. 通常の検索動作 (`/search?q=python`)
検索キーワードに個人情報を含まない安全なクエリです。検索結果のコンテンツに他人の氏名などが含まれていても、デフォルトではマスキングされず正確な公開情報がそのまま取得されます。
* **リクエスト:**
  ```bash
  curl -s "http://127.0.0.1:8000/search?q=python"
  ```
* **実際のレスポンス (一部抜粋):**
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
        "title": "Python (programming language) - Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "content": "Guido van Rossum began working on Python in the late 1980s as a successor...", // ← デフォルトでは実名「Guido van Rossum」が正確にそのまま出力されます
        "engine": "wikipedia"
      }
    ],
    "number_of_results": 20
  }
  ```

##### B. 個人情報の外部送信ブロック (`/search?q=my email is test@example.com`)
ユーザーやAIエージェントが、クエリ内に誤ってメールアドレスなどの機密情報を送信してしまった場合のブロック動作例です。SearXNG にリクエストが送信される前に、サーバー側で安全に遮断されます。
* **リクエスト:**
  ```bash
  curl -s "http://127.0.0.1:8000/search?q=my%20email%20is%20test@example.com"
  ```
* **実際のレスポンス (400 Bad Request):**
  ```json
  {
    "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: EMAIL_ADDRESS)"
  }
  ```

---

#### 2. オプション設定を変更した際の挙動一覧

環境変数や `.env` の設定を変更することで、各種ガードレールの振る舞いをユースケースに合わせて調整できます。

##### A. クエリブロックモード (`PII_BLOCK_LEVEL="block"` - デフォルト)
クエリ内に個人情報やAPIキー、クレジットカード番号などが検出された場合、検索処理自体を完全に拒否します。セキュリティ最優先の安全な環境に適しています。
* **設定:** `PII_BLOCK_LEVEL="block"`
* **入力クエリ:** `Find sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM` (OpenAIのAPIキーを含むクエリ)
* **レスポンス (400 Bad Request):**
  ```json
  {
    "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: API_KEY)"
  }
  ```

##### B. クエリ匿名化モード (`PII_BLOCK_LEVEL="anonymize"`)
クエリ内の個人情報を検出して自動的にプレースホルダー（タグ）に置換（匿名化）した上で、検索を安全に続行します。利便性と安全性のバランスを取る場合に適しています。
* **設定:** `PII_BLOCK_LEVEL="anonymize"`
* **入力クエリ:** `Contact john.doe@example.com`
* **実際にSearXNGへ送信されるクエリ:** `Contact [EMAIL_ADDRESS]`
* **レスポンス:** 個人情報自体は伏せられた状態で検索が実行され、安全に検索結果が返却されます。

##### C. 検索結果マスキング有効化 (`PII_MASK_RESPONSE=True`)
チャット履歴ログの保護や、AIコンテキストに不要な個人情報が蓄積されることを防ぐため、検索結果のコンテンツに含まれる個人情報（人名、電話番号、メールなど）をAIエージェントに渡す前にマスキングします。
* **設定:** `PII_MASK_RESPONSE=True`
* **入力クエリ:** `python`
* **実際のレスポンス (一部抜粋):**
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
    ],
    "number_of_results": 20
  }
  ```

#### 3. MCPプロトコル（JSON-RPC 2.0）接続とツール登録の検証事例

MCP クライアント（AIエージェント）との接続に必要な **JSON-RPC 2.0 準拠のハンドシェイク** および **ツールリスト取得** の実際の動作検証ログです。

##### A. 初期化シーケンスの実行 (`initialize` リクエスト)
クライアントから送られた初期化要求に対し、MCP規格に沿ったプロトコルバージョンとサーバー能力（Capabilities）を正確に応答します。
* **リクエスト (JSON-RPC 2.0):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "mcp-test-client",
        "version": "1.0.0"
      }
    }
  }
  ```
* **実際の返答内容:**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2024-11-05",
      "capabilities": {
        "experimental": {},
        "tools": {
          "listChanged": false
        }
      },
      "serverInfo": {
        "name": "SearXNG MCP Server",
        "version": "A FastAPI server providing a tool for searching with SearXNG, compatible with fastapi-mcp."
      }
    }
  }
  ```

##### B. ツール定義の取得 (`tools/list` リクエスト)
初期化の完了後、AIエージェントが使用可能なツールリストを取得するリクエストに対し、私たちが実装した `search_searxng` ツールの仕様（名前、説明、スキーマ）が正確に返却されます。
* **リクエスト (JSON-RPC 2.0):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }
  ```
* **実際の返答内容:**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
      "tools": [
        {
          "name": "search_searxng",
          "description": "SearXNG を使用して検索を実行します（個人情報・機密情報の送信は禁止されています）...",
          "inputSchema": {
            "type": "object",
            "properties": {
              "q": {
                "type": "string",
                "description": "検索クエリ文字列。個人情報（氏名、住所、メール、電話番号等）や機密ワードは絶対に含めないでください。 / The search query string. DO NOT include any PII or sensitive/confidential words."
              },
              "categories": {
                "type": "string",
                "description": "カンマ区切りの検索カテゴリ (例: 'news,files') / Comma-separated list of search categories."
              },
              "time_range": {
                "type": "string",
                "description": "検索期間 (例: 'day', 'week', 'month') / Time range for the search."
              }
            },
            "required": [
              "q"
            ]
          }
        }
      ]
    }
  }
  ```
  *(注: このツール定義の `description` には、AIエージェント自身が個人情報の送信を自律的に抑止するためのプロンプト指示が自動的に埋め込まれています。)*




---

## English Version

This project acts as a bridge allowing AI agents (such as Claude) to perform web searches using a local or remote SearXNG instance. It is engineered with a dual data-guardrail system: **a robust Query Input Filter to prevent the critical risk of transmitting internal sensitive data to the external web**, and a **Response Output Filter to preserve user privacy and maintain compliance** by sanitizing public search results before they are loaded into the AI's active context (and logs).

### Features

- **FastAPI Backend**: A modern, asynchronous high-performance web framework.
- **MCP Integration**: Exposes the search endpoint as an MCP-compatible tool using the `fastapi-mcp` library.
  - **Data Guardrails (Security & Privacy Compliance)**:
    - **Multilingual Intelligent Merging**: Concurrently runs and merges results from both English (`en_core_web_sm`) and Japanese (`ja_core_news_sm`) spaCy models and custom recognizers. It captures PII like English emails written within Japanese sentences or mixed English/Japanese (code-switching) queries seamlessly without any loss.
    - **Query Filter (Input Guard - Crucial Security)**: Scans input search queries. If any internal PII (API keys, email addresses, phone numbers, credit card numbers, etc.) or configured sensitive words are detected, it **blocks the query entirely** (returns a `400 Bad Request`) or anonymizes the entities to **prevent accidental leaks to the external web**.
    - **Response Filter (Output Guard - Privacy & Compliance)**: Scans retrieved search results (titles and content snippets) and automatically masks them with generic tags (e.g., `<PERSON>`) before returning them to the agent to avoid cluttering chat histories or active context with third-party private data.
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

### MCP Client Integration (e.g. Claude Desktop)

To register and use this SearXNG MCP tool in your AI agent workspace, append the following configurations to your client config file (usually located at `~/.config/Claude/claude_desktop_config.json`).

#### A. Stdio Transport (Recommended - Auto Startup)
The client spawns the MCP process directly and communicates via standard input/output.
* **Using uv (Python package runner) to start the server:**
  ```json
  {
    "mcpServers": {
      "searxng-mcp": {
        "command": "uv",
        "args": [
          "run",
          "--package",
          "fastapi-mcp",
          "mcp",
          "run",
          "/absolute/path/to/project/searxng_mcp/src/main.py"
        ],
        "env": {
          "SEARXNG_URL": "http://localhost:8080",
          "PII_BLOCK_LEVEL": "block",
          "PII_MASK_RESPONSE": "false"
        }
      }
    }
  }
  ```
  *(Note: Replace `/absolute/path/to/project/` with the actual absolute path to where you cloned the project on your machine.)*

#### B. SSE (HTTP) Transport (Connects to a Running Server)
Connects to the server running in the background (e.g., listening on port 8000) over network HTTP Server-Sent Events.
```json
{
  "mcpServers": {
    "searxng-mcp-sse": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```


### Guardrail Configuration Settings

You can customize the security behaviors using environment variables or a `.env` file.

| Environment Variable | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `PII_DETECTION_ENABLED` | bool | `True` | Enable or disable the entire PII scanning process. |
| `PII_BLOCK_LEVEL` | str | `"block"` | Reaction when PII is detected in a query. Options: `block` (reject search & return 400), `anonymize` (replace with tags and proceed), `off` (do nothing). |
| `PII_MASK_RESPONSE` | bool | `False` | Mask PII found in the search results before returning them to the agent. (Default: False, to preserve accuracy of retrieved public web data) |
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

In this project, **"leaking sensitive data via external search queries" is considered the primary security risk**. Therefore, the query input guardrail is fully activated by default, while response masking (output guard) is disabled (`False`) by default to ensure search accuracy and efficiency.

---

#### 1. Default Behavior (Out-of-the-box Settings)
Under default configuration, the following environment variables apply:
* `PII_BLOCK_LEVEL="block"` (Block queries containing PII entirely to prevent external leakage)
* `PII_MASK_RESPONSE=False` (Pass retrieved search data to the AI agent intact)

##### A. Standard Safe Web Search (`/search?q=python`)
A standard safe query. When retrieved results contain third-party public names or locations, they are passed as raw text without being masked, keeping search data accurate.
* **Request:**
  ```bash
  curl -s "http://127.0.0.1:8000/search?q=python"
  ```
* **Actual Response (Excerpt):**
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
        "title": "Python (programming language) - Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "content": "Guido van Rossum began working on Python in the late 1980s as a successor...", // ← Real name "Guido van Rossum" is accurately preserved by default
        "engine": "wikipedia"
      }
    ],
    "number_of_results": 20
  }
  ```

##### B. Search Query Input Guardrail Blocking (`/search?q=my email is test@example.com`)
A scenario where an AI agent or a user accidentally includes a private email address in the query. The MCP server safely intercepts the request and blocks it before it is dispatched to the external SearXNG instance.
* **Request:**
  ```bash
  curl -s "http://127.0.0.1:8000/search?q=my%20email%20is%20test@example.com"
  ```
* **Actual Response (400 Bad Request):**
  ```json
  {
    "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: EMAIL_ADDRESS)"
  }
  ```

---

#### 2. Guardrail Customization Behavior Examples

You can customize the guardrail behavior by changing environment variables or `.env` configuration (e.g., `PII_BLOCK_LEVEL` or `PII_MASK_RESPONSE`).

##### A. Query Block Mode (`PII_BLOCK_LEVEL="block"` - Default)
Rejects search processing entirely and returns an HTTP error if PII is detected in a query. Best for strict security-first environments.
* **Setting:** `PII_BLOCK_LEVEL="block"`
* **Input Query:** `Find sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLM` (Contains an OpenAI API Key)
* **Response (400 Bad Request):**
  ```json
  {
    "detail": "送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: API_KEY)"
  }
  ```

##### B. Query Anonymization Mode (`PII_BLOCK_LEVEL="anonymize"`)
Automatically replaces private data with placeholder tags and safely proceeds with the search. Ideal for balancing utility and security.
* **Setting:** `PII_BLOCK_LEVEL="anonymize"`
* **Input Query:** `Contact john.doe@example.com`
* **Anonymized Query Sent to SearXNG:** `Contact [EMAIL_ADDRESS]`
* **Response:** Query runs safely with anonymized tokens, and normal results are returned.

##### C. Response Masking Enabled (`PII_MASK_RESPONSE=True`)
Masks private data (names, phone numbers, emails, etc.) found in the search results before returning them to the agent. Helps protect chat logs or active context from collecting unrelated third-party private data.
* **Setting:** `PII_MASK_RESPONSE=True`
* **Search Query:** `python`
* **Response (Masking Enabled):**
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
        "title": "Python (programming language) - Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "content": "<PERSON> began working on Python in the late 1980s as a successor...", // ← Developer's real name is masked as `<PERSON>`
        "engine": "wikipedia"
      }
    ],
    "number_of_results": 20
  }
  ```

#### 3. MCP Protocol (JSON-RPC 2.0) Handshake & Tool Discovery Verification

Actual verification logs proving compliance with the **JSON-RPC 2.0 specification** required to handshake and discover tools on the MCP client.

##### A. Session Initialization (`initialize` Request)
Responds with the exact protocol version and server capabilities matching the official Model Context Protocol (MCP) spec upon receiving a client handshake.
* **Request (JSON-RPC 2.0):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "mcp-test-client",
        "version": "1.0.0"
      }
    }
  }
  ```
* **Actual Response:**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2024-11-05",
      "capabilities": {
        "experimental": {},
        "tools": {
          "listChanged": false
        }
      },
      "serverInfo": {
        "name": "SearXNG MCP Server",
        "version": "A FastAPI server providing a tool for searching with SearXNG, compatible with fastapi-mcp."
      }
    }
  }
  ```

##### B. Tool Discovery (`tools/list` Request)
Returns the precise schema, parameters, and descriptions for the `search_searxng` tool, enabling seamless automatic integration on MCP clients (like Claude Desktop).
* **Request (JSON-RPC 2.0):**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }
  ```
* **Actual Response:**
  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
      "tools": [
        {
          "name": "search_searxng",
          "description": "SearXNG を使用して検索を実行します（個人情報・機密情報の送信は禁止されています）...",
          "inputSchema": {
            "type": "object",
            "properties": {
              "q": {
                "type": "string",
                "description": "検索クエリ文字列。個人情報（氏名、住所、メール、電話番号等）や機密ワードは絶対に含めないでください。 / The search query string. DO NOT include any PII or sensitive/confidential words."
              },
              "categories": {
                "type": "string",
                "description": "カンマ区切りの検索カテゴリ (例: 'news,files') / Comma-separated list of search categories."
              },
              "time_range": {
                "type": "string",
                "description": "検索期間 (例: 'day', 'week', 'month') / Time range for the search."
              }
            },
            "required": [
              "q"
            ]
          }
        }
      ]
    }
  }
  ```


