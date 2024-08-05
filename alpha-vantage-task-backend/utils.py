from datetime import datetime

def print_api_data(data, start_date, end_date):
    print(f"API Data Summary:")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")
    
    if 'data' not in data:
        print("No 'data' key found in API response")
        return
    
    data_points = data['data']
    print(f"Total data points: {len(data_points)}")
    
    if data_points:
        print("First 5 data points:")
        for entry in data_points[:5]:
            print(f"Date: {entry['date']}, Value: {entry['value']}")
        
        print("Last 5 data points:")
        for entry in data_points[-5:]:
            print(f"Date: {entry['date']}, Value: {entry['value']}")
    else:
        print("No data points found in API response")

def calculate_daily_average(data, start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    daily_prices = []

    print(f"Calculating average for date range: {start_date} to {end_date}")

    for entry in data.get('data', []):
        date = datetime.strptime(entry['date'], '%Y-%m-%d')
        if start_date <= date <= end_date:
            try:
                price = float(entry['value'])
                daily_prices.append(price)
                print(f"Added price {price} for date {date}")
            except ValueError:
                print(f"Skipped invalid price value '{entry['value']}' for date {date}")

    if not daily_prices:
        print("No valid prices found in the specified date range")
        return None

    average = sum(daily_prices) / len(daily_prices)
    print(f"Calculated average: {average}")
    return average