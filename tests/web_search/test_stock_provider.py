"""Tests for StockPriceProvider."""

import pytest
from unittest.mock import patch, MagicMock
from web_search.providers.finance import StockPriceProvider


class TestStockPriceProvider:
    def test_supports_stock_query(self):
        provider = StockPriceProvider()
        
        class MockRequest:
            original_query = "What's the stock price of AAPL?"
        
        assert provider.supports(MockRequest())

    def test_supports_crypto_query(self):
        provider = StockPriceProvider()
        
        class MockRequest:
            original_query = "Bitcoin price today"
        
        assert provider.supports(MockRequest())

    def test_does_not_support_weather(self):
        provider = StockPriceProvider()
        
        class MockRequest:
            original_query = "What's the weather like?"
        
        assert not provider.supports(MockRequest())

    @patch('web_search.providers.finance.requests.get')
    def test_extract_symbol_from_ticker(self, mock_get):
        provider = StockPriceProvider()
        symbol = provider._extract_symbol("What's AAPL stock price?")
        assert symbol == "AAPL"

    @patch('web_search.providers.finance.requests.get')
    def test_extract_symbol_from_company_name(self, mock_get):
        provider = StockPriceProvider()
        symbol = provider._extract_symbol("What's Apple's stock price?")
        assert symbol == "AAPL"
