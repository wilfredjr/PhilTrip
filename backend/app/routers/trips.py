from fastapi import APIRouter

from app.pricing import calculate_trip_price
from app.schemas import TripCalculationRequest, TripCalculationResponse

router = APIRouter(prefix="/api", tags=["trips"])


@router.post("/calculate-trip", response_model=TripCalculationResponse)
def calculate_trip(request: TripCalculationRequest) -> TripCalculationResponse:
    return calculate_trip_price(request)
