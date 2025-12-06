import asyncio
from typing import Any, List, Optional, Tuple

from agents import function_tool
from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Timeout for geocoding operations
TIMEOUT_SECONDS = 30

@function_tool
async def get_coordinates_by_address(address: str) -> Tuple[float, float]:
    """Get the coordinates of an address using the ArcGIS geocoder."""
    try:
        geolocator = ArcGIS(timeout=TIMEOUT_SECONDS)
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except GeocoderTimedOut:
        return None
    except GeocoderServiceError:
        return None

@function_tool
async def get_address_by_coordinates(latitude: float, longitude: float) -> str:
    """Get the address of a set of coordinates using the ArcGIS geocoder."""
    try:
        geolocator = ArcGIS(timeout=TIMEOUT_SECONDS)
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location:
            return location.address
        else:
            return None
    except GeocoderTimedOut:
        return None
    except GeocoderServiceError:
        return None

# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

import json

async def main():
    address = "Coit Tower, San Francisco, CA"
    
    # Call the function_tool via on_invoke_tool method
    # Signature: on_invoke_tool(ctx: ToolContext, input: str)
    result = await get_coordinates_by_address.on_invoke_tool(
        ctx=None,
        input=json.dumps({"address": address})
    )
    print(f"Coordinates: {result}")
    
    # Parse the result (it returns a string representation)
    # For this example, let's use known coordinates for Coit Tower
    lat, lon = 37.8024, -122.4058
    
    result = await get_address_by_coordinates.on_invoke_tool(
        ctx=None,
        input=json.dumps({"latitude": lat, "longitude": lon})
    )
    print(f"Address: {result}")
    
if __name__ == "__main__":
    asyncio.run(main())