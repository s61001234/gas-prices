import re
import urllib.request
from urllib.parse import quote
from datetime import date

# ── YOUR SCRAPERANT API KEY ──
ANT_KEY = "0d3e109bf79545d1a3568cfa83961e64"

STATE_PRICES = {
    "AK":{"name":"Alaska","fips":"02"}, "AL":{"name":"Alabama","fips":"01"}, "AR":{"name":"Arkansas","fips":"05"},
    "AZ":{"name":"Arizona","fips":"04"}, "CA":{"name":"California","fips":"06"}, "CO":{"name":"Colorado","fips":"08"},
    "CT":{"name":"Connecticut","fips":"09"}, "DC":{"name":"District of Columbia","fips":"11"}, "DE":{"name":"Delaware","fips":"10"},
    "FL":{"name":"Florida","fips":"12"}, "GA":{"name":"Georgia","fips":"13"}, "HI":{"name":"Hawaii","fips":"15"},
    "IA":{"name":"Iowa","fips":"19"}, "ID":{"name":"Idaho","fips":"16"}, "IL":{"name":"Illinois","fips":"17"},
    "IN":{"name":"Indiana","fips":"18"}, "KS":{"name":"Kansas","fips":"20"}, "KY":{"name":"Kentucky","fips":"21"},
    "LA":{"name":"Louisiana","fips":"22"}, "MA":{"name":"Massachusetts","fips":"25"}, "MD":{"name":"Maryland","fips":"24"},
    "ME":{"name":"Maine","fips":"23"}, "MI":{"name":"Michigan","fips":"26"}, "MN":{"name":"Minnesota","fips":"27"},
    "MO":{"name":"Missouri","fips":"29"}, "MS":{"name":"Mississippi","fips":"28"}, "MT":{"name":"Montana","fips":"30"},
    "NC":{"name":"North Carolina","fips":"37"}, "ND":{"name":"North Dakota","fips":"38"}, "NE":{"name":"Nebraska","fips":"31"},
    "NH":{"name":"New Hampshire","fips":"33"}, "NJ":{"name":"New Jersey","fips":"34"}, "NM":{"name":"New Mexico","fips":"35"},
    "NV":{"name":"Nevada","fips":"32"}, "NY":{"name":"New York","fips":"36"}, "OH":{"name":"Ohio","fips":"39"},
    "OK":{"name":"Oklahoma","fips":"40"}, "OR":{"name":"Oregon","fips":"41"}, "PA":{"name":"Pennsylvania","fips":"42"},
    "RI":{"name":"Rhode Island","fips":"44"}, "SC":{"name":"South Carolina","fips":"45"}, "SD":{"name":"South Dakota","fips":"46"},
    "TN":{"name":"Tennessee","fips":"47"}, "TX":{"name":"Texas","fips":"48"}, "UT":{"name":"Utah","fips":"49"},
    "VA":{"name":"Virginia","fips":"51"}, "VT":{"name":"Vermont","fips":"50"}, "WA":{"name":"Washington","fips":"53"},
    "WI":{"name":"Wisconsin","fips":"55"}, "WV":{"name":"West Virginia","fips":"54"}, "WY":{"name":"Wyoming","fips":"56"},
}

def fetch_via_ant(target_url, use_browser=False):
    """Bridge to AAA via ScraperAnt to bypass the 403 Forbidden block"""
    try:
        # browser=false uses 1 credit; browser=true uses 10 credits. 
        # We try false first as it's faster and usually enough for AAA's IP block.
        browser_setting = "true" if use_browser else "false"
        ant_url = f"https://api.scrapingant.com/v2/general?url={quote(target_url)}&x-api-key={ANT_KEY}&browser={browser_setting}"
        
        req = urllib.request.Request(ant_url)
        return urllib.request.urlopen(req, timeout=40).read().decode("utf-8")
    except Exception as e:
        print(f"  Bridge failed for {target_url}: {e}")
        return None

def fetch_state_price(abbr):
    html = fetch_via_ant(f"https://gasprices.aaa.com/?state={abbr}")
    if html:
        patterns = [r'Regular[^$]*\$([\d]+\.[\d]+)', r'"regular"\s*:\s*"?([\d]+\.[\d]+)', r'\$([\d]\.\d{3})']
        for pattern in patterns:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                price = float(m.group(1))
                if 2.0 < price < 8.0: return price
    return None

# ── Main Process ──
print("Using ScraperAnt Bridge to fetch AAA data...")
main_url = "https://gasprices.aaa.com/state-gas-price-averages/"
html = fetch_via_ant(main_url)

prices = {}
if html:
    # Look for AAA National Average
    official_nat_avg = None
    m_nat = re.search(r'National Average\s*\$?([\d]+\.[\d]+)', html, re.IGNORECASE)
    if m_nat: official_nat_avg = float(m_nat.group(1))

    # Look for state table rows
    pattern = r'state=([A-Z]{2}).*?>([\d]+\.[\d]+)<'
    rows = re.findall(pattern, html, re.DOTALL)
    for abbr, reg in rows:
        if abbr in STATE_PRICES:
            prices[abbr] = (float(reg), round(float(reg)*1.1, 3), round(float(reg)*1.2, 3))

# If main page failed, we fetch states individually
if len(prices) < 40:
    print(f"Main page blocked or incomplete. Fetching states one-by-one...")
    for abbr in STATE_PRICES:
        if abbr not in prices:
            p = fetch_state_price(abbr)
            if p: 
                prices[abbr] = (p, round(p*1.1, 3), round(p*1.2, 3))
                print(f"  {abbr}: ${p}")

if len(prices) < 40:
    print("Failed to get data. Check ScraperAnt credits.")
    exit(0)

# ── Patch index.html (Steps 3-6) ──
today = date.today().strftime("%m/%d/%y")
lines = [f'  ["{a}","{STATE_PRICES[a]["name"]}",{p[0]:.3f},{p[1]:.3f},{p[2]:.3f},"{STATE_PRICES[a]["fips"]}"],' for a, p in prices.items()]
new_fallback = "const FALLBACK = [\n" + "\n".join(lines) + "\n];"

nat_avg = official_nat_avg if (html and 'official_nat_avg' in locals() and official_nat_avg) else sum(p[0] for p in prices.values())/len(prices)
nat_avg_str = f"{nat_avg:.3f}"

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'const FALLBACK = \[[\s\S]*?\n\];', new_fallback, content)
content = re.sub(r"dataDate: '[^']*',", f"dataDate: '{today}',", content)
content = re.sub(r"natAvg: [\d.]+,", f"natAvg: {nat_avg_str},", content)
content = re.sub(r'as of [\d/]+\s*·\s*Source: AAA', f'as of {today} · Source: AAA', content)
content = re.sub(r'(\$[\d.]+)(?=</span>\s*<span class="nat-avg-sub">)', f'${nat_avg_str}', content)
content = re.sub(r'(<span id="footer-date">)[^<]*(</span>)', f'\\g<1>{today}\\g<2>', content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! Updated {len(prices)} states. National Avg: ${nat_avg_str}")
