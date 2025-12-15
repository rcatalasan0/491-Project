-- Stock Market Predictor Database Schema
-- Sprint 1: Foundation tables for defense sector stocks

-- Create database (run separately if needed)
-- CREATE DATABASE stock_predictor;

-- Defense sector stocks table
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) DEFAULT 'defense',
    exchange VARCHAR(10) DEFAULT 'NYSE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical and real-time price data
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    price_date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, price_date)
);

-- Technical indicators and market analysis
CREATE TABLE indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    indicator_type VARCHAR(50), -- 'rsi', 'macd', 'ma_20', 'ma_50'
    value DECIMAL(15,6),
    calculation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Defense sector specific events and catalysts that can affect the stock
CREATE TABLE defense_events (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    event_type VARCHAR(50) NOT NULL, -- 'contract_award', 'earnings', 'merger', 'acquisition', 'product_launch'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_date DATE,
    value_amount DECIMAL(15,2), -- Contract value, deal size, etc.
    impact_rating VARCHAR(10), -- 'high', 'medium', 'low'
    source VARCHAR(255), -- News source, SEC filing, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User management (for future sprints)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- User watchlists
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(10) REFERENCES stocks(symbol),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

-- System audit log for tracking changes
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    action VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_prices_symbol_date ON prices(symbol, price_date DESC);
CREATE INDEX idx_indicators_symbol_type ON indicators(symbol, indicator_type);
CREATE INDEX idx_watchlist_user ON watchlist(user_id);

-- Comments for documentation
COMMENT ON TABLE stocks IS 'Defense sector stock symbols and metadata';
COMMENT ON TABLE prices IS 'OHLCV price data for technical analysis';
COMMENT ON TABLE indicators IS 'Technical indicators and market analysis data';
COMMENT ON TABLE users IS 'User accounts for portfolio tracking';
COMMENT ON TABLE watchlist IS 'User-curated stock watchlists';