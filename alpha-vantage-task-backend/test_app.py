import pytest
from app import app
from utils import calculate_daily_average, print_api_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_daily_average_missing_dates(client):
    response = client.get('/daily_average?function=WTI')
    assert response.status_code == 400
    assert "Start date and end date are required" in response.json['error']

def test_daily_average_invalid_function(client):
    response = client.get('/daily_average?function=INVALID&start_date=2023-01-01&end_date=2023-12-31')
    assert response.status_code == 400
    assert "No data available from API" in response.json['error']

def test_daily_average_valid_request(client, mocker):
    mock_data = {
        "data": [
            {"date": "2023-01-01", "value": "70"},
            {"date": "2023-01-02", "value": "72"},
            {"date": "2023-01-03", "value": "75"},
        ]
    }
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_data))
    
    response = client.get('/daily_average?function=WTI&start_date=2023-01-01&end_date=2023-01-03')
    assert response.status_code == 200
    assert response.json['function'] == 'WTI'
    assert response.json['average_price'] == 72.33
    assert response.json['currency'] == 'USD per barrel'

def test_calculate_daily_average():
    data = {
        "data": [
            {"date": "2023-01-01", "value": "70"},
            {"date": "2023-01-02", "value": "72"},
            {"date": "2023-01-03", "value": "75"},
        ]
    }
    average = calculate_daily_average(data, "2023-01-01", "2023-01-03")
    assert round(average, 2) == 72.33

def test_calculate_daily_average_empty_range():
    data = {
        "data": [
            {"date": "2023-01-01", "value": "70"},
            {"date": "2023-01-02", "value": "72"},
            {"date": "2023-01-03", "value": "75"},
        ]
    }
    average = calculate_daily_average(data, "2023-01-04", "2023-01-05")
    assert average is None

def test_print_api_data(capsys):
    data = {
        "data": [
            {"date": "2023-01-01", "value": "70"},
            {"date": "2023-01-02", "value": "72"},
            {"date": "2023-01-03", "value": "75"},
        ]
    }
    print_api_data(data, "2023-01-01", "2023-01-03")
    captured = capsys.readouterr()
    assert "API Data Summary:" in captured.out
    assert "Total data points: 3" in captured.out

def test_daily_average_different_intervals(client, mocker):
    mock_data = {
        "data": [
            {"date": "2023-01-01", "value": "70"},
            {"date": "2023-01-08", "value": "72"},
            {"date": "2023-01-15", "value": "75"},
        ]
    }
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_data))
    
    response = client.get('/daily_average?function=WTI&interval=weekly&start_date=2023-01-01&end_date=2023-01-15')
    assert response.status_code == 200
    assert response.json['interval'] == 'weekly'
    assert response.json['average_price'] == 72.33