# tests/conftest.py
import pytest
import pandas as pd
from datetime import datetime, timedelta


def _make_price_series(n, start_price=400.0):
    """Small helper to generate fake price data."""
    return [start_price + i * 0.5 for i in range(n)]


@pytest.fixture(scope="session")
def app_instance():
    """
    Get the Flask app instance from app.py.

    Supports either:
      - app = Flask(__name__)
      - def create_app(): ...
    """
    try:
        from app import app  # type: ignore
        return app
    except ImportError:
        from app import create_app  # type: ignore
        return create_app()


@pytest.fixture()
def client(app_instance):
    """
    Flask test client used by all API tests.
    """
    app_instance.config["TESTING"] = True
    with app_instance.test_client() as c:
        yield c


@pytest.fixture()
def mock_yfinance_data():
    """
    DataFrame that looks like ~252 trading days of OHLCV data
    for a defense stock (used by most stock API tests).
    """
    n = 252  # about a year of trading days
    end = datetime.utcnow()
    dates = pd.date_range(end=end, periods=n, freq="B")

    data = {
        "Open": _make_price_series(n, 400.0),
        "High": _make_price_series(n, 401.0),
        "Low": _make_price_series(n, 399.0),
        "Close": _make_price_series(n, 400.5),
        "Volume": [1_000_000 + i * 100 for i in range(n)],
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture()
def mock_insufficient_stock_data():
    """
    Short series (<200 days) to simulate a new IPO / limited history.
    """
    n = 30
    end = datetime.utcnow()
    dates = pd.date_range(end=end, periods=n, freq="B")

    data = {
        "Open": _make_price_series(n, 50.0),
        "High": _make_price_series(n, 51.0),
        "Low": _make_price_series(n, 49.0),
        "Close": _make_price_series(n, 50.5),
        "Volume": [200_000 + i * 10 for i in range(n)],
    }
    return pd.DataFrame(data, index=dates)
