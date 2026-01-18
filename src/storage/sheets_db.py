"""
Google Sheets database for storing prospects
"""

import logging
import os
import json
from typing import Dict, List
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleSheetsDB:
    """Google Sheets as a database for prospects"""
    
    def __init__(self):
        """Initialize Google Sheets connection"""
        try:
            # Get credentials from environment variable
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not creds_json:
                raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable not set")
            
            # Parse JSON credentials
            creds_dict = json.loads(creds_json)
            
            # Create credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
            # Initialize gspread client
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            sheet_id = os.getenv('GOOGLE_SHEET_ID')
            if not sheet_id:
                raise ValueError("GOOGLE_SHEET_ID environment variable not set")
            
            self.spreadsheet = self.client.open_by_key(sheet_id)
            
            # Get or create the prospects worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet('Prospects')
            except gspread.WorksheetNotFound:
                logger.info("Creating 'Prospects' worksheet...")
                self.worksheet = self.spreadsheet.add_worksheet(title='Prospects', rows=1000, cols=20)
                self._setup_headers()
            
            logger.info("✅ Connected to Google Sheets successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {str(e)}")
            raise
    
    def _setup_headers(self):
        """Set up column headers"""
        headers = [
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
        
        self.worksheet.update('A1:T1', [headers])
        logger.info("Set up worksheet headers")
    
    def add_prospect(self, prospect: Dict) -> bool:
        """
        Add a prospect to the sheet
        Returns True if new, False if duplicate
        """
        try:
            # Check for duplicates (by name or email)
            if self._is_duplicate(prospect):
                logger.info(f"Duplicate prospect: {prospect.get('name')}")
                return False
            
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
                prospect.get('signals', ''),
                prospect.get('overall_score', ''),
                prospect.get('founder_score', ''),
                prospect.get('thesis_fit_score', ''),
                prospect.get('timing_score', ''),
                prospect.get('signal_strength_score', ''),
                prospect.get('priority', ''),
                prospect.get('reasoning', '')
            ]
            
            # Append to sheet
            self.worksheet.append_row(row)
            logger.info(f"✅ Added prospect to sheet: {prospect.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding prospect to sheet: {str(e)}")
            return False
    
    def _is_duplicate(self, prospect: Dict) -> bool:
        """Check if prospect already exists"""
        try:
            # Get all names and emails from column B and C
            names = self.worksheet.col_values(2)[1:]  # Skip header
            emails = self.worksheet.col_values(3)[1:]  # Skip header
            
            prospect_name = prospect.get('name', '').lower().strip()
            prospect_email = prospect.get('email', '').lower().strip()
            
            # Check for name match
            if prospect_name and prospect_name in [n.lower().strip() for n in names if n]:
                return True
            
            # Check for email match
            if prospect_email and prospect_email in [e.lower().strip() for e in emails if e]:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return False
    
    def get_all_prospects(self) -> List[Dict]:
        """Get all prospects from the sheet"""
        try:
            records = self.worksheet.get_all_records()
            return records
        except Exception as e:
            logger.error(f"Error getting prospects: {str(e)}")
            return []
