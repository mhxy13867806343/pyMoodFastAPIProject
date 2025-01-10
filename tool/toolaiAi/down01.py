import requests
from pyquery import PyQuery as pq
import json
import re
from tool.dbHeaders import outerUserAgentHeadersX64

url = "https://www.toolai.io/zh/category"
resource = requests.get(url, headers=outerUserAgentHeadersX64)
doc = pq(resource.content)
container = doc.find(".container")
l = list(container.items())[1]

data = []  # List to store extracted data

for item in l.items():
    row = item.find('.row').items()
    for rowItem in row:
        rowCol = rowItem.find('.col').items()
        for c in rowCol:
            href = c.find('a').attr('href')
            text_with_number = c.find('a').text()
            # Use regular expression to extract text without numbers
            text = re.sub(r'\d+', '', text_with_number).strip()
            if text:
                category_match = re.search(r'/zh/category/([^/]+)', href)
                if category_match:
                    category = category_match.group(1)
                    data.append({"Category": category, "href": href, "text": text.strip()})  # Strip any leading or trailing whitespace

# Save data as JSON
with open('./tool.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
