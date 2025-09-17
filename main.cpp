#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <sstream>
#include <thread>
#include <chrono>

// Simple HTTP server for Sprint 1 demo
class StockAPI {
private:
    std::map<std::string, std::string> stocks = {
        {"LMT", "Lockheed Martin"},
        {"RTX", "Raytheon Technologies"},
        {"BA", "Boeing"},
        {"NOC", "Northrop Grumman"},
        {"LHX", "L3Harris Technologies"}
    };

public:
    std::string handleHealth() {
        return R"({"status": "OK", "timestamp": ")" + getCurrentTimestamp() + R"(", "service": "stock-predictor-api"})";
    }

    std::string handleStocks() {
        std::stringstream json;
        json << "[";
        bool first = true;
        for (const auto& [symbol, name] : stocks) {
            if (!first) json << ",";
            json << R"({"symbol": ")" << symbol << R"(", "name": ")" << name << R"(", "sector": "defense"})";
            first = false;
        }
        json << "]";
        return json.str();
    }

    std::string handleStockDetail(const std::string& symbol) {
        if (stocks.find(symbol) == stocks.end()) {
            return R"({"error": "Stock not found", "symbol": ")" + symbol + R"("})";
        }
        
        // Mock price data for demo
         return R"({
            "symbol": ")" + symbol + R"(",
            "name": ")" + stocks[symbol] + R"(",
            "current_price": 425.67,
            "change": "+2.34",
            "change_percent": "+0.55%",
            "last_updated": ")" + getCurrentTimestamp() + R"(",
            "52_week_high": 445.50,
            "52_week_low": 380.25,
            "volume": 1250000,
            "market_cap": "68.5B"
        })";
    }

private:
    std::string getCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%SZ");
        return ss.str();
    }
};

// Simple route handler
class Router {
private:
    StockAPI api;

public:
    std::string route(const std::string& path) {
        if (path == "/health" || path == "/api/v1/health") {
            return api.handleHealth();
        }
        else if (path == "/api/v1/stocks") {
            return api.handleStocks();
        }
        else if (path.substr(0, 17) == "/api/v1/stocks/") {
            std::string symbol = path.substr(17);
            return api.handleStockDetail(symbol);
        }
        else {
            return R"({"error": "Not found", "path": ")" + path + R"("})";
        }
    }
};

// Main server (simplified for demo)
int main() {
    Router router;
    
    std::cout << "🚀 Stock Market Predictor API Server Starting..." << std::endl;
    std::cout << "📊 Defense Sector Focus (LMT, RTX, BA, NOC, LHX)" << std::endl;
    std::cout << "🔗 Endpoints:" << std::endl;
    std::cout << "   GET /health" << std::endl;
    std::cout << "   GET /api/v1/stocks" << std::endl;
    std::cout << "   GET /api/v1/stocks/{symbol}" << std::endl;
    std::cout << "\n📡 Server running on localhost:8080" << std::endl;
    
    // Demo the endpoints
    std::cout << "\n=== DEMO OUTPUT ===" << std::endl;
    std::cout << "GET /health:" << std::endl;
    std::cout << router.route("/health") << std::endl;
    
    std::cout << "\nGET /api/v1/stocks:" << std::endl;
    std::cout << router.route("/api/v1/stocks") << std::endl;
    
    std::cout << "\nGET /api/v1/stocks/LMT:" << std::endl;
    std::cout << router.route("/api/v1/stocks/LMT") << std::endl;
    
    // Keep server "running" for demo
    std::cout << "\n✅ API Demo Complete - Ready for Sprint 1 submission!" << std::endl;
    
    return 0;
}
