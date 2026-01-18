"""
Product Hunt scraper using RSS feed (free, no API key needed)
"""

import logging
import feedparser
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


class ProductHuntScraper:
    """Scrapes Product Hunt for new product launches"""
    
    def __init__(self):
        self.rss_url = "https://www.producthunt.com/feed"
    
    def scrape(self) -> List[Dict]:
        """Scrape Product Hunt RSS feed for recent launches"""
        try:
            logger.info("Fetching Product Hunt RSS feed...")
            feed = feedparser.parse(self.rss_url)
            
            prospects = []
            
            for entry in feed.entries[:20]:  # Get top 20 recent products
                try:
                    title = entry.get('title', '')
                    description = entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    # Try to extract maker/founder name from description
                    # Product Hunt RSS often includes "by [name]"
                    name_match = re.search(r'by\s+([A-Za-z\s]+)', description)
                    maker_name = name_match.group(1).strip() if name_match else 'Unknown'
                    
                    prospect = {
                        'name': maker_name,
                        'product_name': title,
                        'product_url': link,
                        'bio': description[:500],
                        'source': 'Product Hunt',
                        'location': 'Unknown',
                        'signals': [
                            f"Launched: {title}",
                            f"Product Hunt: {link}"
                        ]
                    }
                    
                    prospects.append(prospect)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Product Hunt entry: {str(e)}")
                    continue
            
            logger.info(f"Found {len(prospects)} Product Hunt prospects")
            return prospects
            
        except Exception as e:
            logger.error(f"Error scraping Product Hunt: {str(e)}")
            return []
