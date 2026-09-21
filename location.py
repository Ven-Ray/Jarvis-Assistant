"""
Location detection module for Jarvis.
Uses IP geolocation via ipinfo.io API to determine user's current location.
Includes caching, timeout handling, and timezone detection.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict


class LocationDetector:
    """Detects user's current location using IP geolocation."""
    
    def __init__(self):
        self._cached_location = None
        self._cache_time = 0
        self._cache_ttl = 300  # Cache for 5 minutes
    
    def get_current_location(self, timeout: int = 10) -> Optional[Dict]:
        """
        Get the user's current location via IP geolocation.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Dict with keys: city, region, country, lat, lon, timezone, or None on failure
        """
        # Check cache first
        if self._cached_location and (time.time() - self._cache_time) < self._cache_ttl:
            return self._cached_location
        
        # TEST: Simulate failure for testing purposes
        import os
        if os.environ.get("JARVIS_TEST_LOCATION_FAIL"):
            return None
        
        try:
            # Try ipinfo.io API first
            result = self._get_ipinfo(timeout=timeout)
            if result:
                self._cache_result(result)
                return result
            
            # Fallback to ip-api.com
            result = self._get_ipapi(timeout=timeout)
            if result:
                self._cache_result(result)
                return result
            
            return None
            
        except Exception as e:
            return None
    
    def _get_ipinfo(self, timeout: int = 10) -> Optional[Dict]:
        """Get location from ipinfo.io API."""
        try:
            req = urllib.request.Request(
                "https://ipinfo.io/json",
                headers={"User-Agent": "Jarvis-Assistant/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Parse ipinfo.io response format
                location_str = data.get("loc", "")
                lat, lon = None, None
                if location_str and "," in location_str:
                    parts = location_str.split(",")
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                    except ValueError:
                        pass
                
                return {
                    "city": data.get("city", ""),
                    "region": data.get("region", ""),
                    "country": data.get("country", ""),
                    "lat": lat,
                    "lon": lon,
                    "timezone": data.get("timezone", ""),
                    "provider": "ipinfo.io"
                }
                
        except urllib.error.URLError as e:
            return None
        except Exception as e:
            return None
    
    def _get_ipapi(self, timeout: int = 10) -> Optional[Dict]:
        """Get location from ip-api.com API (fallback)."""
        try:
            req = urllib.request.Request(
                "http://ip-api.com/json/?fields=status,country,regionName,city,lat,lon,timezone",
                headers={"User-Agent": "Jarvis-Assistant/1.0"}
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get("status") != "success":
                    return None
                
                return {
                    "city": data.get("city", ""),
                    "region": data.get("regionName", ""),
                    "country": data.get("country", ""),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "timezone": data.get("timezone", ""),
                    "provider": "ip-api.com"
                }
                
        except urllib.error.URLError as e:
            return None
        except Exception as e:
            return None
    
    def _cache_result(self, result: Dict):
        """Cache the location result."""
        self._cached_location = result
        self._cache_time = time.time()
    
    def clear_cache(self):
        """Clear the cached location."""
        self._cached_location = None
        self._cache_time = 0
    
    def get_location_string(self, location: Optional[Dict]) -> str:
        """Format a location dict into a readable string for search queries."""
        if not location:
            return ""
        
        parts = []
        if location.get("city"):
            parts.append(location["city"])
        if location.get("region"):
            parts.append(location["region"])
        if location.get("country"):
            parts.append(location["country"])
        
        return ", ".join(parts)
