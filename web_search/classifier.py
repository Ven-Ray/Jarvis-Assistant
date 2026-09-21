"""
Intent classifier for search requests.
Uses LLM to determine if a request requires web search and generate appropriate query.
"""

import json
import re
from typing import Dict, Any


class SearchClassifier:
    """Classifies user requests to determine search intent."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def classify(self, user_command) -> Dict[str, Any]:
        """
        Classify a user request.
        
        Returns:
            dict with keys: requires_web_search (bool), search_query (str), reason (str)
        """
        if self.llm_client:
            return self._llm_classify(user_command)
        else:
            return self._keyword_fallback(user_command.lower())
    
    def _llm_classify(self, user_command) -> Dict[str, Any]:
        """Use LLM to classify intent and generate search query."""
        web_search_system_prompt = """You are a web-search intent classifier and search-query generator.

Analyze the user's request and determine whether answering it requires current, location-dependent, or externally verifiable information.

A web search is required when the request involves:
- Current or latest information
- News or recent events
- Weather or forecasts
- Sports scores, schedules, standings, or results
- Stock, share, cryptocurrency, currency, commodity, or market prices
- Product prices, availability, or inventory
- Business hours, locations, nearby places, or directions
- Travel prices, schedules, delays, or availability
- Current laws, regulations, policies, or public officials
- Any named person, company, product, place, event, or organization whose current status matters
- Any request that explicitly asks to search, look up, find, check, or verify something online

A web search is usually not required for:
- General explanations
- Mathematics
- Coding help
- Translations
- Creative writing
- Historical facts
- Stable scientific knowledge
- Opinions or general advice

If a web search is required, create one concise search query that includes the user's important keywords. Preserve names, locations, dates, tickers, products, and units. For prices, include terms such as "current price" or "latest price" when appropriate.

Return valid JSON only, using exactly this format:
{"requires_web_search": true, "search_query": "generated search query", "reason": "brief explanation"}

If no search is needed, return:
{"requires_web_search": false, "search_query": "", "reason": "brief explanation"}"""

        try:
            response = self.llm_client.chat.completions.create(
                model="default-model",
                messages=[
                    {"role": "system", "content": web_search_system_prompt},
                    {"role": "user", "content": f"User request:\n{user_command}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in markdown or extra text
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    return {
                        "requires_web_search": False,
                        "search_query": "",
                        "reason": "The model returned invalid JSON."
                    }
            
            return {
                "requires_web_search": bool(result.get("requires_web_search", False)),
                "search_query": result.get("search_query", "").strip(),
                "reason": result.get("reason", "").strip()
            }
            
        except Exception as e:
            print(f"Error classifying web search intent with LLM: {e}")
            return self._keyword_fallback(user_command.lower())
    
    def _keyword_fallback(self, command_lower) -> Dict[str, Any]:
        """Fallback keyword-based web search detection if LLM classification fails."""
        real_time_indicators = [
            "today", "tonight", "now", "currently", "current", "latest", "recent", "live",
            "this week", "this month", "right now",
            "weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy",
            "news", "breaking", "recent events", "what happened",
            "score", "scores", "result", "results", "who won", "standings", "schedule",
            "price", "cost", "rate", "value", "worth", "quote", "market", "stock",
            "shares", "crypto", "cryptocurrency", "bitcoin", "ethereum", "commodity",
            "gold", "silver", "oil", "gas",
            "available", "availability", "in stock", "open now", "closed", "status",
            "near me", "nearby", "closest", "nearest", "directions", "distance", "route", "traffic"
        ]
        
        if any(indicator in command_lower for indicator in real_time_indicators):
            return {
                "requires_web_search": True,
                "search_query": command_lower,
                "reason": "Keyword-based fallback detected real-time indicators."
            }
        
        return {
            "requires_web_search": False,
            "search_query": "",
            "reason": "No real-time indicators found in keyword fallback."
        }
