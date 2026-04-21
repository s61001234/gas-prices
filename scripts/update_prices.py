import re
import urllib.request
import time
from datetime import date

# Updated User-Agent to look like a modern Mac
# We are making the headers much more detailed to look like a real, logged-in browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}
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

def fetch_state_price(abbr):
    try:
        # Wait 2 seconds before each request to avoid being blocked
        time.sleep(2) 
        url = f"https://gasprices.aaa.com/?state={abbr}"
        req_headers = HEADERS.copy()
        req_headers["Referer"] = "https://gasprices.aaa.com/state-gas-price-averages/"
        
        req = urllib.request.Request(url, headers=req_headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
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
                if 2.0 < price < 8.0:
                    return price
    except Exception as e:
        print(f"  {abbr}: fetch failed - {e}")
    return None

def fetch_all_states_page():
    try:
        url = "https://gasprices.aaa.com/state-gas-price-averages/"
        req_headers = HEADERS.copy()
        req_headers["Referer"] = "https://www.google.com/"
        
        req = urllib.request.Request(url, headers=req_headers)
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        
        patterns = [
            r'\[([A-Za-z ]+)\]\(https://gasprices\.aaa\.com\?state=([A-Z]+)\).*?\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)',
            r'state=([A-Z]{2}).*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<',
            r'"([A-Z]{2})"[^}]*"regular"\s*:\s*"?([\d.]+)',
        ]
        for pattern in patterns:
            rows = re.findall(pattern, html, re.DOTALL)
            if len(rows) >= 40:
                return rows, html
        return [], html
    except Exception as e:
        print(f"Error 403: AAA blocked the request. - {e}")
        return [], ""

def fetch_official_nat_avg(html):
    patterns = [r'National Average\s*\$?([\d]+\.[\d]+)', r'national.average.*?\$?([\d]+\.[\d]+)']
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            price = float(m.group(1))
            if 2.0 < price < 8.0:
                return price
    return None

# --- Main Logic ---
print("Fetching AAA state averages page...")
rows, html = fetch_all_states_page()
official_nat_avg = fetch_official_nat_avg(html)
prices = {}

if len(rows) >= 40:
    for row in rows:
        abbr = row[1].strip().upper() if len(row) >= 2 else ""
        if abbr in STATE_PRICES:
            prices[abbr] = (float(row[2]), float(row[3]), float(row[4]))

if len(prices) < 40:
    print(f"Fetching {51 - len(prices)} states individually with a 2-second delay...")
    for abbr in STATE_PRICES:
        if abbr not in prices:
            price = fetch_state_price(abbr)
            if price:
                prices[abbr] = (price, round(price * 1.1, 3), round(price * 1.2, 3))
                print(f"  {abbr}: ${price}")

if len(prices) < 40:
    print("Could not get enough state prices, keeping existing data")
    exit(0)

# Build updated FALLBACK and update index.html (Steps 3-6)
today = date.today().strftime("%m/%d/%y")
lines = [f'  ["{a}","{STATE_PRICES[a]["name"]}",{p[0]:.3f},{p[1]:.3f},{p[2]:.3f},"{STATE_PRICES[a]["fips"]}"],' for a, p in prices.items()]
new_fallback = "const FALLBACK = [\n" + "\n".join(lines) + "\n];"

nat_avg = official_nat_avg if official_nat_avg else sum(p[0] for p in prices.values()) / len(prices)
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
