import pandas as pd
import re
from datetime import datetime
from typing import List, Optional, Tuple
from ..models.schemas import Order, Location
import io

# Regex for item counts i.e. "2 x Burger"
ITEM_COUNT_REGEX = re.compile(r'(\d+)\s*x')

def parse_order_time(time_str: str) -> Tuple[Optional[float], Optional[int], Optional[int]]:
    """
    Parses time format: "11:41 PM, September 10 2024"
    Returns (timestamp, day_of_year, minutes_from_midnight)
    """
    try:
        dt_obj = datetime.strptime(str(time_str).strip(), "%I:%M %p, %B %d %Y")
        day_of_year = dt_obj.timetuple().tm_yday
        minutes_from_midnight = dt_obj.hour * 60 + dt_obj.minute
        return dt_obj.timestamp(), day_of_year, minutes_from_midnight
    except ValueError:
        return None, None, None

def parse_demand(item_str: str) -> int:
    """
    Parses item string to calculate total demand.
    """
    if not isinstance(item_str, str):
        return 1
    matches = ITEM_COUNT_REGEX.findall(item_str)
    if not matches:
        return 1
    try:
        return sum(int(count) for count in matches)
    except:
        return 1

def parse_csv_content(file_content: str) -> List[Order]:
    """
    Parses the CSV string.
    Returns a list of Order objects.
    """
    try:
        # Read CSV from string
        df = pd.read_csv(io.StringIO(file_content), low_memory=False)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")
        
    orders = []
    
    # Expected columns
    RESTAURANT_COL = 'Restaurant name'
    SUBZONE_COL = 'Subzone'
    CITY_COL = 'City'
    TIME_COL = 'Order Placed At'
    ITEM_COL = 'Items in order'
    ORDER_ID_COL = 'Order ID'
    
    # Check simple validity
    if RESTAURANT_COL not in df.columns:
        raise ValueError("CSV is missing required columns. Please check the format.")

    for index, row in df.iterrows():
        try:
            # Construct address
            original_address = f"{row[RESTAURANT_COL]}, {row[SUBZONE_COL]}, {row[CITY_COL]}"
            
            # Parse time
            timestamp, day, minute = parse_order_time(row[TIME_COL])
            if timestamp is None:
                continue # Skip bad times
            
            # Parse demand
            demand = parse_demand(row[ITEM_COL])
            
            # Create Order object
            # Note: We create a Location object with just the address string initially.
            # Coordinates will be filled in later by the Geocoder.
            orders.append(Order(
                order_id=str(row[ORDER_ID_COL]),
                timestamp=int(timestamp),
                location=Location(original_address=original_address),
                demand=demand
            ))
            
        except Exception:
            continue
            
    return orders

def extract_unique_addresses(orders: List[Order]) -> List[str]:
    """Helper to get unique address strings from a list of orders"""
    return list(set(o.location.original_address for o in orders))
