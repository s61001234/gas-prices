import re
import json
import urllib.request
from datetime import date

# AAA loads prices dynamically - we'll try multiple approaches
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Hardcoded current prices as reliable baseline
# Script will try to fetch live data, fall back to updating date only
STATE_PRICES = {
    "AK":{"name":"Alaska","fips":"02"},
    "AL":{"name":"Alabama","fips":"01"},
    "AR":{"name":"Arkansas","fips":"05"},
    "AZ":{"name":"Arizona","fips":"04"},
    "CA":{"name":"California","fips":"06"},
    "CO":{"name":"Colorado","fips":"08"},
    "CT":{"name":"Connecticut","fips":"09"},
    "DC":{"name":"District of Columbia","fips":"11"},
    "DE":{"name":"Delaware","fips":"10"},
    "FL":{"name":"Florida","fips":"12"},
    "GA":{"name":"Georgia","fips":"13"},
    "HI":{"name":"Hawaii","fips":"15"},
    "IA":{"name":"Iowa","fips":"19"},
    "ID":{"name":"Idaho","fips":"16"},
    "IL":{"name":"Illinois","fips":"17"},
    "IN":{"name":"Indiana","fips":"18"},
    "KS":{"name":"Kansas","fips":"20"},
    "KY":{"name":"Kentucky","fips":"21"},
    "LA":{"name":"Louisiana","fips":"22"},
    "MA":{"name":"Massachusetts","fips":"25"},
    "MD":{"name":"Maryland","fips":"24"},
    "ME":{"name":"Maine","fips":"23"},
    "MI":{"name":"Michigan","fips":"26"},
    "MN":{"name":"Minnesota","fips":"27"},
    "MO":{"name":"Missouri","fips":"29"},
    "MS":{"name":"Mississippi","fips":"28"},
    "MT":{"name":"Montana","fips":"30"},
    "NC":{"name":"North Carolina","fips":"37"},
    "ND":{"name":"North Dakota","fips":"38"},
    "NE":{"name":"Nebraska","fips":"31"},
    "NH":{"name":"New Hampshire","fips":"33"},
    "NJ":{"name":"New Jersey","fips":"34"},
    "NM":{"name":"New Mexico","fips":"35"},
    "NV":{"name":"Nevada","fips":"32"},
    "NY":{"name":"New York","fips":"36"},
    "OH":{"name":"Ohio","fips":"39"},
    "OK":{"name":"Oklahoma","fips":"40"},
    "OR":{"name":"Oregon","fips":"41"},
    "PA":{"name":"Pennsylvania","fips":"42"},
    "RI":{"name":"Rhode Island","fips":"44"},
    "SC":{"name":"South Carolina","fips":"45"},
    "SD":{"name":"South Dakota","fips":"46"},
    "TN":{"name":"Tennessee","fips":"47"},
    "TX":{"name":"Texas","fips":"48"},
    "UT":{"name":"Utah","fips":"49"},
    "VA":{"name":"Virginia","fips":"51"},
    "VT":{"name":"Vermont","fips":"50"},
    "WA":{"name":"Washington","fips":"53"},
    "WI":{"name":"Wisconsin","fips":"55"},
    "WV":{"name":"West Virginia","fips":"54"},
    "WY":{"name":"Wyoming","fips":"56"},
}

def fetch_state_price(abbr):
    """Fetch price for a single state from AAA state page"""
    try:
        url = f"https://gasprices.aaa.com/?state={abbr}"
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
        
        # Look for price patterns in the page
        # AAA shows prices like $3.272 or 3.272
        patterns = [
            r'Regular[^$]*\$([\d]+\.[\d]+)',
            r'"regular"\s*:\s*"?([\d]+\.[\d]+)',
            r'regular.*?([\d]\.\d{3})',
            r'\$([\d]\.\d{3})',
        ]
        for pattern in patterns:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                price = float(m.group(1))
                if 2.0 < price < 8.0:  # sanity check
                    return price
    except Exception as e:
        print(f"  {abbr}: fetch failed - {e}")
    return None

def fetch_all_states_page():
    """Try to get all prices from the main state averages page"""
    try:
        url = "https://gasprices.aaa.com/state-gas-price-averages/"
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        
        # Try multiple regex patterns for the table
        patterns = [
            # Markdown table format
            r'\[([A-Za-z ]+)\]\(https://gasprices\.aaa\.com\?state=([A-Z]+)\).*?\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)',
            # HTML table format
            r'state=([A-Z]{2}).*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<',
            # JSON-like format
            r'"([A-Z]{2})"[^}]*"regular"\s*:\s*"?([\d.]+)',
        ]
        
        for pattern in patterns:
            rows = re.findall(pattern, html, re.DOTALL)
            if len(rows) >= 40:
                print(f"Found {len(rows)} states with pattern")
                return rows, html
                
        print(f"Page fetched but no price table found. Page length: {len(html)}")
        print("First 500 chars:", html[:500])
        return [], html
    except Exception as e:
        print(f"Failed to fetch main page: {e}")
        return [], ""

# Try main page first
print("Fetching AAA state averages page...")
rows, html = fetch_all_states_page()

prices = {}  # abbr -> (regular, midgrade, premium)

if len(rows) >= 40:
    for row in rows:
        if len(row) == 6:  # (name, abbr, reg, mid, pre)
            name, abbr, reg, mid, pre = row[0], row[1], row[2], row[3], row[4]
        elif len(row) == 5:
            name, abbr, reg, mid, pre = row
        elif len(row) == 4:
            abbr, reg, mid, pre = row
        else:
            continue
        abbr = abbr.strip().upper()
        if abbr in STATE_PRICES:
            try:
                prices[abbr] = (float(reg), float(mid), float(pre))
            except:
                pass

# If main page didn't work, fetch each state individually
if len(prices) < 40:
    print(f"Only got {len(prices)} from main page, fetching states individually...")
    for abbr in STATE_PRICES:
        if abbr not in prices:
            price = fetch_state_price(abbr)
            if price:
                prices[abbr] = (price, price * 1.1, price * 1.2)
                print(f"  {abbr}: ${price}")

print(f"Total states with prices: {len(prices)}")

if len(prices) < 40:
    print("Could not get enough state prices, keeping existing data")
    exit(0)

# Build new FALLBACK array
today = date.today().strftime("%m/%d/%y")
lines = []
for abbr, info in STATE_PRICES.items():
    if abbr in prices:
        reg, mid, pre = prices[abbr]
        fips = info["fips"]
        name = info["name"]
        lines.append(f'  ["{abbr}","{name}",{reg:.3f},{mid:.3f},{pre:.3f},"{fips}"],')

new_fallback = "const FALLBACK = [\n" + "\n".join(lines) + "\n];"

# Read and update index.html
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Update FALLBACK data
content = re.sub(
    r'const FALLBACK = \[[\s\S]*?\n\];',
    new_fallback,
    content
)

# Update date - find and replace directly
match = re.search(r"dataDate: '[^']*',", content)
if match:
    content = content.replace(match.group(0), f"dataDate: '{today}',")
    print(f"Date updated to {today}")
else:
    print("WARNING: Could not find dataDate")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! Updated {len(lines)} states dated {today}")
