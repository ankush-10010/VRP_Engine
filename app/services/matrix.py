import requests
import time
import math
from typing import List, Tuple
from ..models.schemas import Location

def get_real_travel_time(lat1, lon1, lat2, lon2, departure_timestamp, api_key) -> Tuple[int, float]:
    """
    Gets the real-world travel time in MINUTES from the Google Maps Directions API.
    Raises ValueError for critical API errors (Invalid Key, Over Limit).
    """
    origin = f"{lat1},{lon1}"
    destination = f"{lat2},{lon2}"
    
    url = (f"https://maps.googleapis.com/maps/api/directions/json?"
           f"origin={origin}&destination={destination}&departure_time={departure_timestamp}"
           f"&traffic_model=best_guess&key={api_key}")
           
    try:
        # print(f"Matrix API Call: {origin} -> {destination}")
        response = requests.get(url, timeout=10)
        data = response.json()
        status = data.get('status')
        
        if status == 'OK':
            duration_seconds = data['routes'][0]['legs'][0].get('duration_in_traffic', data['routes'][0]['legs'][0]['duration'])['value']
            distance_meters=data['routes'][0]['legs'][0]['distance']['value']
            
            duration_minutes = math.ceil(duration_seconds / 60)
            distance_km = distance_meters / 1000.0
            
            return duration_minutes, distance_km
        elif status in ['REQUEST_DENIED', 'OVER_QUERY_LIMIT', 'INVALID_REQUEST']:
            # CRITICAL ERROR: Stop the whole process if the key is bad or quota is full
            error_msg = f"Google Maps API CRITICAL ERROR: {status} - {data.get('error_message', 'No details')}"
            print(error_msg)
            raise ValueError(error_msg)
        else:
            # Recoverable error (e.g., ZERO_RESULTS for a specific route)
            print(f"API Warning for {origin}->{destination}: {status}")
            return 99999, float('inf')
            
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return 99999, float('inf')

def calculate_matrix(locations: List[Location], api_key: str, departure_time_offset_hours: int = 24) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Calculates the time and distance matrix for a list of locations.
    Returns (time_matrix, distance_matrix).
    """
    num_locations = len(locations)
    
    # Set departure time in the future for predictive traffic
    departure_timestamp = int(time.time()) + (3600 * departure_time_offset_hours)
    
    time_matrix = [[0] * num_locations for _ in range(num_locations)]
    distance_matrix = [[0.0] * num_locations for _ in range(num_locations)]

    # Iterate over every possible pair of locations
    # Note: This O(N^2) loop is very slow for large N. Ideally this should be async.
    for i in range(num_locations):
        for j in range(num_locations):
            if i == j: continue 
            
            loc1 = locations[i]
            loc2 = locations[j]
            
            # Ensure we have coordinates
            if loc1.latitude is None or loc2.latitude is None:
                 time_matrix[i][j] = 99999
                 distance_matrix[i][j] = float('inf')
                 continue

            duration_min, distance_km = get_real_travel_time(
                loc1.latitude, loc1.longitude,
                loc2.latitude, loc2.longitude,
                departure_timestamp,
                api_key
            )
            
            time_matrix[i][j] = duration_min
            distance_matrix[i][j] = distance_km
            
    return time_matrix, distance_matrix
