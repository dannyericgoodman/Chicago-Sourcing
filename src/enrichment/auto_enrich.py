"""
Auto-enrichment using free data sources
Finds emails, LinkedIn, and additional data without paid APIs
"""

import logging
import re
import requests
from typing import Dict
import time

logger = logging.getLogger(__name__)


class AutoEnricher:
    """Automatically enriches prospects with publicly available data"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def enrich_prospect(self, prospect: Dict) -> Dict:
        """Enrich a prospect with additional data from free sources"""
        try:
            logger.info(f"Enriching prospect: {prospect.get('name', 'Unknown')}")
            
            # Try to find email from GitHub profile
            if prospect.get('github_username'):
                email = self._find_email_from_github(prospect['github_username'])
                if email:
                    prospect['email'] = email
            
            # Try to find LinkedIn from GitHub bio or Twitter
            if prospect.get('github_url') or prospect.get('twitter_url'):
                linkedin = self._find_linkedin_url(prospect)
                if linkedin:
                    prospect['linkedin_url'] = linkedin
            
            # Infer company/title from bio and signals
            if not prospect.get('company'):
                company = self._infer_company(prospect)
                if company:
                    prospect['company'] = company
            
            # Clean and normalize data
            prospect = self._clean_prospect_data(prospect)
            
            logger.info(f"Enrichment complete for {prospect.get('name')}")
            return prospect
            
        except Exception as e:
            logger.error(f"Error enriching prospect: {str(e)}")
            return prospect
    
    def _find_email_from_github(self, username: str) -> str:
        """Try to find email from GitHub commits"""
        try:
            # GitHub API often exposes commit email
            url = f"https://api.github.com/users/{username}/events/public"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                events = response.json()
                
                for event in events[:10]:  # Check last 10 events
                    if event.get('type') == 'PushEvent':
                        commits = event.get('payload', {}).get('commits', [])
                        for commit in commits:
                            email = commit.get('author', {}).get('email')
                            if email and '@' in email and 'noreply' not in email:
                                logger.info(f"Found email from GitHub: {email}")
                                return email
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding email from GitHub: {str(e)}")
            return None
    
    def _find_linkedin_url(self, prospect: Dict) -> str:
        """Try to extract LinkedIn URL from bio or social links"""
        try:
            # Check bio for LinkedIn URL
            bio = prospect.get('bio', '')
            linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', bio)
            if linkedin_match:
                return f"https://linkedin.com/in/{linkedin_match.group(1)}"
            
            # Check if they have a blog/website with LinkedIn
            if prospect.get('blog'):
                try:
                    response = requests.get(prospect['blog'], headers=self.headers, timeout=5)
                    linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', response.text)
                    if linkedin_match:
                        return f"https://linkedin
