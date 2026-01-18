"""
Claude-powered prospect scoring
Uses Claude to evaluate prospects against investment thesis
"""

import logging
import os
from typing import Dict
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeScorer:
    """Score prospects using Claude AI"""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def score_prospect(self, prospect: Dict) -> Dict:
        """Score a prospect using Claude"""
        try:
            logger.info(f"Scoring prospect with Claude: {prospect.get('name')}")
            
            # Build prompt for Claude
            prompt = self._build_scoring_prompt(prospect)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            score_data = self._parse_claude_response(response.content[0].text)
            
            logger.info(f"Claude score: {score_data['overall_score']}/100")
            return score_data
            
        except Exception as e:
            logger.error(f"Error scoring with Claude: {str(e)}")
            # Return default scores on error
            return {
                'overall_score': 50,
                'founder_score': 50,
                'thesis_fit_score': 50,
                'timing_score': 50,
                'signal_strength_score': 50,
                'priority': 'Medium',
                'reasoning': f'Error during scoring: {str(e)}'
            }
    
    def _build_scoring_prompt(self, prospect: Dict) -> str:
        """Build the scoring prompt for Claude"""
        return f"""You are evaluating a potential investment prospect for a pre-seed/seed stage VC fund focused on Chicago-area B2B SaaS and developer tools.

PROSPECT DATA:
Name: {prospect.get('name', 'Unknown')}
Location: {prospect.get('location', 'Unknown')}
Source: {prospect.get('source', 'Unknown')}
Bio: {prospect.get('bio', 'N/A')}
Company: {prospect.get('company', 'Unknown')}
GitHub: {prospect.get('github_url', 'N/A')}
Twitter: {prospect.get('twitter_url', 'N/A')}
LinkedIn: {prospect.get('linkedin_url', 'N/A')}
Website: {prospect.get('blog', prospect.get('website', 'N/A'))}
Signals: {prospect.get('signals', 'None')}

INVESTMENT THESIS:
- Stage: Pre-seed to Seed ($250K-$1M checks)
- Focus: B2B SaaS, developer tools, AI/ML applications, infrastructure, productivity
- Founder qualities: Technical founder, domain expertise, clear problem articulation, scrappy/resourceful, Chicago/Midwest connection

Please score this prospect on four dimensions (0-100 each):

1. FOUNDER QUALITY (0-100): Technical ability, building experience, domain expertise
2. THESIS FIT (0-100): How well does their company/idea fit our investment focus?
3. TIMING (0-100): Are they at the right stage? Building something now vs just tweeting?
4. SIGNAL STRENGTH (0-100): Quality of their activity/launches/community engagement

Respond in EXACTLY this format:
FOUNDER_SCORE: [0-100]
THESIS_FIT_SCORE: [0-100]
TIMING_SCORE: [0-100]
SIGNAL_STRENGTH_SCORE: [0-100]
OVERALL_SCORE: [0-100]
PRIORITY: [High/Medium/Low]
REASONING: [2-3 sentence explanation]"""
    
    def _parse_claude_response(self, response_text: str) -> Dict:
        """Parse Claude's scoring response"""
        try:
            scores = {}
            
            # Extract scores using simple parsing
            for line in response_text.split('\n'):
                if 'FOUNDER_SCORE:' in line:
                    scores['founder_score'] = int(line.split(':')[1].strip())
                elif 'THESIS_FIT_SCORE:' in line:
                    scores['thesis_fit_score'] = int(line.split(':')[1].strip())
                elif 'TIMING_SCORE:' in line:
                    scores['timing_score'] = int(line.split(':')[1].strip())
                elif 'SIGNAL_STRENGTH_SCORE:' in line:
                    scores['signal_strength_score'] = int(line.split(':')[1].strip())
                elif 'OVERALL_SCORE:' in line:
                    scores['overall_score'] = int(line.split(':')[1].strip())
                elif 'PRIORITY:' in line:
                    scores['priority'] = line.split(':')[1].strip()
                elif 'REASONING:' in line:
                    scores['reasoning'] = line.split(':', 1)[1].strip()
            
            # Validate we got all scores
            required = ['overall_score', 'founder_score', 'thesis_fit_score', 
                       'timing_score', 'signal_strength_score', 'priority', 'reasoning']
            
            for field in required:
                if field not in scores:
                    logger.warning(f"Missing field in Claude response: {field}")
                    # Provide defaults
                    if field == 'priority':
                        scores[field] = 'Medium'
                    elif field == 'reasoning':
                        scores[field] = 'Incomplete scoring response'
                    else:
                        scores[field] = 50
            
            return scores
            
        except Exception as e:
            logger.error(f"Error parsing Claude response: {str(e)}")
            return {
                'overall_score': 50,
                'founder_score': 50,
                'thesis_fit_score': 50,
                'timing_score': 50,
                'signal_strength_score': 50,
                'priority': 'Medium',
                'reasoning': 'Error parsing scoring response'
            }
