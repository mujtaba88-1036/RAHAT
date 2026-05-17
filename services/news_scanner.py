import asyncio
import feedparser
import httpx
import logging

# Some common Pakistani news RSS feeds
RSS_FEEDS = {
    "Dawn": "https://www.dawn.com/feeds/home/",
    "Geo": "https://www.geo.tv/rss/1/53",
    "ARY": "https://arynews.tv/feed/",
    "Express Tribune": "https://tribune.com.pk/feed/pakistan"
}

PHYSICAL_CRISIS_KEYWORDS = [
    "flood", "flooding", "waterlogging", "pani bhar", "submerged",
    "fire", "aag lagi", "blaze", "flames",
    "accident", "hadsa", "collision", "crash", "overturned",
    "road blocked", "traffic blocked", "rasta band", "closure",
    "earthquake", "tremor", "landslide",
    "heatwave", "heat stroke", "garmi",
    "rain", "storm", "baarish", "thunderstorm",
    "rescue", "emergency services", "1122",
    "explosion", "blast", "dhamaka",
    "power outage", "bijli gul", "breakdown",
    "sewage", "sewerage overflow"
]

SPECIFIC_LOCATION_KEYWORDS = [
    "G-10", "G-11", "G-9", "G-8", "G-7", "G-6",
    "F-8", "F-7", "F-6", "F-10", "F-11",
    "I-8", "I-9", "I-10", "I-11",
    "E-7", "E-11",
    "Faizabad", "Saddar", "Raja Bazaar", "Rawalpindi",
    "Murree Road", "Peshawar Road", "Kashmir Highway",
    "Blue Area", "Margalla", "Srinagar Highway",
    "Islamabad Expressway", "PWD", "Bahria Town",
    "Committee Chowk", "Chandni Chowk"
]

EXCLUDE_IF_CONTAINS = [
    "parliament", "senate", "national assembly", "budget", "imf",
    "minister said", "prime minister", "opposition", "PTI", "PML",
    "court", "judge", "verdict", "election", "nuclear", "foreign policy"
]

async def fetch_feed(name: str, url: str, client: httpx.AsyncClient) -> list:
    """Fetch and parse a single RSS feed."""
    try:
        response = await client.get(url, timeout=10.0, follow_redirects=True)
        # Parse the raw XML with feedparser in a thread to avoid blocking the event loop
        feed = await asyncio.to_thread(feedparser.parse, response.text)
        return [{"source": name, "entry": entry} for entry in feed.entries]
    except Exception as e:
        logging.error(f"Error fetching feed {name} from {url}: {e}")
        return []

async def scan_latest_crises() -> dict:
    """Scan news feeds and filter for local crises."""
    all_entries = []
    
    # We use a custom User-Agent to ensure we are not blocked by standard news site firewalls
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [fetch_feed(name, url, client) for name, url in RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks)
        for res in results:
            all_entries.extend(res)

    filtered_signals = []
    
    # Track unique URLs to avoid processing the same article twice
    seen_links = set()
    
    for item in all_entries:
        entry = item["entry"]
        link = entry.get("link", "")
        if link in seen_links:
            continue
        seen_links.add(link)
            
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        text_to_search = (title + " " + summary).lower()

        is_political = any(ex.lower() in text_to_search for ex in EXCLUDE_IF_CONTAINS)
        if is_political:
            continue
            
        has_specific_location = any(loc.lower() in text_to_search for loc in SPECIFIC_LOCATION_KEYWORDS)
        has_physical_crisis = any(kw.lower() in text_to_search for kw in PHYSICAL_CRISIS_KEYWORDS)

        # Must have a SPECIFIC sector/road name AND a PHYSICAL crisis keyword
        # Generic "Islamabad" dateline alone does NOT qualify
        if has_specific_location and has_physical_crisis:
            filtered_signals.append({
                "source": item["source"],
                "text": f"{title} - {summary}"
            })

    URGENT_WORDS = ["flood", "fire", "blast", "accident", "killed", 
                    "injured", "emergency", "aag", "pani", "hadsa"]
    
    filtered_signals.sort(
        key=lambda x: any(w in x["text"].lower() for w in URGENT_WORDS),
        reverse=True
    )
    
    # Limit to 3 signals max to avoid token limits and conserve API quota
    filtered_signals = filtered_signals[:3]
    
    using_demo_data = False
    if len(filtered_signals) == 0:
        DEMO_FALLBACK_SIGNALS = [
            {"source": "social", "text": "[Dawn News] Waterlogging reported in G-10 Markaz after heavy rain, vehicles stranded on main road"},
            {"source": "weather", "text": "Pakistan Met Department issues heavy rainfall warning for Islamabad Rawalpindi region, 60mm expected"},
            {"source": "traffic", "text": "[Geo News] Faizabad interchange traffic completely blocked, commuters advised to use Margalla Road"}
        ]
        filtered_signals = DEMO_FALLBACK_SIGNALS
        using_demo_data = True

    return {
        "scanned_sources": list(RSS_FEEDS.keys()),
        "total_articles_scanned": len(all_entries),
        "signals_extracted": len(filtered_signals),
        "signals": filtered_signals,
        "using_demo_data": using_demo_data
    }
