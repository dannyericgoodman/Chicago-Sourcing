"""
Chicago Founder Sourcing Engine - Fully Automated
Runs daily to discover, enrich, score, and store prospects
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List
import yaml

# Import our modules
from src.scrapers.twitter_scraper import TwitterScraper
from src.scrapers.github_scraper import GitHubScraper
from src.scrapers.hn_scraper import HackerNewsScraper
from src.scrapers.producthunt_scraper import ProductHuntScraper
from src.enrichment.auto_enrich import AutoEnricher
from src.scoring.claude_scorer import ClaudeScorer
from src.storage.sheets_db import GoogleSheetsDB
from src.output.slack_notify import SlackNotifier

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sourcing_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SourcingEngine:
    """Fully automated sourcing engine - hands-off operation"""

    def __init__(self):
        """Initialize all components"""
        logger.info("🚀 Starting Chicago Founder Sourcing Engine (Fully Automated)")

        # Load config
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize components
        self.scrapers = self._init_scrapers()
        self.enricher = AutoEnricher()
        self.scorer = ClaudeScorer()
        self.db = GoogleSheetsDB()
        self.slack = SlackNotifier()

        logger.info("✅ All components initialized")

    def _init_scrapers(self) -> dict:
        """Initialize all scrapers"""
        return {
            'twitter': TwitterScraper(),
            'github': GitHubScraper(),
            'hackernews': HackerNewsScraper(),
            'producthunt': ProductHuntScraper()
        }

    def scrape_all_sources(self) -> List[Dict]:
        """Scrape all configured sources for prospects"""
        all_prospects = []

        for source_name, scraper in self.scrapers.items():
            try:
                logger.info(f"🔍 Scraping {source_name}...")
                prospects = scraper.scrape()
                logger.info(f"✅ Found {len(prospects)} prospects from {source_name}")
                all_prospects.extend(prospects)
            except Exception as e:
                logger.error(f"❌ Error scraping {source_name}: {str(e)}")
                continue

        logger.info(f"📊 Total prospects found: {len(all_prospects)}")
        return all_prospects

    def store_prospects(self, prospects: List[Dict]) -> dict:
        """
        Store prospects with automatic enrichment and scoring
        This is the fully automated pipeline!
        """
        stats = {
            'total': len(prospects),
            'new': 0,
            'duplicates': 0,
            'enriched': 0,
            'scored': 0,
            'high_priority': 0
        }

        for i, prospect in enumerate(prospects, 1):
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing prospect {i}/{len(prospects)}: {prospect.get('name', 'Unknown')}")

                # Step 1: Auto-enrich with free data sources
                logger.info("🔄 Auto-enriching prospect...")
                enriched_prospect = self.enricher.enrich_prospect(prospect)
                stats['enriched'] += 1
                logger.info(f"✅ Enriched: Found {enriched_prospect.get('email', 'no email')}")

                # Step 2: Auto-score with Claude
                logger.info("🤖 Auto-scoring with Claude...")
                score_data = self.scorer.score_prospect(enriched_prospect)
                enriched_prospect.update(score_data)
                stats['scored'] += 1
                logger.info(f"✅ Scored: {score_data['overall_score']}/100 - {score_data['priority']} priority")

                # Step 3: Store in Google Sheets
                is_new = self.db.add_prospect(enriched_prospect)

                if is_new:
                    stats['new'] += 1
                    logger.info(f"✅ Added to Google Sheets as new prospect")

                    # Step 4: Track high priority prospects
                    if score_data['priority'] == 'High':
                        stats['high_priority'] += 1
                        logger.info(f"⭐ HIGH PRIORITY PROSPECT!")
                else:
                    stats['duplicates'] += 1
                    logger.info(f"⚠️  Duplicate - already in database")

            except Exception as e:
                logger.error(f"❌ Error processing prospect: {str(e)}")
                continue

        return stats

    def run(self):
        """Main execution - fully automated!"""
        try:
            start_time = datetime.now()
            logger.info(f"\n{'='*80}")
            logger.info(f"🎯 SOURCING RUN STARTED: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*80}\n")

            # Step 1: Scrape all sources
            prospects = self.scrape_all_sources()

            if not prospects:
                logger.warning("⚠️  No prospects found. Exiting.")
                return

            # Step 2: Store with auto-enrichment and auto-scoring
            logger.info("\n" + "="*80)
            logger.info("🔄 STARTING AUTO-ENRICHMENT AND AUTO-SCORING PIPELINE")
            logger.info("="*80 + "\n")

            stats = self.store_prospects(prospects)

            # Final summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("\n" + "="*80)
            logger.info("📊 SOURCING RUN COMPLETE!")
            logger.info("="*80)
            logger.info(f"⏱️  Duration: {duration:.1f} seconds")
            logger.info(f"📥 Total prospects scraped: {stats['total']}")
            logger.info(f"✨ New prospects added: {stats['new']}")
            logger.info(f"🔄 Duplicates skipped: {stats['duplicates']}")
            logger.info(f"🔍 Auto-enriched: {stats['enriched']}")
            logger.info(f"🤖 Auto-scored: {stats['scored']}")
            logger.info(f"⭐ High priority: {stats['high_priority']}")
            logger.info("="*80)
            logger.info(f"✅ Check your Google Sheet for results!")
            logger.info(f"🔗 https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SHEET_ID')}")
            logger.info("="*80 + "\n")

        except Exception as e:
            logger.error(f"❌ Fatal error in sourcing engine: {str(e)}", exc_info=True)
            raise


def main():
    """Entry point"""
    # Run the engine
    engine = SourcingEngine()
    engine.run()


if __name__ == "__main__":
    main()
