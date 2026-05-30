"""The curated reading curriculum.

Each author has an *ordered* list of must-read essays, sequenced as a learning
journey for an aspiring early-stage VC (foundations first, then sharper /
investor-specific judgment). The daily selector walks this list in order, so
each issue advances your studies rather than picking at random. Once an author's
curated list is complete, the selector dips into the rest of their archive for
breadth.

Entries are matched against the live archive *by title* (so the authoritative
URL always comes from the source site, never a hand-typed link that could rot).
`url` is kept only as a fallback for when the live pool is unavailable, and
`keys` are extra lowercase fragments to make title matching robust.
"""

from typing import Dict, List

CURRICULUM: Dict[str, List[Dict]] = {
    # ---- Paul Graham — what great founders & startups actually look like ---- #
    "paul_graham": [
        {"title": "Startup = Growth", "url": "https://paulgraham.com/growth.html",
         "keys": ["startup = growth", "startup growth"]},
        {"title": "Do Things that Don't Scale", "url": "https://paulgraham.com/ds.html",
         "keys": ["do things that don", "things that don't scale"]},
        {"title": "How to Get Startup Ideas", "url": "https://paulgraham.com/startupideas.html",
         "keys": ["how to get startup ideas"]},
        {"title": "What We Look for in Founders", "url": "https://paulgraham.com/founders.html",
         "keys": ["what we look for in founders"]},
        {"title": "Black Swan Farming", "url": "https://paulgraham.com/swan.html",
         "keys": ["black swan farming"]},
        {"title": "How to Convince Investors", "url": "https://paulgraham.com/convince.html",
         "keys": ["how to convince investors"]},
        {"title": "The 18 Mistakes That Kill Startups", "url": "https://paulgraham.com/startupmistakes.html",
         "keys": ["18 mistakes", "mistakes that kill startups"]},
        {"title": "How to Make Wealth", "url": "https://paulgraham.com/wealth.html",
         "keys": ["how to make wealth"]},
        {"title": "Relentlessly Resourceful", "url": "https://paulgraham.com/relres.html",
         "keys": ["relentlessly resourceful"]},
        {"title": "Startups in 13 Sentences", "url": "https://paulgraham.com/13sentences.html",
         "keys": ["13 sentences", "startups in 13"]},
        {"title": "Default Alive or Default Dead?", "url": "https://paulgraham.com/aord.html",
         "keys": ["default alive", "default dead"]},
        {"title": "The Anatomy of Determination", "url": "https://paulgraham.com/determination.html",
         "keys": ["anatomy of determination"]},
        {"title": "Maker's Schedule, Manager's Schedule", "url": "https://paulgraham.com/makersschedule.html",
         "keys": ["maker's schedule", "makers schedule"]},
        {"title": "How to Start a Startup", "url": "https://paulgraham.com/start.html",
         "keys": ["how to start a startup"]},
        {"title": "How to Think for Yourself", "url": "https://paulgraham.com/think.html",
         "keys": ["how to think for yourself"]},
    ],

    # ---- Bill Gurley — marketplaces, valuation discipline, unit economics ---- #
    "bill_gurley": [
        {"title": "All Markets Are Not Created Equal: 10 Factors To Consider When Evaluating Digital Marketplaces",
         "url": "https://abovethecrowd.com/2012/11/13/all-markets-are-not-created-equal-10-factors-to-consider-when-evaluating-digital-marketplaces/",
         "keys": ["all markets are not created equal"]},
        {"title": "All Revenue is Not Created Equal: The Keys to the 10X Revenue Club",
         "url": "https://abovethecrowd.com/2011/05/24/all-revenue-is-not-created-equal-the-keys-to-the-10x-revenue-club/",
         "keys": ["all revenue is not created equal", "10x revenue club"]},
        {"title": "The Dangerous Seduction of the Lifetime Value (LTV) Formula",
         "url": "https://abovethecrowd.com/2012/09/04/the-dangerous-seduction-of-the-lifetime-value-ltv-formula/",
         "keys": ["dangerous seduction", "lifetime value", "ltv formula"]},
        {"title": "How to Miss By a Mile: An Alternative Look at Uber's Potential Market Size",
         "url": "https://abovethecrowd.com/2014/07/11/how-to-miss-by-a-mile-an-alternative-look-at-ubers-potential-market-size/",
         "keys": ["how to miss by a mile"]},
        {"title": "Money Out of Nowhere: How Internet Marketplaces Unlock Economic Wealth",
         "url": "https://abovethecrowd.com/2019/02/27/money-out-of-nowhere-how-internet-marketplaces-unlock-economic-wealth/",
         "keys": ["money out of nowhere"]},
        {"title": "The Thing I Love Most About Uber",
         "url": "https://abovethecrowd.com/2018/04/19/the-thing-i-love-most-about-uber/",
         "keys": ["the thing i love most about uber"]},
        {"title": "On the Road to Recap",
         "url": "https://abovethecrowd.com/2016/04/21/on-the-road-to-recap/",
         "keys": ["on the road to recap"]},
        {"title": "Why Facebook Clearly Belongs in the 10X Revenue Club",
         "url": "https://abovethecrowd.com/2012/02/01/why-facebook-clearly-belongs-in-the-10x-revenue-club/",
         "keys": ["why facebook clearly belongs"]},
    ],

    # ---- Andrew Chen — growth, retention, network effects, PMF ---- #
    "andrew_chen": [
        {"title": "The Law of Shitty Clickthroughs",
         "url": "https://andrewchen.com/the-law-of-shitty-clickthroughs/",
         "keys": ["law of shitty clickthroughs"]},
        {"title": "Growth Hacker is the new VP Marketing",
         "url": "https://andrewchen.com/how-to-be-a-growth-hacker-an-airbnbcraigslist-case-study/",
         "keys": ["growth hacker is the new vp"]},
        {"title": "The Next Feature Fallacy",
         "url": "https://andrewchen.com/the-next-feature-fallacy-the-fallacy-that-the-next-new-feature-will-suddenly-make-people-use-your-product/",
         "keys": ["next feature fallacy"]},
        {"title": "New data shows losing 80% of mobile users is normal",
         "url": "https://andrewchen.com/new-data-shows-why-losing-80-of-your-mobile-users-is-normal-and-that-the-best-apps-do-much-better/",
         "keys": ["losing 80", "80% of mobile users", "80 of your mobile"]},
        {"title": "Minimize your Time to Product/Market Fit",
         "url": "https://andrewchen.com/ttpmf-time-to-product-market-fit/",
         "keys": ["time to product/market fit", "time to product market fit", "ttpmf"]},
        {"title": "Zero to Product/Market Fit",
         "url": "https://andrewchen.com/zero-to-productmarket-fit-presentation/",
         "keys": ["zero to product/market fit", "zero to productmarket"]},
        {"title": "What to do when growth stalls",
         "url": "https://andrewchen.com/growth-stalls/",
         "keys": ["growth stalls", "when growth stalls", "growth stall"]},
    ],
}


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def match_in_pool(entry: Dict, pool: List[Dict]) -> Dict:
    """Find the pool item that corresponds to a curriculum entry, or {}.

    Matching is title-based and forgiving: a hit on any `keys` fragment, or a
    containment match between normalized titles.
    """
    norm_keys = [_norm(k) for k in entry.get("keys", [])]
    norm_title = _norm(entry["title"])
    for item in pool:
        nt = _norm(item.get("title", ""))
        if not nt:
            continue
        if any(k and k in nt for k in norm_keys):
            return item
        if norm_title and (norm_title in nt or nt in norm_title):
            return item
    return {}
