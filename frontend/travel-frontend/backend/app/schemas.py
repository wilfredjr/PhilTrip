from pydantic import BaseModel, Field


class TripCalculationRequest(BaseModel):
    origin: str
    destination: str
    stop_ids: list[str] = Field(default_factory=list)


class TripCalculationResponse(BaseModel):
    base_price_usd: float
    stops_price_usd: float
    toll_buffer_usd: float
    total_price_usd: float
    estimated_hours: float
    currency: str = "USD"
