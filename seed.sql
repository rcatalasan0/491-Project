-- Seed data for Stock Market Predictor
-- Defense sector stocks for Sprint 1 demo

-- Insert defense sector stocks
INSERT INTO stocks (symbol, name, sector, exchange) VALUES
('LMT', 'Lockheed Martin Corporation', 'defense', 'NYSE'),
('RTX', 'Raytheon Technologies Corporation', 'defense', 'NYSE'),
('BA', 'The Boeing Company', 'defense', 'NYSE'),
('NOC', 'Northrop Grumman Corporation', 'defense', 'NYSE'),
('LHX', 'L3Harris Technologies Inc', 'defense', 'NYSE');

-- Insert sample price data (last 5 trading days for demo)
INSERT INTO prices (symbol, price_date, open_price, high_price, low_price, close_price, volume) VALUES
-- Lockheed Martin (LMT)
('LMT', '2025-09-15', 425.00, 428.50, 423.10, 427.89, 1250000),
('LMT', '2025-09-12', 420.50, 426.00, 419.75, 425.67, 1180000),
('LMT', '2025-09-11', 418.25, 422.80, 417.50, 421.15, 1340000),
('LMT', '2025-09-10', 415.60, 419.90, 414.20, 418.75, 1420000),
('LMT', '2025-09-09', 412.30, 417.25, 411.85, 416.80, 1560000),

-- Raytheon (RTX)
('RTX', '2025-09-15', 112.50, 114.20, 111.80, 113.95, 8750000),
('RTX', '2025-09-12', 111.25, 113.10, 110.90, 112.85, 8200000),
('RTX', '2025-09-11', 109.80, 112.40, 109.60, 111.75, 9100000),
('RTX', '2025-09-10', 108.90, 110.50, 108.40, 110.20, 8900000),
('RTX', '2025-09-09', 107.75, 109.80, 107.20, 109.45, 9450000),

-- Boeing (BA)
('BA', '2025-09-15', 175.20, 178.50, 174.10, 177.85, 12500000),
('BA', '2025-09-12', 172.80, 176.90, 171.50, 175.60, 11800000),
('BA', '2025-09-11', 170.45, 174.20, 169.80, 173.25, 13200000),
('BA', '2025-09-10', 168.90, 172.15, 167.75, 171.80, 14100000),
('BA', '2025-09-09', 166.50, 170.25, 165.90, 169.75, 13800000);

-- Insert sample technical indicators (RSI, moving averages)
INSERT INTO indicators (symbol, indicator_type, value, calculation_date) VALUES
('LMT', 'rsi', 65.4, '2025-09-15'),
('LMT', 'ma_20', 422.5, '2025-09-15'),
('LMT', 'ma_50', 418.2, '2025-09-15'),
('RTX', 'rsi', 58.2, '2025-09-15'),
('RTX', 'ma_20', 112.8, '2025-09-15'),
('RTX', 'ma_50', 110.4, '2025-09-15'),
('BA', 'rsi', 72.1, '2025-09-15'),
('BA', 'ma_20', 174.3, '2025-09-15'),
('BA', 'ma_50', 171.6, '2025-09-15');

-- Insert demo user for testing (password: 'demo123' hashed)
INSERT INTO users (email, password_hash, role) VALUES
('demo@stockpredictor.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdeAXhb7u5BPYse', 'demo');

-- Insert sample watchlist
INSERT INTO watchlist (user_id, symbol) VALUES
(1, 'LMT'),
(1, 'RTX'),
(1, 'BA');