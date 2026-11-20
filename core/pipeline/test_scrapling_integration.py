#!/usr/bin/env python3
"""
Test Integration Script for JARVIS Scrapling Wrapper & Pipeline.
"""

import sys
import os

sys.path.insert(0, "/home/faiz/Jarvis/core/pipeline")

try:
    from jarvis_scrapling import scrape_url
    print("[TEST] Successfully imported jarvis_scrapling.")
except ImportError as e:
    print(f"[TEST ERROR] Failed to import jarvis_scrapling: {e}")
    sys.exit(1)

def test_scrape():
    print("[TEST] Running test scrape on https://example.com...")
    result = scrape_url("https://example.com")
    print(f"[TEST] Result: {result}")
    assert result.get("success") == True, "Scraping failed!"
    print("[TEST] Scrapling integration test passed successfully!")

if __name__ == "__main__":
    test_scrape()
