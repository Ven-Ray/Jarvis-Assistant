"""Finance search provider for stocks, crypto, currency.
Uses Alpha Vantage API with Yahoo Finance fallback via scraping.
"""

import os
import re
import requests
from datetime import datetime, timezone
from typing import Optional

from ..providers.base import SearchProvider
from ..schemas import StockPriceResult


class FinanceError(Exception):
    """Base exception for finance module errors."""
    pass


class FinanceTimeoutError(FinanceError):
    """Raised when finance API request times out."""
    pass


class FinanceSymbolError(FinanceError):
    """Raised when stock symbol cannot be resolved."""
    pass


class StockPriceProvider(SearchProvider):
    """Stock price provider using Alpha Vantage API with Yahoo fallback."""
    
    ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
    YAHOO_SEARCH_URL = "https://search.yahoo.com/search"
    
    def __init__(self, timeout=None, api_key=None):
        self.timeout = timeout or 10
        # Use environment variable if not provided
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    
    def supports(self, request) -> bool:
        """Check if this is a finance-related request."""
        query_lower = (request.original_query or "").lower()
        return any(word in query_lower for word in [
            "stock", "stocks", "share", "shares", "crypto", "cryptocurrency",
            "bitcoin", "ethereum", "price of", "market", "nasdaq", "s&p",
            "dow jones", "forex", "currency"
        ])
    
    async def search(self, request):
        """Execute stock price lookup and return normalized result."""
        from ..models import SearchResult
        
        try:
            # Extract symbol from query
            symbol = self._extract_symbol(request.original_query)
            if not symbol:
                raise FinanceSymbolError("Could not determine stock symbol from query")
            
            # Try Alpha Vantage first
            price_data = None
            source = ""
            
            if self.api_key:
                try:
                    price_data = self._get_alpha_vantage_price(symbol)
                    source = "alpha-vantage"
                except FinanceError as e:
                    print(f"[{request.request_id}] Alpha Vantage failed: {e}")
            
            # Fallback to Yahoo Finance scraping
            if not price_data:
                try:
                    price_data = self._get_yahoo_price(symbol)
                    source = "yahoo-finance"
                except FinanceError as e:
                    print(f"[{request.request_id}] Yahoo Finance failed: {e}")
            
            if not price_data:
                raise FinanceError("All stock price sources failed")
            
            # Validate with schema
            result = StockPriceResult(
                symbol=symbol.upper(),
                name=price_data.get("name", ""),
                price=float(price_data["price"]),
                currency=price_data.get("currency", "USD"),
                change=float(price_data.get("change", 0)),
                change_percent=float(price_data.get("change_percent", 0)),
                timestamp=datetime.now(timezone.utc),
                source=source,
                data_timestamp=price_data.get("timestamp")
            )
            
            # Format response deterministically (no LLM needed)
            response_text = self._format_stock_response(result)
            
            return SearchResult(
                request_id=request.request_id,
                category="stocks",
                original_query=request.original_query,
                interpreted_query=f"stock price {symbol}",
                entities={"symbol": symbol},
                data=response_text,
                sources=[{"name": source, "url": ""}],
                retrieved_at=datetime.now(timezone.utc),
                freshness=0.0,
                confidence=1.0
            )
            
        except FinanceError as e:
            return SearchResult(
                request_id=request.request_id,
                category="stocks",
                original_query=request.original_query,
                error=str(e)
            )
    
    def _extract_symbol(self, query):
        """Extract stock symbol from user query."""
        # Look for common ticker patterns (1-5 uppercase letters)
        match = re.search(r'\b([A-Z]{1,5})\b', query)
        if match:
            return match.group(1)
        
        # Try to find company name and map to symbol (simplified)
        query_lower = query.lower()
        symbol_map = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "meta": "META",
            "nvidia": "NVDA", "netflix": "NFLX"
        }
        
        for name, symbol in symbol_map.items():
            if name in query_lower:
                return symbol
        
        return None
    
    def _get_alpha_vantage_price(self, symbol):
        """Get stock price from Alpha Vantage API."""
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol.upper(),
                "apikey": self.api_key
            }
            
            response = requests.get(
                self.ALPHA_VANTAGE_BASE, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for error messages in response
            if "Error Message" in data:
                raise FinanceError(data["Error Message"])
            
            quote = data.get("Global Quote", {})
            if not quote:
                raise FinanceSymbolError(f"No quote found for {symbol}")
            
            return {
                "name": quote.get("08. symbol", symbol),
                "price": quote.get("05. price"),
                "change": quote.get("09. change"),
                "change_percent": quote.get("10. change percent", "").replace("%", ""),
                "currency": "USD"
            }
            
        except requests.Timeout:
            raise FinanceTimeoutError(f"Alpha Vantage timed out for {symbol}")
        except requests.RequestException as e:
            raise FinanceError(f"Alpha Vantage request failed: {e}")
    
    def _get_yahoo_price(self, symbol):
        """Get stock price from Yahoo Finance via web scraping."""
        try:
            url = f"https://finance.yahoo.com/quote/{symbol.upper()}/"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            html = response.text
            
            # Extract price using regex (simplified parsing)
            price_match = re.search(
                r'"regularMarketPrice":\{"raw":([\d.]+)', 
                html
            )
            if not price_match:
                raise FinanceError(f"Could not parse price from Yahoo for {symbol}")
            
            price = float(price_match.group(1))
            
            # Extract change
            change_match = re.search(
                r'"regularMarketChange":\{"raw":(-?[\d.]+)', 
                html
            )
            change = float(change_match.group(1)) if change_match else 0
            
            # Extract change percent
            pct_match = re.search(
                r'"regularMarketChangePercent":\{"raw":(-?[\d.]+)', 
                html
            )
            change_pct = float(pct_match.group(1)) if pct_match else 0
            
            return {
                "name": symbol.upper(),
                "price": price,
                "change": change,
                "change_percent": change_pct,
                "currency": "USD"
            }
            
        except requests.Timeout:
            raise FinanceTimeoutError(f"Yahoo Finance timed out for {symbol}")
        except requests.RequestException as e:
            raise FinanceError(f"Yahoo Finance request failed: {e}")
    
    def _format_stock_response(self, result):
        """Format stock price result into natural language."""
        change_str = ""
        if result.change is not None and result.change != 0:
            direction = "up" if result.change > 0 else "down"
            change_str = f", {direction} ${abs(result.change):.2f}"
            
            if result.change_percent is not None:
                change_str += f" ({abs(result.change_percent):.1f}%)"
        
        return (
            f"The current price of {result.symbol} "
            f"{f'({result.name})' if result.name else ''} "
            f"is ${result.price:.2f}{change_str}. "
            f"Data retrieved from {result.source}."
        )
