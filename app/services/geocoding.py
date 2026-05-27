import googlemaps
from typing import List
import time
from ..models.schemas import Location

def geocode_addresses(addresses: List[str], api_key: str) -> tuple[List[Location], List[str]]:
    """
    Geocodes a list of address strings using Google Maps API.
    Returns a list of Location objects and a list of failed address strings.
    (Stateless version - no DB caching)
    """
    try:
        gmaps = googlemaps.Client(key=api_key, timeout=10)
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        raise e

    geocoded_locations = []
    failed_addresses = []
    
    # Identify what needs API call (all of them in stateless mode)
    uncached_addresses = addresses
            
    for address in uncached_addresses:
        try:
            # Make the API call
            geocode_result = gmaps.geocode(address)

            if geocode_result:
                # Extract the relevant data
                lat = geocode_result[0]['geometry']['location']['lat']
                lng = geocode_result[0]['geometry']['location']['lng']
                formatted_address = geocode_result[0]['formatted_address']
                
                loc_obj = Location(
                    original_address=address,
                    latitude=lat,
                    longitude=lng,
                    formatted_address=formatted_address
                )
                geocoded_locations.append(loc_obj)
            else:
                failed_addresses.append(address)
            
            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            # Check for API specific errors if using the client library
            print(f"Error geocoding {address}: {e}")
            failed_addresses.append(address)
            
            # If it's a critical auth error, re-raise to stop the worker
            if "Request Denied" in str(e) or "Invalid Key" in str(e):
                raise ValueError(f"CRITICAL GEOCODING ERROR: {e}")

    return geocoded_locations, failed_addresses
