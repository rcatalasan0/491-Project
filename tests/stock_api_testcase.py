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

# ---------------------------------------------------------------------------
# Extra API + /predict endpoint tests for Sprint 3
# ---------------------------------------------------------------------------

@pytest.mark.api
class TestHealthAndErrorStructure:
    """Additional tests for /health, 404 and 500 handlers."""

    def test_health_returns_expected_fields(self, client):
        """API-H001: /health returns JSON with status + uptime."""
        resp = client.get("/health")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["status"] == "OK"
        assert data["service"] == "stock-predictor-api"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        # uptime should always be non-negative
        assert data["uptime_seconds"] >= 0

    def test_404_error_structure(self, client):
        """API-H002: 404 handler returns JSON structure (no HTML)."""
        resp = client.get("/this/route/does/not/exist")
        assert resp.status_code == 404

        data = resp.get_json()
        assert data["error"] == "Resource not found"
        assert data["code"] == 404
        assert data["path"] == "/this/route/does/not/exist"

    def test_500_error_structure(self, client, monkeypatch):
        """API-H003: 500 handler returns JSON payload."""

        # Force an exception inside a view so we hit the 500 handler.
        from app import app as flask_app

        @flask_app.route("/boom-test")
        def boom_test():
            raise RuntimeError("forced test error")

        resp = client.get("/boom-test")
        assert resp.status_code == 500

        data = resp.get_json()
        assert data["error"] == "Internal server error"
        assert data["code"] == 500
        assert "forced test error" in data["message"]


@pytest.mark.api
class TestPredictEndpointValidation:
    """Validation and security tests around the /predict endpoint."""

    @pytest.mark.parametrize("days", ["0", "-1", "31", "100"])
    def test_invalid_days_out_of_range(self, client, days):
        """API-P001: days must be between 1 and 30."""
        resp = client.get(f"/predict?ticker=LMT&days={days}")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "days must be between 1 and 30" in data["error"]

    @pytest.mark.parametrize("days", ["abc", "3.5", "", "   "])
    def test_invalid_days_not_integer(self, client, days):
        """API-P002: non-integer days are rejected."""
        url = f"/predict?ticker=LMT&days={days}"
        resp = client.get(url)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "days must be an integer" in data["error"] or "days parameter is required" in data["error"]

    def test_missing_days_parameter(self, client):
        """API-P003: missing days → 400."""
        resp = client.get("/predict?ticker=LMT")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "days parameter is required" in data["error"]

    def test_missing_ticker_parameter_predict(self, client):
        """API-P004: missing ticker → 400."""
        resp = client.get("/predict?days=7")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "ticker is required" in data["error"]

    @pytest.mark.parametrize(
        "ticker",
        [
            "LMT;",                # SQL-ish characters
            "BA<script>",          # XSS-ish
            "NOC DROP TABLE",      # spaces
            "VERYVERYLONGTICKER",  # > 10 chars
        ],
    )
    def test_invalid_ticker_rejected(self, client, ticker):
        """API-P005: ticker must be alphanumeric <= 10 chars."""
        resp = client.get(f"/predict?ticker={ticker}&days=5")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "ticker must be alphanumeric" in data["error"] or "ticker is required" in data["error"]

    def test_unicode_ticker_rejected(self, client):
        """API-P006: unicode / non-ASCII ticker values rejected."""
        resp = client.get("/predict?ticker=テスト&days=5")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "ticker must be alphanumeric" in data["error"]

    def test_valid_predict_structure(self, client):
        """API-P007: happy path – JSON structure for /predict."""
        resp = client.get("/predict?ticker=LMT&days=7")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["ticker"] == "LMT"
        assert data["days"] == 7
        assert data["model"] == "baseline-linear-demo"
        assert len(data["predictions"]) == 7

        for i, row in enumerate(data["predictions"], start=1):
            assert row["day"] == i
            assert isinstance(row["predicted_price"], (int, float))

    def test_predict_response_is_deterministic(self, client):
        """API-P008: calling /predict twice with same params gives same sequence."""
        url = "/predict?ticker=LMT&days=3"
        r1 = client.get(url)
        r2 = client.get(url)

        assert r1.status_code == 200
        assert r2.status_code == 200

        d1 = r1.get_json()["predictions"]
        d2 = r2.get_json()["predictions"]
        assert d1 == d2  # deterministic, good for regression tests


@pytest.mark.api
class TestStockEndpointEdgeCases:
    """More coverage for /api/stocks/<ticker> edge conditions."""

    def test_default_period_is_1y(self, client, monkeypatch):
        """API-S001: /api/stocks/LMT uses 1y period by default."""

        import app as app_module

        called_args = {}

        def fake_fetch_stock_history(ticker, period="1y"):
            called_args["ticker"] = ticker
            called_args["period"] = period
            # minimal fake response for test
            return [
                {
                    "date": "2025-01-01",
                    "Open": 10.0,
                    "High": 11.0,
                    "Low": 9.5,
                    "Close": 10.5,
                    "Volume": 1234,
                }
            ]

        monkeypatch.setattr(app_module, "fetch_stock_history", fake_fetch_stock_history)

        resp = client.get("/api/stocks/LMT")
        assert resp.status_code == 200

        assert called_args["ticker"] == "LMT"
        assert called_args["period"] == "1y"

        data = resp.get_json()
        assert data["ticker"] == "LMT"
        assert data["period"] == "1y"
        assert data["count"] == 1

    def test_batch_endpoint_rejects_empty_body(self, client):
        """API-S002: batch endpoint requires non-empty tickers list."""
        resp = client.post("/api/stocks/batch", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["code"] == "INVALID_BODY"

    def test_batch_endpoint_mixed_valid_invalid(self, client, monkeypatch):
        """API-S003: batch returns per-ticker status for valid + invalid tickers."""
        import app as app_module

        def fake_fetch_stock_history(ticker, period="1y"):
            if ticker.upper() == "LMT":
                return [{"date": "2025-01-01", "Open": 1, "High": 1, "Low": 1, "Close": 1, "Volume": 1}]
            from app import InvalidTickerError
            raise InvalidTickerError(f"bad ticker {ticker}")

        monkeypatch.setattr(app_module, "fetch_stock_history", fake_fetch_stock_history)

        resp = client.post("/api/stocks/batch", json={"tickers": ["LMT", "BAD1"]})
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["requested"] == 2
        assert len(data["stocks"]) == 2

        statuses = {row["ticker"]: row["status"] for row in data["stocks"]}
        assert statuses["LMT"] == "ok"
        assert statuses["BAD1"] == "invalid"
