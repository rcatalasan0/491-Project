#include <string>
#include <iostream>

// Has been declared in main.cpp
std::string run_route(const std::string& path);

#define ASSERT_CONTAINS(hay, needle) do { \
  if ((hay).find(needle) == std::string::npos) { \
    std::cerr << "Expected to find: " << needle << "\nIn:\n" << hay << std::endl; \
    std::exit(1); \
  } \
} while (0)

int main() {
  // Health
  ASSERT_CONTAINS(run_route("/health"), R"("status": "OK")");
  // Stock list
  {
    auto r = run_route("/api/v1/stocks");
    ASSERT_CONTAINS(r, R"("symbol": "LMT")");
    ASSERT_CONTAINS(r, R"("sector": "defense")");
  }
  // Valid detail
  {
    auto r = run_route("/api/v1/stocks/LMT");
    ASSERT_CONTAINS(r, R"("symbol": "LMT")");
    ASSERT_CONTAINS(r, R"("name": "Lockheed Martin")");
  }
  // Unknown if we can't find the Stock
  ASSERT_CONTAINS(run_route("/api/v1/stocks/XYZ"), R"("error": "Stock not found")");
  // Missing symbol is we can't find abbrev
  ASSERT_CONTAINS(run_route("/api/v1/stocks/"), R"("error":"Missing symbol")");

  std::cout << "router_test OK\n";
  return 0;
}
