from dataclasses import dataclass

from fastapi import HTTPException

from app.schemas import TripCalculationRequest, TripCalculationResponse


@dataclass(frozen=True)
class RouteConfig:
    distance_km: float
    base_price_usd: float
    toll_buffer_usd: float
    estimated_hours: float
    toll_notes: str


# Base private-transfer rates from Manila, priced in USD to shield margins from PHP volatility.
MANILA_BASE_ROUTES: dict[str, RouteConfig] = {
    "tagaytay": RouteConfig(
        distance_km=65.0,
        base_price_usd=75.0,
        toll_buffer_usd=15.0,
        estimated_hours=2.5,
        toll_notes="SLEX / STAR tolls plus southbound driver return-trip fuel allowance",
    ),
    "baguio": RouteConfig(
        distance_km=250.0,
        base_price_usd=190.0,
        toll_buffer_usd=35.0,
        estimated_hours=6.0,
        toll_notes="NLEX / TPLEX tolls plus long-haul driver return-trip fuel allowance",
    ),
    "clark": RouteConfig(
        distance_km=90.0,
        base_price_usd=85.0,
        toll_buffer_usd=18.0,
        estimated_hours=2.5,
        toll_notes="NLEX tolls plus northbound driver return-trip fuel allowance",
    ),
    "anilao": RouteConfig(
        distance_km=120.0,
        base_price_usd=110.0,
        toll_buffer_usd=15.0,
        estimated_hours=3.0,
        toll_notes="SLEX / STAR tolls plus Batangas corridor driver return-trip fuel allowance",
    ),
}

# Sightseeing add-ons are also quoted in USD for the same FX-protection rationale.
SIGHTSEEING_STOP_FEES_USD: dict[str, float] = {
    "nuvali": 12.0,
    "taal": 28.0,
    "sanguillermo": 15.0,
}

# Accept legacy frontend stop identifiers while canonicalizing to short keys.
STOP_ID_ALIASES: dict[str, str] = {
    "nuvali-eco-park": "nuvali",
    "taal-heritage-town": "taal",
    "san-guillermo-church": "sanguillermo",
}

SUPPORTED_ORIGINS = {"manila", "manila-ncr"}


def normalize_stop_id(stop_id: str) -> str:
    cleaned = stop_id.strip().lower()
    return STOP_ID_ALIASES.get(cleaned, cleaned)


def calculate_trip_price(request: TripCalculationRequest) -> TripCalculationResponse:
    origin = request.origin.strip().lower()
    destination = request.destination.strip().lower()

    if origin not in SUPPORTED_ORIGINS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported origin '{request.origin}'. Routes are currently available from Manila only.",
        )

    route = MANILA_BASE_ROUTES.get(destination)
    if route is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported destination '{request.destination}'.",
        )

    base_price_usd = route.base_price_usd

    stops_price_usd = 0.0
    for raw_stop_id in request.stop_ids:
        stop_id = normalize_stop_id(raw_stop_id)
        stop_fee = SIGHTSEEING_STOP_FEES_USD.get(stop_id)
        if stop_fee is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sightseeing stop '{raw_stop_id}'.",
            )
        stops_price_usd += stop_fee

    # Toll and driver-return buffers are fixed USD overheads per corridor.
    # They are intentionally denominated in USD (not PHP) so operational profit
    # margins remain stable even when local toll receipts and fuel costs swing
    # with peso exchange-rate volatility.
    toll_buffer_usd = route.toll_buffer_usd

    total_price_usd = base_price_usd + stops_price_usd + toll_buffer_usd

    return TripCalculationResponse(
        base_price_usd=round(base_price_usd, 2),
        stops_price_usd=round(stops_price_usd, 2),
        toll_buffer_usd=round(toll_buffer_usd, 2),
        total_price_usd=round(total_price_usd, 2),
        estimated_hours=route.estimated_hours,
    )
