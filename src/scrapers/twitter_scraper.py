"""
Twitter/X scraper using Nitter (free alternative to Twitter API)
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time

logger = logging.getLogger(__name__)


class TwitterScraper:
    """Scrapes Twitter for Chicago founder activity using Nitter"""
    
    def __init__(self):
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.privacydev.net",
            "https://nitter.poast.org"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape(self) -> List[Dict]:
        """Scrape Twitter for Chicago founders"""
        prospects = []
        
        search_queries = [
            "building in public chicago",
            "startup founder chicago",
            "just launched chicago",
            "YC chicago"
        ]
        
        for query in search_queries:
            try:
                logger.info(f"Searching Twitter for: {query}")
                results = self._search_nitter(query)
                prospects.extend(results)
                time.sleep(2)  # Be nice to Nitter
            except Exception as e:
                logger.error(f"Error searching Twitter for '{query}': {str(e)}")
                continue
        
        # Deduplicate by username
        seen = set()
        unique_prospects = []
        for p in prospects:
            if p['twitter_handle'] not in seen:
                seen.add(p['twitter_handle'])
                unique_prospects.append(p)
        
        logger.info(f"Found {len(unique_prospects)} unique Twitter prospects")
        return unique_prospects
    
    def _search_nitter(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Nitter instances for tweets"""
        for instance in self.nitter_instances:
            try:
                url = f"{instance}/search?f=tweets&q={query.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    return self._parse_nitter_results(response.text, max_results)
            except Exception as e:
                logger.warning(f"Failed to query {instance}: {str(e)}")
                continue
        
        logger.warning(f"All Nitter instances failed for query: {query}")
        return []
    
    def _parse_nitter_results(self, html: str, max_results: int) -> List[Dict]:
        """Parse Nitter HTML to extract prospect info"""
        soup = BeautifulSoup(html, 'html.parser')
        prospects = []
        
        tweets = soup.find_all('div', class_='timeline-item', limit=max_results)
        
        for tweet in tweets:
            try:
                # Extract username
                username_elem = tweet.find('a', class_='username')
                if not username_elem:
                    continue
                
                username = username_elem.text.strip().replace('@', '')
                
                # Extract full name
                fullname_elem = tweet.find('a', class_='fullname')
                name = fullname_elem.text.strip() if fullname_elem else username
                
                # Extract tweet text
                tweet_content = tweet.find('div', class_='tweet-content')
                bio = tweet_content.text.strip() if tweet_content else ""
                
                prospect = {
                    'name': name,
                    'twitter_handle': username,
                    'twitter_url': f"https://twitter.com/{username}",
                    'bio': bio[:500],  # Limit bio length
                    'source': 'Twitter',
                    'location': 'Chicago, IL',
                    'signals': [bio[:200]]
                }
                
                prospects.append(prospect)
                
            except Exception as e:
                logger.debug(f"Error parsing tweet: {str(e)}")
                continue
        
        return prospects
