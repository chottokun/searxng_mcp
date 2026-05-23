from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from src.schemas import ResultSet
from src.services.searxng_service import SearxngService, get_searxng_service
from src.services.pii_service import PiiService, get_pii_service

router = APIRouter()

# ツールとしてAIが参照するdescriptionを強化する
SEARCH_TOOL_DESCRIPTION = (
    "設定された SearXNG インスタンスを使用して検索を実行します。\n\n"
    "【重要 / IMPORTANT】\n"
    "個人情報（氏名、住所、電話番号、メールアドレス、マイナンバー、クレジットカード番号など）や、"
    "機密性の高い言葉（社外秘や秘密プロジェクト名など）は、検索クエリに絶対に含めないでください。\n"
    "DO NOT include any personally identifiable information (PII) or sensitive/confidential words in your search query. "
    "Queries containing PII or sensitive words will be blocked or anonymized."
)

@router.get(
    "/search",
    operation_id="search_searxng",
    response_model=ResultSet,
    summary="SearXNG を使用して検索を実行します（個人情報・機密情報の送信は禁止されています）",
    description=SEARCH_TOOL_DESCRIPTION,
    tags=["Search"]
)
async def search(
    q: str = Query(
        ...,
        description=(
            "検索クエリ文字列。個人情報（氏名、住所、メール、電話番号等）や機密ワードは絶対に含めないでください。 / "
            "The search query string. DO NOT include any PII or sensitive/confidential words."
        )
    ),
    categories: Optional[str] = Query(None, description="カンマ区切りの検索カテゴリ (例: 'news,files') / Comma-separated list of search categories."),
    time_range: Optional[str] = Query(None, description="検索期間 (例: 'day', 'week', 'month') / Time range for the search."),
    searxng_service: SearxngService = Depends(get_searxng_service),
    pii_service: PiiService = Depends(get_pii_service)
):
    """
    設定された SearXNG インスタンスを使用して検索を実行します。
    
    検索クエリの検査が最初に行われ、個人情報や機密性の高い情報が含まれる場合は
    ブロック（400エラー）またはプレースホルダーへの匿名化が適用されます。
    また、検索結果に個人情報が含まれている場合、返却前にマスキングされます。
    """
    # 1. 検索クエリの検査と匿名化・ブロック
    try:
        inspected_q = pii_service.inspect_query(q)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. 検索の実行
    results = await searxng_service.search(q=inspected_q, categories=categories, time_range=time_range)

    # 3. 検索結果のマスキング
    safe_results = pii_service.mask_results(results)

    return safe_results
