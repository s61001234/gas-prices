import re
import urllib.request
from datetime import date

url = "https://gasprices.aaa.com/state-gas-price-averages/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")

FIPS = {
    "AK":"02","AL":"01","AR":"05","AZ":"04","CA":"06","CO":"08","CT":"09",
    "DC":"11","DE":"10","FL":"12","GA":"13","HI":"15","IA":"19","ID":"16",
    "IL":"17","IN":"18","KS":"20","KY":"21","LA":"22","MA":"25","MD":"24",
    "ME":"23","MI":"26","MN":"27","MO":"29","MS":"28","MT":"30","NC":"37",
    "ND":"38","NE":"31","NH":"33","NJ":"34","NM":"35","NV":"32","NY":"36",
    "OH":"39","OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46",
    "TN":"47","TX":"48","UT":"49","VA":"51","VT":"50","WA":"53","WI":"55",
    "WV":"54","WY":"56",
}

STATE_NAMES = {
    "AK":"Alaska","AL":"Alabama","AR":"Arkansas","AZ":"Arizona",
    "CA":"California","CO":"Colorado","CT":"Connecticut","DC":"District of Columbia",
    "DE":"Delaware","FL":"Florida","GA":"Georgia","HI":"Hawaii","IA":"Iowa",
    "ID":"Idaho","IL":"Illinois","IN":"Indiana","KS":"Kansas","KY":"Kentucky",
    "LA":"Louisiana","MA":"Massachusetts","MD":"Maryland","ME":"Maine",
    "MI":"Michigan","MN":"Minnesota","MO":"Missouri","MS":"Mississippi",
    "MT":"Montana","NC":"North Carolina","ND":"North Dakota","NE":"Nebraska",
    "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NV":"Nevada",
    "NY":"New York","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
    "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee",
    "TX":"Texas","UT":"Utah","VA":"Virginia","VT":"Vermont","WA":"Washington",
    "WI":"Wisconsin","WV":"West Virginia","WY":"Wyoming",
}

rows = re.findall(
    r'\[([A-Za-z ]+)\]\(https://gasprices\.aaa\.com\?state=([A-Z]+)\)'
    r'.*?\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)\s*\|\s*\$([\d.]+)',
    html
)

if len(rows) < 40:
    print(f"Only found {len(rows)} rows, keeping existing data")
    exit(0)

today = date.today().strftime("%m/%d/%y")
lines = []
for (name, abbr, reg, mid, pre) in rows:
    abbr = abbr.strip()
    fips = FIPS.get(abbr, "")
    if not fips:
        continue
    display_name = STATE_NAMES.get(abbr, name.strip())
    lines.append(f'  ["{abbr}","{display_name}",{reg},{mid},{pre},"{fips}"],')

new_fallback = "const FALLBACK = [\n" + "\n".join(lines) + "\n];"
new_date = f"dataDate: '{today}',"

with open("index.html", "r") as f:
    content = f.read()

content = re.sub(r'const FALLBACK = \[[\s\S]*?\];', new_fallback, content)
content = re.sub(r"dataDate: '[^']+'," , new_date, content)

with open("index.html", "w") as f:
    f.write(content)

print(f"Updated {len(lines)} states - dated {today}")
