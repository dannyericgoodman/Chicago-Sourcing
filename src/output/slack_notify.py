"""
Slack notifications (DISABLED - user doesn't use Slack)
"""

import logging

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack notifications - disabled for this setup"""
    
    def __init__(self):
        # Slack notifications disabled - check Google Sheet directly
        self.enabled = False
        self.webhook_url = None
        logger.info("Slack notifications disabled (check Google Sheet for results)")
    
    def notify_high_priority_prospect(self, prospect):
        """Would notify about high priority prospect, but disabled"""
        logger.info(f"High priority prospect (Slack disabled): {prospect.get('name')}")
        pass
    
    def send_daily_summary(self, stats):
        """Would send daily summary, but disabled"""
        logger.info(f"Daily summary (Slack disabled): {stats}")
        pass
