import pandas as pd
import random
from datetime import datetime, timedelta

def generate():
    # Read the original data
    df = pd.read_csv('order_history_kaggle_data.csv', low_memory=False)
    
    # We just need 500 rows. Let's sample them to get a mix of locations.
    df_sampled = df.sample(n=500, random_state=42).copy()
    
    # We want to pack them all into Sept 12, 2024 between 08:00 AM and 09:00 AM
    # Let's generate 100 random times in that hour
    base_time = datetime(2024, 9, 12, 8, 0, 0)
    
    new_times = []
    for _ in range(500):
        random_seconds = random.randint(0, 3600)
        dt = base_time + timedelta(seconds=random_seconds)
        # Format: "11:41 PM, September 10 2024"
        new_times.append(dt.strftime("%I:%M %p, %B %d %Y"))
        
    df_sampled['Order Placed At'] = new_times
    
    # Sort them chronologically just to be nice (though the backend sorts them anyway)
    df_sampled['temp_time'] = pd.to_datetime(df_sampled['Order Placed At'], format="%I:%M %p, %B %d %Y")
    df_sampled = df_sampled.sort_values('temp_time').drop(columns=['temp_time'])
    
    # Save to new csv
    df_sampled.to_csv('dense_orders_500.csv', index=False)
    print("Successfully generated dense_orders_500.csv with 500 orders squeezed into 1 hour!")

if __name__ == "__main__":
    generate()
