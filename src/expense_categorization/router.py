from fastapi import APIRouter, Depends

from ..schemas import BatchCategorizeRequest, BatchCategorizeResponse, CategorizeRequest, CategorizeResponse
from ..security import require_internal_token
from .service import categorize

router = APIRouter(
    prefix="/api/v1",
    tags=["expense-categorization"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/categorize", response_model=CategorizeResponse, summary="Predict an expense category")
def categorize_expense(payload: CategorizeRequest) -> CategorizeResponse:
    return categorize(payload)


@router.post(
    "/categorize/batch",
    response_model=BatchCategorizeResponse,
    summary="(Planned) Bulk categorization for statement imports",
)
def categorize_batch(payload: BatchCategorizeRequest) -> BatchCategorizeResponse:
    results = [categorize(item) for item in payload.items]
    return BatchCategorizeResponse(results=results)
