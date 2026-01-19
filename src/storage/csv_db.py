"""
CSV file database for storing prospects
Simple, reliable, no API dependencies
"""

import logging
import os
import csv
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVDatabase:
    """CSV file as a database for prospects"""

    def __init__(self, filepath='prospects.csv'):
        """Initialize CSV database"""
        self.filepath = filepath

        # Column headers
        self.headers = [
            'Date Added',
            'Name',
            'Email',
            'Location',
            'Company',
            'Title',
            'LinkedIn',
            'Twitter',
            'GitHub',
            'Website',
            'Source',
            'Bio',
            'Signals',
            'Overall Score',
            'Founder Score',
            'Thesis Fit',
            'Timing Score',
            'Signal Score',
            'Priority',
            'Reasoning'
        ]

        # Create file with headers if it doesn't exist
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)
            logger.info(f"Created new CSV database: {self.filepath}")
        else:
            logger.info(f"Using existing CSV database: {self.filepath}")

    def add_prospect(self, prospect: Dict) -> bool:
        """
        Add a prospect to the CSV file
        Returns True if new, False if duplicate
        """
        try:
            # Check for duplicates (by name or email)
            if self._is_duplicate(prospect):
                logger.info(f"Duplicate prospect: {prospect.get('name')}")
                return False

            # Convert signals list to string if needed
            signals = prospect.get('signals', '')
            if isinstance(signals, list):
                signals = ' | '.join(str(s) for s in signals if s)

            # Prepare row data
            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                prospect.get('name', ''),
                prospect.get('email', ''),
                prospect.get('location', ''),
                prospect.get('company', ''),
                prospect.get('title', ''),
                prospect.get('linkedin_url', ''),
                prospect.get('twitter_url', prospect.get('twitter_handle', '')),
                prospect.get('github_url', ''),
                prospect.get('blog', prospect.get('website', '')),
                prospect.get('source', ''),
                prospect.get('bio', '')[:500],  # Limit bio length
                signals,
                prospect.get('overall_score', ''),
                prospect.get('founder_score', ''),
                prospect.get('thesis_fit_score', ''),
                prospect.get('timing_score', ''),
                prospect.get('signal_strength_score', ''),
                prospect.get('priority', ''),
                prospect.get('reasoning', '')
            ]

            # Append to CSV
            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)

            logger.info(f"✅ Added prospect to CSV: {prospect.get('name')}")
            return True

        except Exception as e:
            logger.error(f"Error adding prospect to CSV: {str(e)}")
            return False

    def _is_duplicate(self, prospect: Dict) -> bool:
        """Check if prospect already exists in CSV"""
        try:
            prospect_name = prospect.get('name', '').lower().strip()
            prospect_email = prospect.get('email', '').lower().strip()

            # Read all existing prospects
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_name = row.get('Name', '').lower().strip()
                    existing_email = row.get('Email', '').lower().strip()

                    # Check for name match
                    if prospect_name and prospect_name == existing_name:
                        return True

                    # Check for email match
                    if prospect_email and prospect_email == existing_email:
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return False

    def get_all_prospects(self) -> List[Dict]:
        """Get all prospects from the CSV"""
        try:
            prospects = []
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                prospects = list(reader)
            return prospects
        except Exception as e:
            logger.error(f"Error getting prospects: {str(e)}")
            return []

    def get_stats(self) -> Dict:
        """Get statistics about prospects in CSV"""
        try:
            prospects = self.get_all_prospects()

            stats = {
                'total': len(prospects),
                'high_priority': len([p for p in prospects if p.get('Priority') == 'HIGH']),
                'medium_priority': len([p for p in prospects if p.get('Priority') == 'MEDIUM']),
                'low_priority': len([p for p in prospects if p.get('Priority') == 'LOW'])
            }

            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {'total': 0, 'high_priority': 0, 'medium_priority': 0, 'low_priority': 0}
