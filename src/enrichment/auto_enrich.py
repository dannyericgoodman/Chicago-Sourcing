"""
Lightweight automatic enrichment using free/cheap sources
No Proxycurl needed - uses public APIs and scraping
"""
import requests
import logging
import re
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class AutoEnricher:
    """Automatically enriches prospects with publicly available data"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info("Auto-enricher initialized")

    def enrich_prospect(self, prospect: Dict) -> Dict:
        """
        Enrich a prospect with additional data from free sources
        Returns enriched prospect dict
        """
        enriched = prospect.copy()

        name = prospect.get('name', '')
        logger.info(f"Enriching prospect: {name}")

        # Try to find email if not present
        if not enriched.get('email'):
            email = self._find_email(prospect)
            if email:
                enriched['email'] = email
                logger.info(f"Found email for {name}: {email}")

        # Try to find LinkedIn if not present
        if not enriched.get('linkedin_url'):
            linkedin = self._find_linkedin(prospect)
            if linkedin:
                enriched['linkedin_url'] = linkedin
                logger.info(f"Found LinkedIn for {name}: {linkedin}")

        # Enrich GitHub profile if username exists
        if enriched.get('github_username'):
            github_data = self._enrich_github(enriched['github_username'])
            if github_data:
                enriched['github_enrichment'] = github_data

        # Enrich Twitter profile if handle exists
        if enriched.get('twitter_handle'):
            twitter_data = self._enrich_twitter(enriched['twitter_handle'])
            if twitter_data:
                enriched['twitter_enrichment'] = twitter_data

        # Try to infer current company/title from signals
        if not enriched.get('current_company'):
            company, title = self._infer_current_role(prospect)
            if company:
                enriched['current_company'] = company
            if title:
                enriched['current_title'] = title

        return enriched

    def _find_email(self, prospect: Dict) -> Optional[str]:
        """Try to find email from various sources"""

        # Check GitHub profile (if username exists)
        github_username = prospect.get('github_username')
        if github_username:
            try:
                # GitHub API (public profile)
                response = self.session.get(
                    f"https://api.github.com/users/{github_username}",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    email = data.get('email')
                    if email and self._is_valid_email(email):
                        return email
            except Exception as e:
                logger.debug(f"Error fetching GitHub email: {e}")

        # Check signals for email mentions
        signals = prospect.get('signals', [])
        for signal in signals:
            # Handle signals as strings (they're just text snippets)
            if isinstance(signal, str):
                email = self._extract_email_from_text(signal)
                if email:
                    return email
            # Legacy support if signals are dicts
            elif isinstance(signal, dict):
                signal_data = signal.get('signal_data', {})
                for field in ['tweet_text', 'comment', 'github_bio', 'text']:
                    text = signal_data.get(field, '')
                    email = self._extract_email_from_text(text)
                    if email:
                        return email

        return None

    def _find_linkedin(self, prospect: Dict) -> Optional[str]:
        """Try to find LinkedIn URL from various sources"""

        # Check GitHub bio
        github_username = prospect.get('github_username')
        if github_username:
            try:
                response = self.session.get(
                    f"https://api.github.com/users/{github_username}",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    bio = data.get('bio', '') or ''
                    blog = data.get('blog', '') or ''

                    # Check for LinkedIn URL in bio or blog field
                    linkedin = self._extract_linkedin_from_text(bio + ' ' + blog)
                    if linkedin:
                        return linkedin
            except Exception as e:
                logger.debug(f"Error fetching GitHub profile: {e}")

        # Check signals
        signals = prospect.get('signals', [])
        for signal in signals:
            # Handle signals as strings (they're just text snippets)
            if isinstance(signal, str):
                linkedin = self._extract_linkedin_from_text(signal)
                if linkedin:
                    return linkedin
            # Legacy support if signals are dicts
            elif isinstance(signal, dict):
                signal_data = signal.get('signal_data', {})
                for field in ['tweet_text', 'comment', 'github_bio', 'text']:
                    text = signal_data.get(field, '')
                    linkedin = self._extract_linkedin_from_text(text)
                    if linkedin:
                        return linkedin

        return None

    def _enrich_github(self, username: str) -> Dict:
        """Get additional GitHub profile data"""
        try:
            response = self.session.get(
                f"https://api.github.com/users/{username}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'bio': data.get('bio'),
                    'company': data.get('company'),
                    'location': data.get('location'),
                    'blog': data.get('blog'),
                    'twitter': data.get('twitter_username'),
                    'public_repos': data.get('public_repos'),
                    'followers': data.get('followers'),
                    'created_at': data.get('created_at')
                }
        except Exception as e:
            logger.debug(f"Error enriching GitHub profile: {e}")

        return {}

    def _enrich_twitter(self, handle: str) -> Dict:
        """Get Twitter profile data (limited without API)"""
        # Without Twitter API, we're limited
        # Could use Nitter to scrape profile, but skip for now
        return {
            'handle': handle.strip('@'),
            'url': f"https://twitter.com/{handle.strip('@')}"
        }

    def _infer_current_role(self, prospect: Dict) -> tuple:
        """Try to infer current company and title from signals"""
        company = None
        title = None

        # Check GitHub company field
        github_enrichment = prospect.get('github_enrichment', {})
        github_company = github_enrichment.get('company', '')
        if github_company:
            # Clean up GitHub company (often has @company format)
            company = github_company.strip('@').strip()

        # Check signals for mentions of current role
        signals = prospect.get('signals', [])
        for signal in signals:
            text = ''

            # Handle signals as strings (they're just text snippets)
            if isinstance(signal, str):
                text = signal
            # Legacy support if signals are dicts
            elif isinstance(signal, dict):
                signal_data = signal.get('signal_data', {})
                for field in ['tweet_text', 'comment', 'github_bio', 'text']:
                    text = signal_data.get(field, '')
                    if text:
                        break

            if not text:
                continue

            # Pattern: "Senior Engineer at Stripe"
            match = re.search(r'([\w\s]+(?:Engineer|Developer|Designer|PM|Manager|Director|Founder|CEO|CTO))[\s@]+at[\s@]+([\w\s]+)', text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                company = match.group(2).strip()
                break

        return company, title

    def _extract_email_from_text(self, text: str) -> Optional[str]:
        """Extract email from text"""
        if not text:
            return None

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)

        if match:
            email = match.group(0)
            if self._is_valid_email(email):
                return email

        return None

    def _extract_linkedin_from_text(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from text"""
        if not text:
            return None

        # Pattern: linkedin.com/in/username
        linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9-]+)'
        match = re.search(linkedin_pattern, text)

        if match:
            username = match.group(1)
            return f"https://www.linkedin.com/in/{username}"

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format and filter out common false positives"""
        if not email:
            return False

        # Filter out example/placeholder emails
        invalid_domains = [
            'example.com', 'test.com', 'domain.com',
            'email.com', 'mail.com', 'placeholder.com'
        ]

        domain = email.split('@')[1].lower() if '@' in email else ''
        if domain in invalid_domains:
            return False

        # Basic format check
        if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
            return True

        return False
