import json
import yfinance as yf
import sys
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "YFinance",
    host="0.0.0.0",
    port=8000,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

@mcp.tool()
def get_stock_data(ticker: str) -> str:
    """Fetch current stock price and basic info for a given ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Safe extraction
    return json.dumps({
        "price": info.get("currentPrice", info.get("regularMarketPrice", 0.0)),
        "high": info.get("dayHigh", 0.0),
        "low": info.get("dayLow", 0.0),
        "previous_close": info.get("previousClose", 0.0),
        "sector": info.get("sector", "Unknown"),
        "business_summary": info.get("longBusinessSummary", "")[:300] + "..."
    })

@mcp.tool()
def get_company_news(ticker: str) -> str:
    """Fetch recent news article titles and links for a company."""
    stock = yf.Ticker(ticker)
    news = stock.news
    if not news:
        return "No news found."
    
    formatted_news = []
    for item in news[:5]:
        # yfinance >= 0.2.x nests data inside item['content']
        content = item.get("content", item)
        title = content.get("title") or item.get("title", "No title")
        provider = content.get("provider", {})
        publisher = provider.get("displayName") or item.get("publisher", "Unknown")
        url_obj = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        url = url_obj.get("url", "")
        line = f"- **{title}** — {publisher}"
        if url:
            line += f" ([link]({url}))"
        formatted_news.append(line)
    
    return "\n".join(formatted_news)

if __name__ == "__main__":
    if "--sse" in sys.argv:
        print("Starting YFinance MCP Server on SSE (0.0.0.0:8000)...")
        mcp.run(transport="sse")
    else:
        mcp.run()
