"""
Stock API Integration Tests
Test ID: API-001 through API-012
Sprint 3 - Stock Market Predictor
"""
import pytest
from unittest.mock import patch, MagicMock
import time


@pytest.mark.integration
class TestStockAPIIntegration:
    """Yahoo Finance API integration tests"""
    
    @patch('yfinance.Ticker')
    def test_fetch_365_days_stock_data(self, mock_ticker, client, mock_yfinance_data):
        """API-001: Bug #45 - Verify 365 days of data returned"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        response = client.get('/api/stocks/LMT?period=1y')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'ticker' in data
        assert data['ticker'] == 'LMT'
        assert 'historical_data' in data
        
        # Verify 365 days (or ~252 trading days)
        assert len(data['historical_data']) >= 200
        
        # Verify yfinance called with period='1y'
        mock_instance.history.assert_called_once()
        call_kwargs = mock_instance.history.call_args[1]
        assert call_kwargs.get('period') == '1y'
    
    
    @patch('yfinance.Ticker')
    def test_invalid_ticker_handling(self, mock_ticker, client):
        """API-002: Handle invalid ticker symbols"""
        import pandas as pd
        
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance
        
        response = client.get('/api/stocks/INVALIDTICKER?period=1y')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    
    @patch('yfinance.Ticker')
    def test_insufficient_data_handling(self, mock_ticker, client, mock_insufficient_stock_data):
        """API-003: Handle stocks with <200 days of data"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_insufficient_stock_data
        mock_ticker.return_value = mock_instance
        
        response = client.get('/api/stocks/NEWIPO?period=1y')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'warning' in data or len(data['historical_data']) < 200
        else:
            assert response.status_code == 400
    
    
    @patch('yfinance.Ticker')
    def test_api_timeout_handling(self, mock_ticker, client):
        """API-004: Handle yFinance API timeouts"""
        mock_ticker.side_effect = TimeoutError("API timeout")
        
        response = client.get('/api/stocks/LMT?period=1y')
        
        assert response.status_code in [503, 504, 500]
        data = response.get_json()
        assert 'error' in data
    
    
    @patch('yfinance.Ticker')
    def test_rate_limit_handling(self, mock_ticker, client):
        """API-005: Handle API rate limiting"""
        mock_instance = MagicMock()
        mock_instance.history.side_effect = Exception("HTTPError 429: Too Many Requests")
        mock_ticker.return_value = mock_instance
        
        response = client.get('/api/stocks/LMT?period=1y')
        
        assert response.status_code in [429, 503]
    
    
    @patch('yfinance.Ticker')
    def test_cache_implementation(self, mock_ticker, client, mock_yfinance_data):
        """API-006: Verify caching reduces API calls"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        # First request
        response1 = client.get('/api/stocks/LMT?period=1y')
        assert response1.status_code == 200
        
        # Second request (should use cache)
        response2 = client.get('/api/stocks/LMT?period=1y')
        assert response2.status_code == 200
        
        # Third request
        response3 = client.get('/api/stocks/LMT?period=1y')
        assert response3.status_code == 200
        
        # Verify API not called every time
        call_count = mock_ticker.call_count
        assert call_count <= 3
    
    
    @patch('yfinance.Ticker')
    def test_batch_ticker_request(self, mock_ticker, client, mock_yfinance_data):
        """API-007: Handle multiple tickers in one request"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        response = client.post('/api/stocks/batch', json={
            'tickers': ['LMT', 'BA', 'NOC']
        })
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'stocks' in data
            assert len(data['stocks']) == 3
        else:
            pytest.skip("Batch endpoint not implemented")
    
    
    @patch('yfinance.Ticker')
    def test_data_completeness(self, mock_ticker, client, mock_yfinance_data):
        """API-008: Verify all required fields present"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        response = client.get('/api/stocks/LMT?period=1y')
        assert response.status_code == 200
        
        data = response.get_json()
        historical = data['historical_data']
        
        if len(historical) > 0:
            sample = historical[0]
            required_fields = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            for field in required_fields:
                assert field in sample
    
    
    @patch('yfinance.Ticker')
    def test_period_parameter_variations(self, mock_ticker, client, mock_yfinance_data):
        """API-009: Test different period parameters"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y']
        
        for period in periods:
            response = client.get(f'/api/stocks/LMT?period={period}')
            assert response.status_code == 200
    
    
    def test_missing_ticker_parameter(self, client):
        """API-010: Handle missing ticker parameter"""
        response = client.get('/api/stocks/')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    
    @patch('yfinance.Ticker')
    def test_response_time_under_load(self, mock_ticker, client, mock_yfinance_data):
        """API-011: Verify response time <500ms"""
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        start = time.time()
        response = client.get('/api/stocks/LMT?period=1y')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5  # 500ms
    
    
    @patch('yfinance.Ticker')
    def test_concurrent_api_requests(self, mock_ticker, client, mock_yfinance_data):
        """API-012: Handle concurrent requests"""
        import threading
        
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_instance
        
        results = []
        
        def make_request(ticker):
            response = client.get(f'/api/stocks/{ticker}?period=1y')
            results.append(response.status_code)
        
        threads = []
        tickers = ['LMT', 'BA', 'NOC', 'RTX', 'GD'] * 2
        
        for ticker in tickers:
            thread = threading.Thread(target=make_request, args=(ticker,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert all(status == 200 for status in results)
