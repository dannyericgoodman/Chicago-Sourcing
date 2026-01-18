"""
Hacker News scraper using Algolia API (free)
"""

import logging
import requests
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HackerNewsScraper:
    """Scrapes Hacker News for Show HN and Launch HN posts"""
    
    def __init__(self):
        self.algolia_url = "http://hn.algolia.com/api/v1/search"
    
    def scrape(self) -> List[Dict]:
        """Search Hacker News for launch posts"""
        prospects = []
        
        queries = [
            "Show HN",
            "Launch HN",
            "Ask HN: Feedback"
        ]
        
        for query in queries:
            try:
                logger.info(f"Searching Hacker News for: {query}")
                results = self._search_hn(query)
                prospects.extend(results)
            except Exception as e:
                logger.error(f"Error searching HN for '{query}': {str(e)}")
                continue
        
        # Deduplicate by author
        seen = set()
        unique_prospects = []
        for p in prospects:
            if p['hn_username'] not in seen:
                seen.add(p['hn_username'])
                unique_prospects.append(p)
        
        logger.info(f"Found {len(unique_prospects)} unique HN prospects")
        return unique_prospects
    
    def _search_hn(self, query: str, max_results: int = 30) -> List[Dict]:
        """Search HN using Algolia API"""
        try:
            # Search for recent posts (last 30 days)
            params = {
                'query': query,
                'tags': 'story',
                'numericFilters': f'created_at_i>{int((datetime.now() - timedelta(days=30)).timestamp())}',
                'hitsPerPage': max_results
            }
            
            response = requests.get(self.algolia_url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"HN Algolia API error: {response.status_code}")
                return []
            
            data = response.json()
            prospects = []
            
            for hit in data.get('hits', []):
                try:
                    author = hit.get('author')
                    title = hit.get('title', '')
                    url = hit.get('url', '')
                    
                    if not author:
                        continue
                    
                    prospect = {
                        'name': author,
                        'hn_username': author,
                        'hn_url': f"https://news.ycombinator.com/user?id={author}",
                        'bio': title[:500],
                        'website': url,
                        'source': 'Hacker News',
                        'location': 'Unknown',  # HN doesn't expose location
                        'signals': [
                            f"HN Post: {title}",
                            f"Posted on: {datetime.fromtimestamp(hit.get('created_at_i', 0)).strftime('%Y-%m-%d')}"
                        ]
                    }
                    
                    # Add points/comments as signals
                    if hit.get('points'):
                        prospect['signals'].append(f"{hit['points']} points")
                    if hit.get('num_comments'):
                        prospect['signals'].append(f"{hit['num_comments']} comments")
                    
                    prospects.append(prospect)
                    
                except Exception as e:
                    logger.debug(f"Error parsing HN hit: {str(e)}")
                    continue
            
            return prospects
            
        except Exception as e:
            logger.error(f"Error searching HN: {str(e)}")
            return []
