from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Enable CORS so your Next.js frontend can connect smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. HARDCODED TRAVEL DATA (IN-MEMORY TRUTH)
# Base structural routes originating from Manila
ROUTES_REGISTRY = {
    "Tagaytay, Cavite": {
        "base_price_usd": 75.00,
        "estimated_hours": 2.0,
        "toll_buffer_usd": 8.00  # SLEX & Cavitex
    },
    "Baguio City, Benguet": {
        "base_price_usd": 190.00,
        "estimated_hours": 5.5,
        "toll_buffer_usd": 22.00 # NLEX, SCTEX, TPLEX
    },
    "Anilao Reefs, Batangas": {
        "base_price_usd": 110.00,
        "estimated_hours": 3.0,
        "toll_buffer_usd": 12.00 # SLEX & STAR Tollway
    }
}

# Optional tourist side-trips map
SIGHTSEEING_STOPS_REGISTRY = {
    "nuvali": {
        "name": "Nuvali Eco-Park",
        "add_on_price_usd": 12.00,
        "valid_destinations": ["Tagaytay, Cavite", "Anilao Reefs, Batangas"]
    },
    "taal": {
        "name": "Taal Heritage Town",
        "add_on_price_usd": 28.00,
        "valid_destinations": ["Tagaytay, Cavite"]
    },
    "sanguillermo": {
        "name": "San Guillermo Historical Church",
        "add_on_price_usd": 15.00,
        "valid_destinations": ["Baguio City, Benguet"]
    }
}

# 2. PYDANTIC VALIDATION SCHEMAS
class TripCalculationRequest(BaseModel):
    destination: str
    selected_stop_ids: List[str] = []

# 3. ENDPOINTS
@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "in-memory-mvp"}

@app.post("/api/calculate-trip")
def calculate_trip(request: TripCalculationRequest):
    # Verify the requested destination exists in our registry
    if request.destination not in ROUTES_REGISTRY:
        raise HTTPException(status_code=404, detail="Destination route not supported yet.")
        
    route_info = ROUTES_REGISTRY[request.destination]
    base_price = route_info["base_price_usd"]
    toll_buffer = route_info["toll_buffer_usd"]
    
    # Loop over user-selected sightseeing stops and sum up their USD values
    stops_total_price = 0.0
    processed_stops_names = []
    
    for stop_id in request.selected_stop_ids:
        if stop_id in SIGHTSEEING_STOPS_REGISTRY:
            stop_data = SIGHTSEEING_STOPS_REGISTRY[stop_id]
            
            # Double check if this stop is physically on the way to that province
            if request.destination in stop_data["valid_destinations"]:
                stops_total_price += stop_data["add_on_price_usd"]
                processed_stops_names.append(stop_data["name"])
                
    # final math addition logic
    grand_total_usd = base_price + toll_buffer + stops_total_price
    
    return {
        "destination": request.destination,
        "base_price_usd": round(base_price, 2),
        "toll_buffer_usd": round(toll_buffer, 2),
        "stops_price_usd": round(stops_total_price, 2),
        "total_price_usd": round(grand_total_usd, 2),
        "estimated_hours": route_info["estimated_hours"],
        "included_stops": processed_stops_names
    }
