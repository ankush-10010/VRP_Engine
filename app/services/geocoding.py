import googlemaps
from typing import List
import time
from ..models.schemas import Location

def geocode_addresses(addresses: List[str], api_key: str) -> tuple[List[Location], List[str]]:
    """
    Geocodes a list of address strings using Google Maps API.
    Returns a list of Location objects and a list of failed address strings.
    """
    # Function scope imports to avoid circular dependency
    from ..db.session import SessionLocal
    from ..models.db_models import GeocodedLocation as LocationDB
    from sqlalchemy.exc import SQLAlchemyError
    
    db = SessionLocal()
    
    try:
        gmaps = googlemaps.Client(key=api_key, timeout=10)
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        db.close()
        raise e

    geocoded_locations = []
    failed_addresses = []
    
    # 1. Check Cache
    uncached_addresses = []
    cache_map = {}
    
    try:
        # Batch query for existing addresses
        cached_records = db.query(LocationDB).filter(LocationDB.original_address.in_(addresses)).all()
        for record in cached_records:
            loc = Location(
                original_address=record.original_address,
                latitude=record.latitude,
                longitude=record.longitude,
                formatted_address=record.formatted_address
            )
            geocoded_locations.append(loc)
            cache_map[record.original_address] = loc
            
    except Exception as e:
        print(f"DB Read Error: {e}")
        # Proceed as if no cache
    
    # Identify what needs API call
    for addr in addresses:
        if addr not in cache_map:
            uncached_addresses.append(addr)
            
    # 2. Call API for Uncached
    new_db_records = []
    
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
                
                # Prepare for DB persistence
                new_db_records.append(LocationDB(
                    original_address=address,
                    formatted_address=formatted_address,
                    latitude=lat,
                    longitude=lng
                ))
            else:
                failed_addresses.append(address)
            
            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            # Check for API specific errors if using the client library
            # (Note: googlemaps python client raises standard exceptions, but we can catch more details)
            print(f"Error geocoding {address}: {e}")
            failed_addresses.append(address)
            
            # If it's a critical auth error, re-raise to stop the worker
            if "Request Denied" in str(e) or "Invalid Key" in str(e):
                db.close()
                raise ValueError(f"CRITICAL GEOCODING ERROR: {e}")

    # 3. Save New Records
    if new_db_records:
        try:
            db.bulk_save_objects(new_db_records)
            db.commit()
        except Exception as e:
            print(f"DB Write Error: {e}")
            db.rollback()
    
    db.close()
    return geocoded_locations, failed_addresses
