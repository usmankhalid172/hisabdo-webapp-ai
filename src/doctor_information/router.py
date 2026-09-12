from fastapi import APIRouter, Depends

from ..schemas import (
    DoctorInformationRequest,
    DoctorInformationResponse,
)
from ..security import require_internal_token
from .service import DoctorInformationService


router = APIRouter(
    prefix="/api/v1",
    tags=["doctor-information"],
    dependencies=[Depends(require_internal_token)],
)


service = DoctorInformationService()


@router.post(
    "/doctor-information",
    response_model=DoctorInformationResponse,
    summary="Answer questions using approved doctor information",
)
def doctor_information(
    payload: DoctorInformationRequest,
) -> DoctorInformationResponse:
    result = service.answer(payload.question)

    return DoctorInformationResponse(
        answer=result["answer"],
        conversation_id=payload.conversation_id,
        source=result["source"],
        retrieved=result["retrieved"],
        retrieved_doctors=result["retrieved_doctors"],
        tokens_used=result["tokens_used"],
    )