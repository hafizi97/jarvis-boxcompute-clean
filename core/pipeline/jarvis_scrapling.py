#!/usr/bin/env python3
"""
JARVIS Scrapling Wrapper Module
Exposes the local Scrapling setup located at ~/Jarvis/tools/scrapling
as a callable tool/module for all OpenCode agents and the pipeline.
"""

import sys
import os
import json

# Add scrapling virtual environment site-packages to path
SCRAPLING_SITE_PACKAGES = "/home/faiz/Jarvis/tools/scrapling/lib/python3.13/site-packages"
if SCRAPLING_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, SCRAPLING_SITE_PACKAGES)

try:
    from scrapling import Fetcher, Selector
    SCRAPLING_AVAILABLE = True
except ImportError as e:
    SCRAPLING_AVAILABLE = False
    IMPORT_ERROR = str(e)

def scrape_url(url: str, stealth: bool = True, selector_mode: str = "smart") -> dict:
    """
    Scrapes a URL using the integrated Scrapling library.
    Returns a dictionary containing status, extracted text, and meta info.
    """
    if not SCRAPLING_AVAILABLE:
        return {
            "success": False,
            "error": f"Scrapling package not available in path: {globals().get('IMPORT_ERROR', 'Unknown error')}"
        }
    
    try:
        # Fetcher handles stealth requests
        fetcher = Fetcher()
        response = fetcher.get(url)
        
        # Parse content using Selector
        selector = Selector(response.text)
        
        title_el = selector.css('title::text')
        title_text = title_el.get() if title_el else ""
        
        return {
            "success": True,
            "url": url,
            "status": response.status,
            "title": title_text,
            "text_snippet": response.text[:1000] # first 1000 chars snippet
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS Scrapling Tool")
    parser.add_argument("url", help="URL to scrape")
    args = parser.parse_args()
    
    result = scrape_url(args.url)
    print(json.dumps(result, indent=2))
