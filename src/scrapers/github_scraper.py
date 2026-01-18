"""
GitHub scraper to find technical founders in Chicago
"""

import logging
import requests
import os
from typing import List, Dict
import time

logger = logging.getLogger(__name__)


class GitHubScraper:
    """Scrapes GitHub for Chicago-based developers/founders"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}' if self.token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
    
    def scrape(self) -> List[Dict]:
        """Search GitHub for Chicago developers"""
        prospects = []
        
        # Search queries for Chicago founders/developers
        queries = [
            'location:Chicago followers:>10',
            'location:Illinois followers:>20',
            'location:"Chicago, IL" repos:>5'
        ]
        
        for query in queries:
            try:
                logger.info(f"Searching GitHub: {query}")
                results = self._search_users(query, max_results=20)
                prospects.extend(results)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error searching GitHub: {str(e)}")
                continue
        
        # Deduplicate by GitHub username
        seen = set()
        unique_prospects = []
        for p in prospects:
            if p['github_username'] not in seen:
                seen.add(p['github_username'])
                unique_prospects.append(p)
        
        logger.info(f"Found {len(unique_prospects)} unique GitHub prospects")
        return unique_prospects
    
    def _search_users(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search GitHub users API"""
        try:
            url = f"{self.base_url}/search/users?q={query}&per_page={max_results}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code}")
                return []
            
            data = response.json()
            prospects = []
            
            for user in data.get('items', []):
                try:
                    # Get detailed user info
                    user_detail = self._get_user_detail(user['login'])
                    if user_detail:
                        prospects.append(user_detail)
                        time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Error processing user {user.get('login')}: {str(e)}")
                    continue
            
            return prospects
            
        except Exception as e:
            logger.error(f"Error in GitHub search: {str(e)}")
            return []
    
    def _get_user_detail(self, username: str) -> Dict:
        """Get detailed user information"""
        try:
            url = f"{self.base_url}/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            user = response.json()
            
            prospect = {
                'name': user.get('name') or username,
                'github_username': username,
                'github_url': user.get('html_url'),
                'bio': user.get('bio') or '',
                'company': user.get('company') or '',
                'location': user.get('location') or 'Chicago',
                'blog': user.get('blog') or '',
                'twitter_handle': user.get('twitter_username') or '',
                'email': user.get('email') or '',
                'source': 'GitHub',
                'signals': []
            }
            
            # Add signals
            if user.get('bio'):
                prospect['signals'].append(f"GitHub bio: {user['bio']}")
            if user.get('company'):
                prospect['signals'].append(f"Company: {user['company']}")
            
            # Check for startup signals in bio
            startup_keywords = ['founder', 'ceo', 'building', 'startup', 'launched']
            bio_lower = (user.get('bio') or '').lower()
            if any(keyword in bio_lower for keyword in startup_keywords):
                prospect['signals'].append('Startup keywords in bio')
            
            return prospect
            
        except Exception as e:
            logger.error(f"Error getting user detail for {username}: {str(e)}")
            return None
