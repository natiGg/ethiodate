import aiohttp
import logging

async def reverse_geocode(lat: float, lon: float) -> tuple[str, str]:
    """
    Takes a latitude and longitude and returns a tuple of (City, Country).
    Uses the free Nominatim OpenStreetMap API.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
    headers = {
        "User-Agent": "EthiopianDatingBot/1.0 (Contact: admin@example.com)"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    address = data.get("address", {})
                    
                    # Extract city-like feature
                    city = address.get("city") or address.get("town") or address.get("village") or address.get("county") or "Unknown City"
                    country = address.get("country", "Unknown Country")
                    
                    return city, country
                else:
                    logging.error(f"Geocoding failed with status {response.status}")
    except Exception as e:
        logging.error(f"Geocoding exception: {e}")
        
    return "Unknown City", "Unknown Country"
