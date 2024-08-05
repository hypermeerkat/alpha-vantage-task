from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta
from utils import calculate_daily_average, print_api_data
from dotenv import load_dotenv
import os
from flask_cors import CORS
from cachetools import TTLCache
import json

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# Create a cache with a maximum of 100 items and a TTL of 1 hour
cache = TTLCache(maxsize=100, ttl=3600)

RESOURCE_INTERVALS = {
    'WTI': ['daily', 'weekly', 'monthly'],
    'BRENT': ['daily', 'weekly', 'monthly'],
    'NATURAL_GAS': ['daily', 'weekly', 'monthly'],
    'COPPER': ['monthly', 'quarterly', 'annual'],
    'ALUMINUM': ['monthly', 'quarterly', 'annual'],
    'WHEAT': ['monthly', 'quarterly', 'annual'],
    'CORN': ['monthly', 'quarterly', 'annual'],
    'COTTON': ['monthly', 'quarterly', 'annual'],
    'SUGAR': ['monthly', 'quarterly', 'annual'],
    'COFFEE': ['monthly', 'quarterly', 'annual'],
}

@app.route('/daily_average', methods=['GET'])
def daily_average():
    function = request.args.get('function', 'WTI')
    interval = request.args.get('interval', 'daily')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')

    if function not in RESOURCE_INTERVALS:
        return jsonify({"error": f"Invalid resource: {function}"}), 400

    if interval not in RESOURCE_INTERVALS[function]:
        return jsonify({"error": f"Invalid interval '{interval}' for resource '{function}'. Valid intervals are: {', '.join(RESOURCE_INTERVALS[function])}"}), 400

    if not start_date or not end_date:
        return jsonify({"error": f"Start date and end date are required. Received: start_date={start_date}, end_date={end_date}"}), 400

    cache_key = f"{function}_{interval}"
    cached_data = cache.get(cache_key)

    if cached_data is None:
        url = f"https://www.alphavantage.co/query?function={function}&interval={interval}&apikey={api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()
            
            if 'Information' in data:
                return jsonify({"error": f"API limit reached or invalid key. Message: {data['Information']}"}), 429

            if 'Error Message' in data:
                return jsonify({"error": data['Error Message']}), 400

            # Print the full API response for debugging
            print("Full API Response:", json.dumps(data, indent=2))

            # Cache the API response
            cache[cache_key] = json.dumps(data)
        except requests.RequestException as e:
            return jsonify({"error": f"API request failed: {str(e)}. URL: {url}"}), 500
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    else:
        data = json.loads(cached_data)

    print_api_data(data, start_date, end_date)

    average = calculate_daily_average(data, start_date, end_date)
    
    if average is None:
        return jsonify({
            "error": f"No valid data available for the specified date range: {start_date} to {end_date}. "
                     f"Available date range: {data['data'][-1]['date']} to {data['data'][0]['date']}"
        }), 400
    
    return jsonify({
        "function": function,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "average_price": round(average, 2),
        "currency": "USD per unit"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port)