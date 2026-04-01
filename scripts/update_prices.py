import re
import urllib.request
from datetime import date

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

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
    try:
        url = f"https://gasprices.aaa.com/?state={abbr}"
        req = urllib.request.Request(url, headers=HEADERS)
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
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        patterns = [
            r'\[([A-Za-z ]+)\]\(https://gasprices\.aaa\.com\?state=([A-Z]+)\).*?\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)',
            r'state=([A-Z]{2}).*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<.*?>([\d]+\.[\d]+)<',
            r'"([A-Z]{2})"[^}]*"regular"\s*:\s*"?([\d.]+)',
        ]
        for pattern in patterns:
            rows = re.findall(pattern, html, re.DOTALL)
            if len(rows) >= 40:
                print(f"Found {len(rows)} states with pattern")
                return rows, html
        print(f"Page fetched but no price table found. Page length: {len(html)}")
        return [], html
    except Exception as e:
        print(f"Failed to fetch main page: {e}")
        return [], ""

def fetch_official_nat_avg(html):
    """Try to get AAA's official national average from the page"""
    # Try main page HTML first
    patterns = [
        r'National Average\s*\$?([\d]+\.[\d]+)',
        r'national.average.*?\$?([\d]+\.[\d]+)',
        r'avg.*?\$?([\d]+\.[\d]+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            price = float(m.group(1))
            if 2.0 < price < 8.0:
                print(f"AAA official national average found: ${price}")
                return price

    # Try AAA homepage as backup
    try:
        req = urllib.request.Request("https://gasprices.aaa.com/", headers=HEADERS)
        home_html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
        for pattern in patterns:
            m = re.search(pattern, home_html, re.IGNORECASE)
            if m:
                price = float(m.group(1))
                if 2.0 < price < 8.0:
                    print(f"AAA official national average (homepage): ${price}")
                    return price
    except Exception as e:
        print(f"Could not fetch homepage: {e}")

    print("Could not find AAA official national average, will calculate from states")
    return None

# ── STEP 1: Fetch main AAA page ──
print("Fetching AAA state averages page...")
rows, html = fetch_all_states_page()

# ── STEP 1B: Try to get AAA's official national average ──
official_nat_avg = fetch_official_nat_avg(html)

prices = {}

if len(rows) >= 40:
    for row in rows:
        if len(row) == 6:
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

# ── STEP 2: If main page failed, fetch each state one by one ──
if len(prices) < 40:
    print(f"Only got {len(prices)} from main page, fetching states individually...")
    for abbr in STATE_PRICES:
        if abbr not in prices:
            price = fetch_state_price(abbr)
            if price:
                prices[abbr] = (price, round(price * 1.1, 3), round(price * 1.2, 3))
                print(f"  {abbr}: ${price}")

print(f"Total states with prices: {len(prices)}")

if len(prices) < 40:
    print("Could not get enough state prices, keeping existing data")
    exit(0)

# ── STEP 3: Build updated FALLBACK array ──
today = date.today().strftime("%m/%d/%y")
lines = []
for abbr, info in STATE_PRICES.items():
    if abbr in prices:
        reg, mid, pre = prices[abbr]
        fips = info["fips"]
        name = info["name"]
        lines.append(f'  ["{abbr}","{name}",{reg:.3f},{mid:.3f},{pre:.3f},"{fips}"],')

new_fallback = "const FALLBACK = [\n" + "\n".join(lines) + "\n];"

# ── STEP 4: Determine national average ──
if official_nat_avg:
    nat_avg = official_nat_avg
    print(f"Using AAA official national average: ${nat_avg}")
else:
    nat_avg = sum(p[0] for p in prices.values()) / len(prices)
    print(f"Using calculated national average: ${nat_avg:.3f}")
nat_avg_str = f"{nat_avg:.3f}"

# ── STEP 5: Read index.html and patch all values ──
with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Patch 1: state price data
content = re.sub(
    r'const FALLBACK = \[[\s\S]*?\n\];',
    new_fallback,
    content
)
print("State prices updated")

# Patch 2: date in app object
match = re.search(r"dataDate: '[^']*',", content)
if match:
    content = content.replace(match.group(0), f"dataDate: '{today}',")
    print(f"dataDate updated to {today}")
else:
    print("WARNING: Could not find dataDate")

# Patch 3: national average in app object
match2 = re.search(r"natAvg: [\d.]+,", content)
if match2:
    content = content.replace(match2.group(0), f"natAvg: {nat_avg_str},")
    print(f"natAvg updated to ${nat_avg_str}")
else:
    print("WARNING: Could not find natAvg")

# Patch 4: date in HTML header
content = re.sub(
    r'as of [\d/]+\s*·\s*Source: AAA',
    f'as of {today} · Source: AAA',
    content
)
print(f"Header date updated to {today}")

# Patch 5: national average in HTML header
content = re.sub(
    r'(\$[\d.]+)(?=</span>\s*<span class="nat-avg-sub">)',
    f'${nat_avg_str}',
    content
)
print(f"Header national avg updated to ${nat_avg_str}")

# Patch 6: footer date
content = re.sub(
    r'(<span id="footer-date">)[^<]*(</span>)',
    f'\\g<1>{today}\\g<2>',
    content
)
print(f"Footer date updated to {today}")

# ── STEP 6: Save updated file ──
with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done! Updated {len(lines)} states dated {today}")
