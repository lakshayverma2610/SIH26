import logging
from urllib.parse import urlencode


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_google_maps_url(latitude, longitude):
    """Create a Google Maps directions URL for a hotspot."""
    params = {
        "api": "1",
        "destination": f"{latitude},{longitude}"
    }

    return "https://www.google.com/maps/dir/?" + urlencode(params)


def dispatch_patrol_unit(hotspot_data):
    """
    Simulate dispatching a police patrol unit.

    Expected hotspot_data:
    {
        "latitude": 28.6304,
        "longitude": 77.2773,
        "location_name": "Example Hotspot"
    }
    """

    latitude = hotspot_data.get("latitude")
    longitude = hotspot_data.get("longitude")
    location_name = hotspot_data.get("location_name", "Unknown location")

    if latitude is None or longitude is None:
        raise ValueError("Hotspot must contain latitude and longitude.")

    maps_url = create_google_maps_url(latitude, longitude)

    alert = {
        "status": "PATROL_DISPATCHED",
        "location": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "maps_url": maps_url,
        "message": (
            f"Patrol unit dispatched to {location_name}. "
            f"Navigate using: {maps_url}"
        )
    }

    logging.info(alert["message"])

    return alert


if __name__ == "__main__":
    sample_hotspot = {
        "latitude": 28.6304,
        "longitude": 77.2773,
        "location_name": "Sample ATM Hotspot"
    }

    result = dispatch_patrol_unit(sample_hotspot)

    print("\nDispatch Result:")
    print(result)